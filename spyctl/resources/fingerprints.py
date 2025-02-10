import re
from dataclasses import dataclass, field
from typing import Dict, Generator, List, Set, Tuple

import zulu
from tabulate import tabulate

import spyctl.config.configs as cfg
import spyctl.filter_resource as filt
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.source_query_resources import get_guardian_fingerprints

FPRINT_KIND = lib.FPRINT_KIND
FPRINT_TYPE_CONT = lib.POL_TYPE_CONT
FPRINT_TYPE_SVC = lib.POL_TYPE_SVC
FPRINT_TYPES = {FPRINT_TYPE_CONT, FPRINT_TYPE_SVC}
GROUP_KIND = lib.FPRINT_GROUP_KIND
FIRST_TIMESTAMP_FIELD = lib.FIRST_TIMESTAMP_FIELD
LATEST_TIMESTAMP_FIELD = lib.LATEST_TIMESTAMP_FIELD
FINGERPRINTS_FIELD = lib.FPRINT_GRP_FINGERPRINTS_FIELD
CONT_NAMES_FIELD = lib.FPRINT_GRP_CONT_NAMES_FIELD
CONT_IDS_FIELD = lib.FPRINT_GRP_CONT_IDS_FIELD
MACHINES_FIELD = lib.FPRINT_GRP_MACHINES_FIELD
NOT_AVAILABLE = lib.NOT_AVAILABLE


class InvalidFingerprintError(Exception):
    pass


class InvalidFprintGroup(Exception):
    pass


class Fingerprint:
    required_keys = {
        lib.API_FIELD,
        lib.KIND_FIELD,
        lib.METADATA_FIELD,
        lib.SPEC_FIELD,
    }
    spec_required_keys = {lib.PROC_POLICY_FIELD, lib.NET_POLICY_FIELD}
    type_required_selector = {
        FPRINT_TYPE_CONT: lib.CONT_SELECTOR_FIELD,
        FPRINT_TYPE_SVC: lib.SVC_SELECTOR_FIELD,
    }

    def __init__(self, fprint: Dict) -> None:
        if not isinstance(fprint, dict):
            raise InvalidFingerprintError(
                "Fingerprint should be a dictionary."
            )
        for key in self.required_keys:
            if key not in fprint:
                raise InvalidFingerprintError(
                    f"Fingerprint missing {key} field."
                )
        if not lib.valid_api_version(fprint[lib.API_FIELD]):
            raise InvalidFingerprintError(f"Invalid {lib.API_FIELD}.")
        if not lib.valid_kind(fprint[lib.KIND_FIELD], FPRINT_KIND):
            raise InvalidFingerprintError(f"Invalid {lib.KIND_FIELD}.")
        self.metadata = fprint[lib.METADATA_FIELD]
        if not isinstance(self.metadata, dict):
            raise InvalidFingerprintError("metadata is not a dictionary.")
        self.name = self.metadata.get(lib.METADATA_NAME_FIELD)
        if not self.name:
            raise InvalidFingerprintError("Invalid name.")
        self.type = self.metadata.get(lib.METADATA_TYPE_FIELD)
        if self.type not in FPRINT_TYPES:
            raise InvalidFingerprintError("Invalid type.")
        self.spec = fprint["spec"]
        if not isinstance(self.spec, dict):
            raise InvalidFingerprintError("Spec must be a dictionary.")
        for key in self.spec_required_keys.union(
            {self.type_required_selector[self.type]}
        ):
            if key not in self.spec:
                raise InvalidFingerprintError(
                    f"Missing {key} from {lib.SPEC_FIELD} for {self.type}"
                    f" fingerprint."
                )
        self.selectors = {
            key: value
            for key, value in self.spec.items()
            if key.endswith("Selector")
        }
        for selector_name, selector in self.selectors.items():
            if not isinstance(selector, dict):
                raise InvalidFingerprintError(
                    f"{selector_name} must be a dictionary."
                )

    def as_dict(self) -> Dict:
        rv = {
            lib.API_FIELD: lib.API_VERSION,
            lib.KIND_FIELD: FPRINT_KIND,
            lib.METADATA_FIELD: self.metadata,
            lib.SPEC_FIELD: self.spec,
        }
        return rv


class FingerprintGroup:
    def __init__(self, fingerprint: Dict) -> None:
        self.fingerprints = {}
        self.first_timestamp = NOT_AVAILABLE
        self.latest_timestamp = NOT_AVAILABLE
        self.pods = set()
        self.namespaces = set()
        self.machines = set()

    def add_fingerprint(self, fingerprint: Dict):
        machine_uid = fingerprint[lib.METADATA_FIELD].get("muid")
        if machine_uid:
            self.machines.add(machine_uid)
        self.__update_first_timestamp(
            fingerprint[lib.METADATA_FIELD].get(FIRST_TIMESTAMP_FIELD)
        )
        self.__update_latest_timestamp(
            fingerprint[lib.METADATA_FIELD].get(LATEST_TIMESTAMP_FIELD)
        )
        fprint_id = fingerprint[lib.METADATA_FIELD].get("id")
        if fprint_id is None:
            fprint_id = lib.make_uuid()
        if (
            fprint_id not in self.fingerprints
            or LATEST_TIMESTAMP_FIELD
            not in self.fingerprints.get(fprint_id, {}).get(
                lib.METADATA_FIELD, {}
            )
        ):
            self.fingerprints[fprint_id] = {
                lib.API_FIELD: fingerprint[lib.API_FIELD],
                lib.KIND_FIELD: fingerprint[lib.KIND_FIELD],
                lib.METADATA_FIELD: fingerprint[lib.METADATA_FIELD],
                lib.SPEC_FIELD: fingerprint[lib.SPEC_FIELD],
            }
        elif self.fingerprints[fprint_id][lib.METADATA_FIELD][
            LATEST_TIMESTAMP_FIELD
        ] <= fingerprint[lib.METADATA_FIELD].get(LATEST_TIMESTAMP_FIELD, 0):
            self.fingerprints[fprint_id] = {
                lib.API_FIELD: fingerprint[lib.API_FIELD],
                lib.KIND_FIELD: fingerprint[lib.KIND_FIELD],
                lib.METADATA_FIELD: fingerprint[lib.METADATA_FIELD],
                lib.SPEC_FIELD: fingerprint[lib.SPEC_FIELD],
            }

    def __update_first_timestamp(self, timestamp):
        if timestamp is None:
            return
        if (
            self.first_timestamp is None
            or self.first_timestamp == NOT_AVAILABLE
        ):
            self.first_timestamp = timestamp
        elif timestamp < self.first_timestamp:
            self.first_timestamp = timestamp

    def __update_latest_timestamp(self, timestamp):
        if timestamp is None:
            return
        if (
            self.latest_timestamp is None
            or self.latest_timestamp == NOT_AVAILABLE
        ):
            self.latest_timestamp = timestamp
        elif timestamp > self.latest_timestamp:
            self.latest_timestamp = timestamp

    def as_dict(self):
        return {}


class ContainerFingerprintGroup(FingerprintGroup):
    def __init__(self, fingerprint: Dict) -> None:
        super().__init__(fingerprint)
        self.image_id = fingerprint[lib.SPEC_FIELD][lib.CONT_SELECTOR_FIELD][
            lib.IMAGEID_FIELD
        ]
        self.image = fingerprint[lib.SPEC_FIELD][lib.CONT_SELECTOR_FIELD][
            lib.IMAGE_FIELD
        ]
        self.container_names = set()
        self.container_ids = set()
        self.add_fingerprint(fingerprint)

    def add_fingerprint(self, fingerprint: Dict):
        super().add_fingerprint(fingerprint)
        image_id = fingerprint[lib.SPEC_FIELD][lib.CONT_SELECTOR_FIELD][
            lib.IMAGEID_FIELD
        ]
        if image_id != self.image_id:
            raise InvalidFprintGroup(
                "Container fprint group must all have the same image ID"
            )
        image = fingerprint[lib.SPEC_FIELD][lib.CONT_SELECTOR_FIELD][
            lib.IMAGE_FIELD
        ]
        if image != self.image:
            raise InvalidFprintGroup(
                "Container fprint group must all have the same image"
            )
        container_name = fingerprint[lib.METADATA_FIELD].get(
            lib.CONT_NAME_FIELD
        )
        if container_name:
            self.container_names.add(container_name)
        container_id = fingerprint[lib.METADATA_FIELD].get(lib.CONT_ID_FIELD)
        if container_id:
            self.container_ids.add(container_id)

    def as_dict(self) -> Dict:
        rv = {
            lib.API_FIELD: lib.API_VERSION,
            lib.KIND_FIELD: GROUP_KIND,
            lib.METADATA_FIELD: {
                lib.IMAGE_FIELD: self.image,
                lib.IMAGEID_FIELD: self.image_id,
                FIRST_TIMESTAMP_FIELD: self.first_timestamp,
                LATEST_TIMESTAMP_FIELD: self.latest_timestamp,
            },
            lib.DATA_FIELD: {
                FINGERPRINTS_FIELD: list(self.fingerprints.values()),
                MACHINES_FIELD: list(self.machines),
                CONT_NAMES_FIELD: list(self.container_names),
                CONT_IDS_FIELD: list(self.container_ids),
            },
        }
        return rv


class ServiceFingerprintGroup(FingerprintGroup):
    def __init__(self, fingerprint: Dict) -> None:
        super().__init__(fingerprint)
        self.cgroup = fingerprint[lib.SPEC_FIELD][lib.SVC_SELECTOR_FIELD][
            lib.CGROUP_FIELD
        ]
        self.add_fingerprint(fingerprint)

    def add_fingerprint(self, fingerprint: Dict):
        super().add_fingerprint(fingerprint)
        cgroup = fingerprint[lib.SPEC_FIELD][lib.SVC_SELECTOR_FIELD][
            lib.CGROUP_FIELD
        ]
        if cgroup != self.cgroup:
            raise InvalidFprintGroup(
                "Linux service fprint group must all have the same cgroup"
            )

    def as_dict(self) -> Dict:
        rv = {
            lib.API_FIELD: lib.API_VERSION,
            lib.KIND_FIELD: GROUP_KIND,
            lib.METADATA_FIELD: {
                lib.CGROUP_FIELD: self.cgroup,
                FIRST_TIMESTAMP_FIELD: self.first_timestamp,
                LATEST_TIMESTAMP_FIELD: self.latest_timestamp,
            },
            lib.DATA_FIELD: {
                FINGERPRINTS_FIELD: list(self.fingerprints.values()),
                MACHINES_FIELD: list(self.machines),
            },
        }
        return rv


@dataclass
class ContainerSumData:
    image_and_tag: str
    image_id: str
    latest_timestamp: float
    covered_count: int = 0
    count: int = 0
    images: Set[str] = field(default_factory=set)
    repos: Set[str] = field(default_factory=set)
    additional_fields: Dict[str, str] = field(default_factory=dict)

    def update_image(self, image: str):
        image_components = image.split("/")
        repo = "/".join(image_components[:-1])
        self.images.add(image)
        if not repo:
            repo = "NO_REPO"
        self.repos.add(repo)

    def update_latest_timestamp(self, timestamp):
        if timestamp > self.latest_timestamp:
            self.latest_timestamp = timestamp

    def get_data(self):
        repos = list(self.repos)
        if len(repos) == 1:
            repo = repos[0]
            if len(repo) > 30:
                repo = repo[:27] + "..."
        else:
            repo = f"MULTIPLE ({len(repos)})"
        return [
            self.image_and_tag,
            self.image_id.strip("sha256:")[:12],
            repo,
            f"{self.covered_count}/{self.count}",
            lib.epoch_to_zulu(self.latest_timestamp),
            *list(self.additional_fields.values()),
        ]

    def get_wide_data(self):
        full_images = "\n".join(sorted(self.images))
        return [
            self.image_and_tag,
            self.image_id,
            full_images,
            f"{self.covered_count}/{self.count}",
            lib.epoch_to_zulu(self.latest_timestamp),
            *list(self.additional_fields.values()),
        ]

    @classmethod
    def extract_image_name_and_tag(cls, image: str) -> str:
        image_components = image.split("/")
        name_and_tag = image_components[-1]
        return name_and_tag

    @classmethod
    def get_headers(cls, group_by: List[str] = []) -> List[str]:
        headers = [
            "IMAGE_NAME:TAG",
            "IMAGEID",
            "REPO",
            "COVERED_BY_POLICY",
            "LATEST_TIMESTAMP",
        ]
        if group_by:
            headers.extend([field.upper() for field in group_by])
        return headers

    @classmethod
    def get_wide_headers(cls, group_by: List[str] = []) -> List[str]:
        headers = [
            "IMAGE_NAME:TAG",
            "IMAGEID",
            "REPO/IMAGE_NAME:TAG",
            "COVERED_BY_POLICY",
            "LATEST_TIMESTAMP",
        ]
        if group_by:
            headers.extend([field.upper() for field in group_by])
        return headers


@dataclass
class ServiceSumData:
    cgroup: str
    latest_timestamp: float
    covered_count: int = 0
    count: int = 0
    additional_fields: Dict[str, str] = field(default_factory=dict)

    def update_latest_timestamp(self, timestamp):
        if timestamp > self.latest_timestamp:
            self.latest_timestamp = timestamp

    def get_data(self):
        service_name = self.cgroup.split("/")[-1]
        cgroup = self.cgroup
        if len(cgroup) > 30:
            cgroup = cgroup[:27] + "..."
        return [
            service_name,
            cgroup,
            f"{self.covered_count}/{self.count}",
            lib.epoch_to_zulu(self.latest_timestamp),
            *list(self.additional_fields.values()),
        ]

    def get_wide_data(self):
        service_name = self.cgroup.split("/")[-1]
        return [
            service_name,
            self.cgroup,
            f"{self.covered_count}/{self.count}",
            lib.epoch_to_zulu(self.latest_timestamp),
            *list(self.additional_fields.values()),
        ]

    @classmethod
    def get_headers(cls, group_by: List[str] = []) -> List[str]:
        headers = [
            "SERVICE_NAME",
            "CGROUP",
            "COVERED_BY_POLICY",
            "LATEST_TIMESTAMP",
        ]
        if group_by:
            headers.extend([field.upper() for field in group_by])
        return headers

    @classmethod
    def get_wide_headers(cls, group_by: List[str] = []) -> List[str]:
        headers = [
            "SERVICE_NAME",
            "CGROUP",
            "COVERED_BY_POLICY",
            "LATEST_TIMESTAMP",
        ]
        if group_by:
            headers.extend([field.upper() for field in group_by])
        return headers


def fprint_output_summary(
    ctx: cfg.Context,
    fprint_type: str,
    sources,
    filters,
    st,
    et,
    name_or_id_expr,
    group_by: List[str] = [],
    sort_by: List[str] = [],
    wide=False,
) -> str:
    fingerprints = get_guardian_fingerprints(
        *ctx.get_api_data(),
        sources,
        (st, et),
        fprint_type,
        unique=True,
        limit_mem=True,
        expr=name_or_id_expr,
        **filters,
    )
    if fprint_type == FPRINT_TYPE_CONT:
        summary = __cont_fprint_summary(fingerprints, wide, group_by, sort_by)
    elif fprint_type == FPRINT_TYPE_SVC:
        summary = __svc_fprint_summary(fingerprints, wide, group_by, sort_by)
    else:
        cli.err_exit("Invalid fingerprint type for summary.")
    return summary


def __cont_fprint_summary(
    fingerprints: Generator[Dict, None, None],
    wide: bool,
    group_by: List[str],
    sort_by: List[str] = [],
) -> str:
    if wide:
        container_headers = ContainerSumData.get_wide_headers(group_by)
    else:
        container_headers = ContainerSumData.get_headers(group_by)
    sort_by = [field.upper() for field in sort_by]
    for col in sort_by:
        if col not in container_headers:
            avail_headers = "\n\t".join(container_headers)
            cli.err_exit(
                f"Invalid sort by field: {col}. Options are: \n\t"
                f"{avail_headers}"
            )
    container_data: Dict[Tuple, ContainerSumData] = {}
    for fprint in fingerprints:
        image_name_and_tag = ContainerSumData.extract_image_name_and_tag(
            fprint[lib.IMAGE_FIELD]
        )
        image_id = fprint["image_id"]
        key = [image_name_and_tag, image_id]
        for f in group_by:
            key.append(filt.get_field_value(f, fprint))
        key = tuple(key)
        if (
            fprint[lib.METADATA_FIELD][lib.METADATA_TYPE_FIELD]
            == FPRINT_TYPE_CONT
        ):
            if key not in container_data:
                container_data[key] = ContainerSumData(
                    image_name_and_tag,
                    fprint["image_id"],
                    fprint["time"],
                    1 if fprint.get("covered_by_policy") else 0,
                    1,
                    additional_fields={
                        field: filt.get_field_value(field, fprint)
                        for field in group_by
                    },
                )
                container_data[key].update_image(fprint[lib.IMAGE_FIELD])
            else:
                container_data[key].update_image(fprint[lib.IMAGE_FIELD])
                container_data[key].update_latest_timestamp(fprint["time"])
                container_data[key].count += 1
                if fprint.get("covered_by_policy"):
                    container_data[key].covered_count += 1
    if wide:
        row_data = [data.get_wide_data() for data in container_data.values()]
    else:
        row_data = [data.get_data() for data in container_data.values()]

    if sort_by:

        def sort_key(row) -> list:
            rv = []
            for col in sort_by:
                insert = row[container_headers.index(col)]
                if insert is None:
                    insert = "~"  # Sort None values to the end
                rv.append(insert)
            return rv

        row_data.sort(key=sort_key)
    else:
        row_data.sort(key=lambda x: [x[0]])
    container_tbl = tabulate(
        row_data,
        container_headers,
        tablefmt="plain",
    )
    return container_tbl


def __svc_fprint_summary(
    fingerprints: Generator[Dict, None, None],
    wide: bool,
    group_by: List[str],
    sort_by: List[str] = [],
) -> str:
    service_headers = [
        "CGROUP",
        "MACHINES",
        "LATEST_TIMESTAMP",
    ]
    if wide:
        service_headers = ServiceSumData.get_wide_headers(group_by)
    else:
        service_headers = ServiceSumData.get_headers(group_by)

    for col in sort_by:
        if col not in service_headers:
            avail_headers = "\n\t".join(service_headers)
            cli.err_exit(
                f"Invalid sort by field: {col}. Options are: \n\t"
                f"{avail_headers}"
            )

    service_data: Dict[Tuple, ServiceSumData] = {}

    grp_by_fields = [lib.CGROUP_FIELD] + group_by
    for fprint in fingerprints:
        key = tuple([filt.get_field_value(f, fprint) for f in grp_by_fields])
        if key not in service_data:
            service_data[key] = ServiceSumData(
                fprint[lib.CGROUP_FIELD],
                fprint["time"],
                1 if fprint.get("covered_by_policy") else 0,
                1,
                {
                    field: filt.get_field_value(field, fprint)
                    for field in group_by
                },
            )
        else:
            service_data[key].update_latest_timestamp(fprint["time"])
            service_data[key].count += 1
            if fprint.get("covered_by_policy"):
                service_data[key].covered_count += 1

    if wide:
        row_data = [data.get_wide_data() for data in service_data.values()]
    else:
        row_data = [data.get_data() for data in service_data.values()]
    if sort_by:
        row_data.sort(
            key=lambda row: [
                row[service_headers.index(col)] for col in sort_by
            ]
        )
    else:
        row_data.sort(key=lambda x: [x[0]])
    service_tbl = tabulate(
        row_data,
        service_headers,
        tablefmt="plain",
    )
    return service_tbl


def fprint_grp_output_wide(
    fingerprint_groups: Tuple,
    coverage=False,
    coverage_percentage: float = None,
) -> str:
    cont_fprint_grps, svc_fprint_grps = fingerprint_groups
    output_list = []
    if coverage:
        percentage = round(coverage_percentage * 100)
        output_list.append(
            f"Policy coverage for queried fingerprints: {percentage}%"
        )
        if len(cont_fprint_grps) + len(svc_fprint_grps) > 0:
            output_list.append(
                f"{lib.WARNING_COLOR}The fingerprints below are not covered by"
                f" a policy:{lib.COLOR_END}"
            )
    if len(cont_fprint_grps) > 0:
        container_headers = [
            "IMAGE",
            "IMAGEID",
            "CONTAINERS",
            "FINGERPRINTS",
            "MACHINES",
            "FIRST_TIMESTAMP",
            "LATEST_TIMESTAMP",
        ]
        container_data = []
        for fprint_grp in cont_fprint_grps:
            container_data.append(cont_grp_output_data_wide(fprint_grp))
        container_data.sort(key=lambda x: [x[0]])
        container_tbl = tabulate(
            container_data, container_headers, tablefmt="plain"
        )
        output_list.append(container_tbl)
    if len(svc_fprint_grps) > 0:
        service_headers = [
            "CGROUP",
            "FINGERPRINTS",
            "MACHINES",
            "FIRST_TIMESTAMP",
            "LATEST_TIMESTAMP",
        ]
        service_data = []
        for fprint_grp in svc_fprint_grps:
            service_data.append(svc_grp_output_data_wide(fprint_grp))
        service_data.sort(key=lambda x: x[0])
        service_tbl = tabulate(service_data, service_headers, tablefmt="plain")
        if len(output_list) > 0:
            service_tbl = "\n" + service_tbl
        output_list.append(service_tbl)
    return "\n".join(output_list)


CONT_REDUNDANT_PATS = [
    re.compile(r"^.+\.amazonaws\.com/"),
    re.compile(r"^public\.ecr\.aws/.+/"),
    re.compile(r"^docker\.io/"),
    re.compile(r"^quay\.io/"),
    re.compile(r"^k8s\.gcr\.io/"),
    re.compile(r"^registry\.k8s\.io/"),
    re.compile(r"@sha256:[a-zA-Z0-9]+$"),
    re.compile(r"__[a-zA-Z0-9]+__[a-zA-Z0-9]+$"),
]


def prepare_image_name(image: str, patterns: List[re.Pattern]):
    for pat in patterns:
        image = re.sub(pat, "", image)
    return image


def cont_grp_output_data(grp: Dict) -> List[str]:
    first_timestamp = grp[lib.METADATA_FIELD].get(
        FIRST_TIMESTAMP_FIELD, NOT_AVAILABLE
    )
    try:
        first_timestamp = (
            zulu.Zulu.fromtimestamp(first_timestamp).format(
                "YYYY-MM-ddTHH:mm:ss"
            )
            + "Z"
        )
    except Exception:
        pass
    latest_timestamp = grp[lib.METADATA_FIELD].get(
        LATEST_TIMESTAMP_FIELD, NOT_AVAILABLE
    )
    try:
        latest_timestamp = (
            zulu.Zulu.fromtimestamp(latest_timestamp).format(
                "YYYY-MM-ddTHH:mm:ss"
            )
            + "Z"
        )
    except Exception:
        pass
    image = prepare_image_name(
        grp[lib.METADATA_FIELD][lib.IMAGE_FIELD], CONT_REDUNDANT_PATS
    )
    rv = [
        image,
        grp[lib.METADATA_FIELD][lib.IMAGEID_FIELD].strip("sha256:")[:12],
        len(grp[lib.DATA_FIELD][CONT_IDS_FIELD]),
        len(grp[lib.DATA_FIELD][MACHINES_FIELD]),
        latest_timestamp,
    ]
    return rv


def svc_grp_output_data(grp: Dict) -> List[str]:
    first_timestamp = grp[lib.METADATA_FIELD].get(
        FIRST_TIMESTAMP_FIELD, NOT_AVAILABLE
    )
    try:
        first_timestamp = (
            zulu.Zulu.fromtimestamp(first_timestamp).format(
                "YYYY-MM-ddTHH:mm:ss"
            )
            + "Z"
        )
    except Exception:
        pass
    latest_timestamp = grp[lib.METADATA_FIELD].get(
        LATEST_TIMESTAMP_FIELD, NOT_AVAILABLE
    )
    try:
        latest_timestamp = (
            zulu.Zulu.fromtimestamp(latest_timestamp).format(
                "YYYY-MM-ddTHH:mm:ss"
            )
            + "Z"
        )
    except Exception:
        pass
    rv = [
        grp[lib.METADATA_FIELD][lib.CGROUP_FIELD],
        len(grp[lib.DATA_FIELD][MACHINES_FIELD]),
        latest_timestamp,
    ]
    return rv


def cont_grp_output_data_wide(grp: Dict) -> List[str]:
    first_timestamp = grp[lib.METADATA_FIELD].get(
        FIRST_TIMESTAMP_FIELD, NOT_AVAILABLE
    )
    try:
        first_timestamp = (
            zulu.Zulu.fromtimestamp(first_timestamp).format(
                "YYYY-MM-ddTHH:mm:ss"
            )
            + "Z"
        )
    except Exception:
        pass
    latest_timestamp = grp[lib.METADATA_FIELD].get(
        LATEST_TIMESTAMP_FIELD, NOT_AVAILABLE
    )
    try:
        latest_timestamp = (
            zulu.Zulu.fromtimestamp(latest_timestamp).format(
                "YYYY-MM-ddTHH:mm:ss"
            )
            + "Z"
        )
    except Exception:
        pass
    rv = [
        grp[lib.METADATA_FIELD][lib.IMAGE_FIELD],
        grp[lib.METADATA_FIELD][lib.IMAGEID_FIELD],
        len(grp[lib.DATA_FIELD][CONT_IDS_FIELD]),
        len(grp[lib.DATA_FIELD][FINGERPRINTS_FIELD]),
        len(grp[lib.DATA_FIELD][MACHINES_FIELD]),
        first_timestamp,
        latest_timestamp,
    ]
    return rv


def svc_grp_output_data_wide(grp: Dict) -> List[str]:
    first_timestamp = grp[lib.METADATA_FIELD].get(
        FIRST_TIMESTAMP_FIELD, NOT_AVAILABLE
    )
    try:
        first_timestamp = (
            zulu.Zulu.fromtimestamp(first_timestamp).format(
                "YYYY-MM-ddTHH:mm:ss"
            )
            + "Z"
        )
    except Exception:
        pass
    latest_timestamp = grp[lib.METADATA_FIELD].get(
        LATEST_TIMESTAMP_FIELD, NOT_AVAILABLE
    )
    try:
        latest_timestamp = (
            zulu.Zulu.fromtimestamp(latest_timestamp).format(
                "YYYY-MM-ddTHH:mm:ss"
            )
            + "Z"
        )
    except Exception:
        pass
    rv = [
        grp[lib.METADATA_FIELD][lib.CGROUP_FIELD],
        len(grp[lib.DATA_FIELD][FINGERPRINTS_FIELD]),
        len(grp[lib.DATA_FIELD][MACHINES_FIELD]),
        first_timestamp,
        latest_timestamp,
    ]
    return rv


def fprint_groups_output(groups: List[FingerprintGroup]) -> Dict:
    if len(groups) == 1:
        return groups[0]
    elif len(groups) > 1:
        return {
            lib.API_FIELD: lib.API_VERSION,
            lib.ITEMS_FIELD: groups,
        }
    else:
        return {}


def recursive_length(node_list):
    answer = 0
    for d in node_list:
        for x in d.values():
            if isinstance(x, list) and isinstance(x[0], dict):
                answer += recursive_length(x)
        answer += 1
    return answer


def latest_fingerprints(fingerprints: List[Dict]) -> List[Dict]:
    fprint_map = {}
    for fingerprint in fingerprints:
        fprint_id = fingerprint["id"]
        if fprint_id not in fprint_map:
            fprint_map[fprint_id] = fingerprint
        elif fprint_map[fprint_id]["time"] <= fingerprint["time"]:
            fprint_map[fprint_id] = fingerprint
    return list(fprint_map.values())


def make_fingerprint_groups(
    fingerprints: List[Dict],
) -> Tuple[List[Dict], List[Dict]]:
    cont_fprint_grps: Dict[Tuple[str, str], ContainerFingerprintGroup] = {}
    svc_fprint_grps: Dict[str, ServiceFingerprintGroup] = {}
    for fprint in fingerprints:
        type = fprint[lib.METADATA_FIELD][lib.METADATA_TYPE_FIELD]
        if type == FPRINT_TYPE_CONT:
            image = fprint[lib.SPEC_FIELD][lib.CONT_SELECTOR_FIELD][
                lib.IMAGE_FIELD
            ]
            if not image:
                continue
            image_id = fprint[lib.SPEC_FIELD][lib.CONT_SELECTOR_FIELD][
                lib.IMAGEID_FIELD
            ]
            if not image_id:
                continue
            key = (image, image_id)
            if key not in cont_fprint_grps:
                try:
                    cont_fprint_grps[key] = ContainerFingerprintGroup(fprint)
                except Exception as e:
                    cli.try_log(
                        "Unable to create fingerprint group."
                        f" {' '.join(e.args)}"
                    )
            else:
                try:
                    cont_fprint_grps[key].add_fingerprint(fprint)
                except Exception as e:
                    cli.try_log(
                        "Unable to add fingerprint to group."
                        f" {' '.join(e.args)}"
                    )
        elif type == FPRINT_TYPE_SVC:
            cgroup = fprint[lib.SPEC_FIELD][lib.SVC_SELECTOR_FIELD][
                lib.CGROUP_FIELD
            ]
            key = cgroup
            if key not in svc_fprint_grps:
                try:
                    svc_fprint_grps[key] = ServiceFingerprintGroup(fprint)
                except Exception as e:
                    cli.try_log(
                        "Unable to create fingerprint group."
                        f" {' '.join(e.args)}"
                    )
            else:
                try:
                    svc_fprint_grps[key].add_fingerprint(fprint)
                except Exception as e:
                    cli.try_log(
                        "Unable to add fingerprint to group."
                        f" {' '.join(e.args)}"
                    )
    return (
        [grp.as_dict() for grp in cont_fprint_grps.values()],
        [grp.as_dict() for grp in svc_fprint_grps.values()],
    )
