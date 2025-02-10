# pylint: disable=broad-exception-caught

import json
from typing import Dict, List, Optional, Set, Tuple, Union

import zulu
from tabulate import tabulate

import spyctl.api.policies as api
import spyctl.config.configs as cfg
import spyctl.filter_resource as filt
import spyctl.merge_lib.merge_object as m_obj
import spyctl.merge_lib.merge_object_helper as _m_obj_h
import spyctl.merge_lib.merge_schema as _ms
import spyctl.resources.api_filters as _af
import spyctl.resources.fingerprints as spyctl_fprints
import spyctl.resources.resources_lib as r_lib
import spyctl.schemas_v2 as schemas
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.source_query_resources import get_fingerprints
from spyctl.config.configs import get_current_context
from spyctl.filter_resource import filter_obj

FPRINT_KIND = spyctl_fprints.FPRINT_KIND
GROUP_KIND = spyctl_fprints.GROUP_KIND
BASELINE_KIND = lib.BASELINE_KIND
POLICY_KIND = lib.POL_KIND

POLICY_SUB_TYPES = {lib.POL_TYPE_TRACE: "suppression"}


def get_policy_subtype(pol_type: str) -> str:
    """
    Returns the subtype of a policy based on its type.

    Args:
        pol_type (str): The type of the policy.

    Returns:
        str: The subtype of the policy. If the subtype is not found, it
            returns "guardian".
    """
    return POLICY_SUB_TYPES.get(pol_type, "guardian")


class InvalidPolicyError(Exception):
    pass


class Policy:
    required_keys = {
        lib.API_FIELD,
        lib.KIND_FIELD,
        lib.METADATA_FIELD,
        lib.SPEC_FIELD,
    }

    def __init__(
        self,
        obj: Dict,
        name: str = None,
        mode: str = lib.POL_MODE_AUDIT,
        disable_procs: str = None,
        disable_conns: str = None,
    ) -> None:
        for key in self.required_keys:
            if key not in obj:
                raise InvalidPolicyError(f"Missing {key} for input object")
        self.metadata = obj[lib.METADATA_FIELD]
        if name:
            self.metadata[lib.METADATA_NAME_FIELD] = name
        self.spec: Dict = obj[lib.SPEC_FIELD]
        self.response_actions = obj[lib.SPEC_FIELD].get(
            lib.RESPONSE_FIELD, lib.RESPONSE_ACTION_TEMPLATE
        )
        self.mode = obj[lib.SPEC_FIELD].get(lib.POL_MODE_FIELD, mode)
        self.spec[lib.POL_MODE_FIELD] = self.mode
        self.spec[lib.RESPONSE_FIELD] = self.response_actions
        self.__parse_disable_procs(disable_procs)
        self.__parse_disable_conns(disable_conns)

    def spec_dict(self):
        spec_field_names = [
            lib.PROC_POLICY_FIELD,
            lib.NET_POLICY_FIELD,
            lib.RESPONSE_FIELD,
        ]
        selectors = {}
        other_fields = {}
        pol_fields = {}
        for k, v in self.spec.items():
            if "Selector" in k:
                selectors[k] = v
            if k in spec_field_names:
                continue
            else:
                other_fields[k] = v
        for name in spec_field_names:
            pol_fields[name] = self.spec[name]
        rv = {}
        rv.update(selectors)
        rv.update(other_fields)
        rv.update(pol_fields)
        return rv

    def as_dict(self):
        rv = {
            lib.API_FIELD: lib.API_VERSION,
            lib.KIND_FIELD: POLICY_KIND,
            lib.METADATA_FIELD: self.metadata,
            lib.SPEC_FIELD: self.spec_dict(),
        }
        return rv

    def __parse_disable_procs(self, disable_procs: Optional[str]):
        if disable_procs == lib.DISABLE_PROCS_ALL:
            self.spec[lib.DISABLE_PROCS_FIELD] = lib.DISABLE_PROCS_ALL

    def __parse_disable_conns(self, disable_conns: Optional[str]):
        if disable_conns == lib.DISABLE_CONNS_ALL:
            self.spec[lib.DISABLE_CONNS_FIELD] = lib.DISABLE_CONNS_ALL
        elif disable_conns == lib.DISABLE_CONNS_EGRESS:
            self.spec[lib.DISABLE_CONNS_FIELD] = lib.EGRESS_FIELD
        elif disable_conns == lib.DISABLE_CONNS_INGRESS:
            self.spec[lib.DISABLE_CONNS_FIELD] = lib.INGRESS_FIELD
        elif disable_conns == lib.DISABLE_CONNS_PRIVATE:
            self.spec[lib.DISABLE_PR_CONNS_FIELD] = lib.DISABLE_CONNS_ALL
        elif disable_conns == lib.DISABLE_CONNS_PRIVATE_E:
            self.spec[lib.DISABLE_PR_CONNS_FIELD] = lib.EGRESS_FIELD
        elif disable_conns == lib.DISABLE_CONNS_PRIVATE_I:
            self.spec[lib.DISABLE_PR_CONNS_FIELD] = lib.INGRESS_FIELD
        elif disable_conns == lib.DISABLE_CONNS_PUBLIC:
            self.spec[lib.DISABLE_PU_CONNS_FIELD] = lib.DISABLE_CONNS_ALL
        elif disable_conns == lib.DISABLE_CONNS_PUBLIC_E:
            self.spec[lib.DISABLE_PU_CONNS_FIELD] = lib.EGRESS_FIELD
        elif disable_conns == lib.DISABLE_CONNS_PUBLIC_I:
            self.spec[lib.DISABLE_PU_CONNS_FIELD] = lib.INGRESS_FIELD


def get_data_for_api_call(policy: Policy) -> Tuple[Optional[str], str]:
    policy = policy.as_dict()
    name = policy[lib.METADATA_FIELD][lib.METADATA_NAME_FIELD]
    pol_type = policy[lib.METADATA_FIELD][lib.METADATA_TYPE_FIELD]
    tags = policy[lib.METADATA_FIELD].get(lib.METADATA_TAGS_FIELD)
    uid = policy[lib.METADATA_FIELD].get(lib.METADATA_UID_FIELD, "")
    policy_selectors = {
        key: value
        for key, value in policy[lib.SPEC_FIELD].items()
        if key.endswith("Selector")
    }
    data = {
        lib.API_REQ_FIELD_NAME: name[:32],
        lib.API_REQ_FIELD_POLICY: json.dumps(policy),
        lib.API_REQ_FIELD_POL_SELECTORS: json.dumps(policy_selectors),
        lib.API_REQ_FIELD_TYPE: pol_type,
        lib.API_REQ_FIELD_UID: uid,
    }
    if tags:
        data[lib.API_REQ_FIELD_TAGS] = tags
    else:
        data[lib.API_REQ_FIELD_TAGS] = []
    return uid, data


def create_policy(
    input_data: Union[Dict, List[Dict]],
    mode: str,
    name: str = None,
    ctx: cfg.Context = None,
    disable_procs: str = None,
    disable_conns: str = None,
    include_imageid: bool = False,
):
    input_objs = []
    if isinstance(input_data, list):
        if len(input_data) == 0:
            cli.err_exit("Nothing to build policy with")
        for datum in input_data:
            input_objs.extend(r_lib.handle_input_data(datum, ctx))
    else:
        input_objs.extend(r_lib.handle_input_data(input_data, ctx))
    if len(input_objs) == 0:
        cli.err_exit("Nothing to build policy with")
    merge_object = m_obj.MergeObject(
        input_objs[0],
        _ms.POLICY_MERGE_SCHEMAS,
        None,
        disable_procs=disable_procs,
        disable_conns=disable_conns,
    )
    if len(input_objs) == 1:
        merge_object.asymmetric_merge({})
    else:
        for obj in input_objs[1:]:
            merge_object.symmetric_merge(obj)
    try:
        policy = Policy(
            merge_object.get_obj_data(),
            name,
            mode,
            disable_procs,
            disable_conns,
        )
    except InvalidPolicyError as e:
        cli.err_exit(f"Unable to create policy. {' '.join(e.args)}")
    # Validate the policy.
    rv = policy.as_dict()
    if not schemas.valid_object(rv):
        cli.err_exit("Created policy failed validation.")
    if not include_imageid:
        container_selector = rv[lib.SPEC_FIELD].get(lib.CONT_SELECTOR_FIELD)
        if container_selector:
            container_selector.pop(lib.IMAGEID_FIELD, None)
    return rv


def policies_output(policies: List[Dict]):
    if len(policies) == 1:
        return policies[0]
    elif len(policies) > 1:
        return {lib.API_FIELD: lib.API_VERSION, lib.ITEMS_FIELD: policies}
    else:
        return {}


def matching_fingerprints_summary(
    ctx: cfg.Context,
    policies: List[Dict],
    time: Tuple[float, float],
    limit_mem,
):
    has_matching = []
    no_matching = []
    sources, filters = _af.Fingerprints.build_sources_and_filters()
    pipeline = _af.Fingerprints.generate_pipeline(filters=filters)
    fingerprints = list(
        get_fingerprints(
            *ctx.get_api_data(),
            sources,
            time,
            pipeline=pipeline,
            limit_mem=limit_mem,
        )
    )
    for policy in policies:
        filters = lib.selectors_to_filters(policy)
        if filt.filter_fingerprints(
            fingerprints,
            use_context_filters=False,
            suppress_warning=True,
            **filters,
        ):
            has_matching.append(policy)
        else:
            no_matching.append(policy)
    output_list = []
    headers = ["UID", "NAME", "STATUS", "TYPE", "CREATE_TIME"]
    if len(no_matching) > 0:
        output_list.append(
            "Policies WITH NO matching fingerprints in last query:"
        )
        no_match_data = []
        for pol in no_matching:
            no_match_data.append(policy_summary_data(pol))
        output_list.append(tabulate(no_match_data, headers, tablefmt="plain"))
    if len(has_matching) > 0:
        output_list.append(
            "\nPolicies WITH matching fingerprints in last query:"
        )
        data = []
        for pol in has_matching:
            data.append(policy_summary_data(pol))
        data.sort(key=lambda x: [x[3], x[1]])
        output_list.append(tabulate(data, headers, tablefmt="plain"))
    return "\n".join(output_list)


def policies_summary_output(
    policies: List[Dict],
    time: Tuple[float, float] = None,
    get_deviations_count: bool = False,
    suppress_msg=False,
    dev_name_or_uid=None,
    dev_filters=None,
    include_irrelevant=False,
):
    if dev_filters is None:
        dev_filters = {}
    output_list = []
    if get_deviations_count:
        headers = [
            "UID",
            "NAME",
            "STATUS",
            "TYPE",
            "VERSION",
            "CREATE_TIME",
            "DEVIATIONS_(UNIQ/TOT)",
        ]
    else:
        headers = ["UID", "NAME", "STATUS", "TYPE", "VERSION", "CREATE_TIME"]
    data = []
    deviation_counts = {}
    if get_deviations_count:
        deviation_counts = get_deviation_counts(
            policies,
            time,
            suppress_msg,
            dev_name_or_uid,
            dev_filters=dev_filters,
            include_irrelevant=include_irrelevant,
        )
    for policy in policies:
        data.append(
            policy_summary_data(policy, deviation_counts, get_deviations_count)
        )
    data.sort(key=lambda x: [x[3], x[1]])
    output_list.append(tabulate(data, headers, tablefmt="plain"))
    return "\n".join(output_list)


def policy_summary_data(
    policy: Dict, deviations_counts=None, get_deviations_count=False
):
    if deviations_counts is None:
        deviations_counts = {}
    uid = policy[lib.METADATA_FIELD].get(lib.METADATA_UID_FIELD)
    status = policy[lib.SPEC_FIELD].get(lib.ENABLED_FIELD, True)
    mode = policy[lib.SPEC_FIELD].get(lib.POL_MODE_FIELD, lib.POL_MODE_ENFORCE)
    if status is False and uid:
        status = "Disabled"
    elif status is False and not uid:
        status = "Not Applied & Disabled"
    elif status and mode == lib.POL_MODE_ENFORCE and uid:
        status = "Enforcing"
    elif status and mode == lib.POL_MODE_AUDIT and uid:
        status = "Auditing"
    else:
        status = "Not Applied"
    if not uid:
        uid = "N/A"
    create_time = policy[lib.METADATA_FIELD].get(lib.METADATA_CREATE_TIME)
    if create_time:
        try:
            create_time = (
                zulu.parse(create_time).format("YYYY-MM-ddTHH:mm:ss") + "Z"
            )
        except Exception:
            pass
    else:
        create_time = "N/A"
    rv = [
        uid,
        policy[lib.METADATA_FIELD][lib.NAME_FIELD],
        status,
        policy[lib.METADATA_FIELD][lib.TYPE_FIELD],
        policy[lib.METADATA_FIELD][lib.VERSION_FIELD],
        create_time,
    ]
    if get_deviations_count:
        counts = deviations_counts.get(uid)
        if not counts:
            rv.append("0/0")
        else:
            rv.append(f"{len(counts[0])}/{counts[1]}")
    return rv


def get_policy_by_uid(
    uid: str, policies: Optional[List[Dict]] = None
) -> Optional[Dict]:

    ctx = get_current_context()
    if not policies:
        policies = api.get_policies(*ctx.get_api_data())
    policies = filter_obj(
        policies,
        [
            [lib.METADATA_FIELD, lib.METADATA_UID_FIELD],
        ],
        uid,
    )
    if not policies:
        return None
    return policies[0]


def get_deviation_counts(
    policies: List[Dict],
    time: Tuple[float, float],
    suppress_msg=False,
    dev_name_or_uid=None,
    dev_filters=None,
    include_irrelevant=False,
) -> Dict:
    import spyctl.resources.deviations as spyctl_dev

    if dev_filters is None:
        dev_filters = {}
    if not suppress_msg:
        cli.try_log(
            f"Getting policy deviations from {lib.epoch_to_zulu(time[0])} to"
            f" {lib.epoch_to_zulu(time[1])}"
        )
    rv: Dict[str, List[Set, int]] = {}
    ctx = cfg.get_current_context()
    policy_uids = {
        policy[lib.METADATA_FIELD].get(
            lib.METADATA_UID_FIELD
        ): _m_obj_h.get_merge_object(
            lib.POL_KIND, policy, True, "check_deviations"
        )
        for policy in policies
    }  # policy uid -> merge object
    pipeline = _af.Deviations.generate_pipeline(
        dev_name_or_uid, filters=dev_filters
    )
    for deviation in spyctl_dev.get_deviations_stream(
        ctx,
        list(policy_uids),
        time,
        pipeline,
        disable_pbar_on_first=not lib.is_redirected(),
        raw_data=True,
        policies=policies,
        include_irrelevant=include_irrelevant,
    ):
        checksum = deviation[lib.CHECKSUM_FIELD]
        pol_uid = deviation["policy_uid"]
        if pol_uid not in rv:
            rv[pol_uid] = [set(), 0]
        rv[pol_uid][0].add(checksum)
        rv[pol_uid][1] += 1
    return rv


def filter_policies_by_name_or_uid(policies, name_or_uid):
    if name_or_uid:
        policies = filt.filter_obj(
            policies,
            [
                [lib.METADATA_FIELD, lib.NAME_FIELD],
                [lib.METADATA_FIELD, lib.METADATA_UID_FIELD],
            ],
            name_or_uid,
        )
    else:
        return policies
