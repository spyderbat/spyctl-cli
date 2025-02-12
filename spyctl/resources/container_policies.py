"""
Contains the logic for creating container policies from athena results
"""

import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from pydantic import BaseModel

import spyctl.config.configs as cfg
import spyctl.merge_lib.merge_object_helper as _moh
import spyctl.schemas_v2 as schemas
import spyctl.spyctl_lib as lib
from spyctl.api.objects import get_objects


def create_container_policies(
    procs: List[Dict],
    conns: List[Dict],
    conts: List[Dict],
    mode: str,
    **kwargs,
) -> List[Dict]:
    """
    Create container policies based on the provided process, connection,
    and container data.

    Args:
        procs (List[Dict]): A list of dictionaries representing process data.
        _conns (List[Dict]): A list of dictionaries representing connection
            data.
        conts (List[Dict]): A list of dictionaries representing container data.

    Returns:
        List[Dict]: A list of dictionaries representing the created container
            policies.
    """
    procs.sort(key=lambda x: x["pid"])  # sort for improved id generation
    cont_map = build_container_mappings(conts)
    build_proc_models(cont_map, procs)
    build_conn_models(cont_map, conns)
    policies = assemble_policies(cont_map, mode, **kwargs)
    return policies


def assemble_policies(cont_map: "ContainerMappings", mode: str, **kwargs) -> List[Dict]:
    """
    Assemble the container policies from the given container mappings.

    Args:
        cont_map (ContainerMappings): The container mappings.

    Returns:
        List[Dict]: A list of dictionaries representing the container policies.
    """
    rv = []
    for image_pat, pol_inp in cont_map.image_pat_to_pol_inputs.items():
        spec_dict = {
            **build_selectors(image_pat, **kwargs),
            lib.ENABLED_FIELD: True,
            lib.POL_MODE_FIELD: mode,
            lib.PROC_POLICY_FIELD: [
                pol_inp.procs[puid].base_model for puid in pol_inp.roots
            ],
            lib.NET_POLICY_FIELD: {
                lib.INGRESS_FIELD: [i.base_model for i in pol_inp.ingress.values()],
                lib.EGRESS_FIELD: [e.base_model for e in pol_inp.egress.values()],
            },
            lib.RESPONSE_FIELD: lib.RESPONSE_ACTION_TEMPLATE,
        }
        name = f"Pol for {image_pat}"[:127]
        metadata = schemas.GuardianMetadataModel(name=name, type=lib.POL_TYPE_CONT)
        spec = schemas.GuardianPolicySpecModel(**spec_dict)
        pol = schemas.GuardianPolicyModel(
            apiVersion=lib.API_VERSION,
            kind=lib.POL_KIND,
            metadata=metadata,
            spec=spec,
        )
        pol = json.loads(pol.model_dump_json(by_alias=True, exclude_none=True))
        mo = _moh.get_merge_object(lib.POL_KIND, pol, True, "create")
        rv.append(mo.get_obj_data())
    return rv


def build_selectors(image_pat: str, **kwargs) -> Dict:
    """
    Build selectors for the given image pattern.

    Args:
        image_pat (str): The image pattern.

    Returns:
        List[Dict]: A list of dictionaries representing the selectors.
    """
    rv = {}
    cs = schemas.ContainerSelectorModel(
        matchFields={
            "image": image_pat,
        }
    )
    rv[lib.CONT_SELECTOR_FIELD] = cs.model_dump(by_alias=True, exclude_none=True)
    if "image_id" in kwargs:
        rv[lib.CONT_SELECTOR_FIELD]["matchFields"]["imageID"] = kwargs["image_id"]
    if "container_id" in kwargs:
        rv[lib.CONT_SELECTOR_FIELD]["matchFields"]["containerID"] = kwargs[
            "container_id"
        ]
    if "container_name" in kwargs:
        rv[lib.CONT_SELECTOR_FIELD]["matchFields"]["containerName"] = kwargs[
            "container_name"
        ]
    if "clustername" in kwargs:
        cls = schemas.ClusterSelectorModel(
            matchFields={
                "name": kwargs["clustername"],
            }
        )
        rv[lib.CLUS_SELECTOR_FIELD] = cls.model_dump(by_alias=True, exclude_none=True)
    if "pod_namespace" in kwargs or "pod_namespace_labels" in kwargs:
        ns_labels = kwargs.get("pod_namespace_labels", {})
        sel_labels = {}
        if "pod_namespace" in kwargs:
            sel_labels["kubernetes.io/name"] = kwargs["pod_namespace"]
        sel_labels.update(ns_labels)
        ns = schemas.NamespaceSelectorModel(matchLabels=sel_labels)
        rv[lib.NAMESPACE_SELECTOR_FIELD] = ns.model_dump(
            by_alias=True, exclude_none=True
        )
    if "pod_labels" in kwargs:
        pod_labels = kwargs["pod_labels"]
        pod = schemas.PodSelectorModel(matchLabels=pod_labels)
        rv[lib.POD_SELECTOR_FIELD] = pod.model_dump(by_alias=True, exclude_none=True)
    if "hostname" in kwargs or "muid" in kwargs:
        if "hostname" in kwargs and "muid" in kwargs:
            ms = schemas.MachineSelectorModel(
                matchFields={
                    "hostname": kwargs["hostname"],
                    "muid": kwargs["muid"],
                }
            )
        elif "hostname" in kwargs:
            ms = schemas.MachineSelectorModel(
                matchFields={
                    "hostname": kwargs["hostname"],
                }
            )
        else:
            ms = schemas.MachineSelectorModel(
                matchFields={
                    "muid": kwargs["muid"],
                }
            )
        rv[lib.MACHINE_SELECTOR_FIELD] = ms.model_dump(by_alias=True, exclude_none=True)
    return rv


@dataclass
class ImageTracker:
    """
    Tracks image information. Ultimately used to determine
    How many policies to generate and where to place wildcards
    """

    tags: Set[str] = field(default_factory=set)
    repos: Set[str] = field(default_factory=set)
    cont_ids: Set[str] = field(default_factory=set)


@dataclass
class ProcModel:
    """Tracks the process model and the original record."""

    base_model: schemas.ProcessNodeModel
    rec: Dict
    key: Tuple[str, str]


@dataclass
class IngressModel:
    """Tracks the ingress conn model and the original record."""

    base_model: schemas.IngressNodeModel
    rec: Dict


@dataclass
class EgressModel:
    """Tracks the egress conn model and the original record."""

    base_model: schemas.EgressNodeModel
    rec: Dict


@dataclass
class PolicyInputs:
    """Tracks the inputs required to build a container policy"""

    procs: Dict[str, ProcModel] = field(default_factory=dict)
    proc_keys: Dict[Tuple[str, str], ProcModel] = field(default_factory=dict)
    ingress: Dict[str, IngressModel] = field(default_factory=dict)
    egress: Dict[str, EgressModel] = field(default_factory=dict)
    roots: Set = field(default_factory=set)
    proc_ids: Set = field(default_factory=set)

    def add_proc(self, proc: Dict, key: Tuple[str, str]) -> ProcModel:
        """Adds a process to the policy inputs."""
        proc["exe"] = proc["exe"].split(" (deleted)")[0]  # remove deleted
        if key in self.proc_keys:
            pm = self.proc_keys[key]
            bm = pm.base_model
            if proc["exe"] not in bm.exe and proc["exe"]:
                bm.exe.append(proc["exe"])
            if proc["euser"] not in bm.euser:
                bm.euser.append(proc["euser"])
        elif proc["id"] in self.procs:
            pm = self.procs[proc["id"]]
            bm = pm.base_model
            if proc["exe"] not in bm.exe and proc["exe"]:
                bm.exe.append(proc["exe"])
            if proc["euser"] not in bm.euser:
                bm.euser.append(proc["euser"])
        else:
            pm = ProcModel(build_proc_model(proc), proc, key)
        self.procs[proc["id"]] = pm
        self.proc_keys[key] = pm
        return pm


@dataclass
class ContainerMappings:
    """Maps container IDs to image patterns and image patterns to policy
    inputs. There should be one policy per image pattern.
    """

    cont_id_to_image_pat: Dict[str, str] = field(default_factory=dict)
    image_pat_to_pol_inputs: Dict[str, PolicyInputs] = field(default_factory=dict)


def build_container_mappings(conts: List[Dict]) -> ContainerMappings:
    """
    Builds container mappings based on the given list of containers.

    Args:
        conts (List[Dict]): A list of dictionaries representing containers.

    Returns:
        ContainerMappings: An object containing the container mappings.

    """
    rv = ContainerMappings()
    # Build image trackers
    image_trackers: Dict[str, ImageTracker] = defaultdict(
        ImageTracker
    )  # image -> tags, repos, cont_ids
    for cont in conts:
        full_image: str = cont["image"]
        repo_image, tag = full_image.rsplit(":", 1)
        repo_image = repo_image.rsplit("/", 1)
        if len(repo_image) == 1:
            repo = ""
            image = repo_image[0]
        else:
            repo, image = repo_image
        image_trackers[image].tags.add(tag)
        image_trackers[image].repos.add(repo)
        image_trackers[image].cont_ids.add(cont["id"])
    # Build container mappings
    for image, img_t in image_trackers.items():
        if len(img_t.repos) > 1:
            repo = "*"
        else:
            repo = img_t.repos.pop()
        if len(img_t.tags) > 1:
            tag = "*"
        else:
            tag = img_t.tags.pop()
        image_pat = f"{repo}/{image}:{tag}"
        rv.image_pat_to_pol_inputs[image_pat] = PolicyInputs()
        rv.cont_id_to_image_pat.update(
            {cont_id: image_pat for cont_id in img_t.cont_ids}
        )
    return rv


def build_conn_models(cont_map: ContainerMappings, conns: List[Dict]):
    """
    Builds connection models based on container mappings and connection
    information.

    Args:
        cont_map (ContainerMappings): The container mappings object containing
            the policy information.
        conns (List[Dict]): The list of connection dictionaries.

    Returns:
        None
    """
    for conn in conns:
        cont_uid = conn.get("container_uid")
        if not cont_uid:
            continue
        image_pat = cont_map.cont_id_to_image_pat[cont_uid]
        pol_inp = cont_map.image_pat_to_pol_inputs[image_pat]
        puid = sorted(conn["puids"])[-1]
        proc_model = pol_inp.procs.get(puid)
        key = proc_model.key
        if not key:
            continue
        if conn["direction"] == "inbound":
            conn_model = build_ingress_model(pol_inp, conn, proc_model)
            pol_inp.ingress[key] = conn_model
        elif conn["direction"] == "outbound":
            conn_model = build_egress_model(pol_inp, conn, proc_model)
            pol_inp.egress[key] = conn_model


def build_ingress_model(
    pol_inp: PolicyInputs, conn: Dict, proc_model: ProcModel
) -> IngressModel:
    """
    Build an ingress model based on the given connection dictionary.

    Args:
        pol_inp (PolicyInputs): The policy inputs object.
        conn (Dict): A dictionary containing connection information.
        key (str): The key to use for the connection model.

    Returns:
        schemas.IngressNodeModel: The constructed ingress model.

    """

    def add_from(new_from_obj, i_mod: IngressModel):
        old_from = i_mod.base_model.from_field
        for from_obj in old_from:
            if not isinstance(new_from_obj, type(from_obj)):
                continue
            if isinstance(new_from_obj, schemas.DnsBlockModel):
                from_obj.dns_selector = list(
                    set(from_obj.dns_selector).union(new_from_obj.dns_selector)
                )
                return
            if isinstance(new_from_obj, schemas.IpBlockModel):
                if from_obj.ip_block.cidr == new_from_obj.ip_block.cidr:
                    return
        old_from.append(new_from_obj)

    def add_port(new_port_obj: schemas.PortsModel, i_mod: IngressModel):
        old_ports = i_mod.base_model.ports
        for port_obj in old_ports:
            if (
                port_obj.port == new_port_obj.port
                and port_obj.proto == new_port_obj.proto
            ):
                return
        old_ports.append(new_port_obj)

    ports_model = schemas.PortsModel(
        port=conn["local_port"],
        protocol=conn["proto"],
    )
    from_obj = schemas.IpBlockModel(
        ipBlock=schemas.CIDRModel(cidr=f'{conn["remote_ip"]}/32')
    )
    conn_model = pol_inp.ingress.get(proc_model.key)
    if not conn_model:
        conn_model = IngressModel(
            schemas.IngressNodeModel(
                **{
                    lib.FROM_FIELD: [
                        from_obj.model_dump(by_alias=True, exclude_none=True)
                    ],
                    lib.PROCESSES_FIELD: [proc_model.base_model.id],
                    lib.PORTS_FIELD: [
                        ports_model.model_dump(by_alias=True, exclude_none=True)
                    ],
                }
            ),
            conn,
        )
    else:
        add_from(from_obj, conn_model)
        add_port(ports_model, conn_model)
        conn_model.base_model.processes = list(
            set(conn_model.base_model.processes).union([proc_model.base_model.id])
        )
    return conn_model


def build_egress_model(
    pol_inp: PolicyInputs, conn: Dict, proc_model: ProcModel
) -> EgressModel:
    """
    Build an egress model based on the given connection dictionary.

    Args:
        pol_inp (PolicyInputs): The policy inputs object.
        conn (Dict): A dictionary containing connection information.
        key (str): The key to use for the connection model.

    Returns:
        EgressModel: The constructed egress model.

    """

    def add_to(new_to_obj, i_mod: EgressModel):
        old_to = i_mod.base_model.to
        for from_obj in old_to:
            if not isinstance(new_to_obj, type(from_obj)):
                continue
            if isinstance(new_to_obj, schemas.DnsBlockModel):
                from_obj.dns_selector = list(
                    set(from_obj.dns_selector).union(new_to_obj.dns_selector)
                )
                return
            if isinstance(new_to_obj, schemas.IpBlockModel):
                if from_obj.ip_block.cidr == new_to_obj.ip_block.cidr:
                    return
        old_to.append(new_to_obj)

    def add_port(new_port_obj: schemas.PortsModel, i_mod: EgressModel):
        old_ports = i_mod.base_model.ports
        for port_obj in old_ports:
            if (
                port_obj.port == new_port_obj.port
                and port_obj.proto == new_port_obj.proto
            ):
                return
        old_ports.append(new_port_obj)

    ports_model = schemas.PortsModel(
        port=conn["remote_port"],
        protocol=conn["proto"],
    )
    if "remote_hostname" in conn:
        to_obj = schemas.DnsBlockModel(dnsSelector=conn["remote_hostname"].split(","))
    else:
        to_obj = schemas.IpBlockModel(
            ipBlock=schemas.CIDRModel(cidr=f'{conn["remote_ip"]}/32')
        )
    conn_model = pol_inp.egress.get(proc_model.key)
    if not conn_model:
        conn_model = EgressModel(
            schemas.EgressNodeModel(
                to=[to_obj.model_dump(by_alias=True, exclude_none=True)],
                processes=[proc_model.base_model.id],
                ports=[ports_model.model_dump(by_alias=True, exclude_none=True)],
            ),
            conn,
        )
    else:
        add_to(to_obj, conn_model)
        add_port(ports_model, conn_model)
        conn_model.base_model.processes = list(
            set(conn_model.base_model.processes).union([proc_model.base_model.id])
        )
    return conn_model


def build_proc_models(cont_map: ContainerMappings, procs: List[Dict]):
    """
    Builds process tree for policy based on container mappings and a list
    of processes.

    Args:
        cont_map (ContainerMappings): The container mappings object.
        procs (List[Dict]): A list of process dictionaries.

    Returns:
        None
    """
    # First pass to make a dictionary of processes
    proc_recs = {}
    for proc in procs:
        proc_recs[proc["id"]] = proc
    # Second pass find missing parents
    missing_ppuids = set()
    for proc in proc_recs.values():
        ppuid = proc["ppuid"]
        if ppuid not in proc_recs:
            missing_ppuids.add(ppuid)
    if missing_ppuids:
        proc_recs.update(find_missing_parents_in_container(list(missing_ppuids)))
    # Third pass to build the process models
    for proc in proc_recs.values():
        image_pat = cont_map.cont_id_to_image_pat[proc["container_uid"]]
        pol_inp = cont_map.image_pat_to_pol_inputs[image_pat]
        key = _proc_key(proc, proc_recs)
        pol_inp.add_proc(proc, key)
    # Link up the nodes
    for pol_inp in cont_map.image_pat_to_pol_inputs.values():
        for proc_model in list(pol_inp.proc_keys.values()):
            ppuid = proc_model.rec["ppuid"]
            if ppuid in pol_inp.procs:
                pproc_model = pol_inp.procs[ppuid]
                if not pproc_model.base_model.children:
                    pproc_model.base_model.children = [proc_model.base_model]
                else:
                    pproc_model.base_model.children.append(proc_model.base_model)
            else:
                # We found a root
                pol_inp.roots.add(proc_model.rec["id"])
            make_proc_id(proc_model, pol_inp)


def _proc_key(proc: Dict, proc_recs) -> Tuple[str, str]:
    def ancestors(_proc: Dict) -> str:
        a_list = []
        while _proc["ppuid"] in proc_recs:
            _proc = proc_recs[_proc["ppuid"]]
            a_list.append(_proc["name"])
        return "/".join(reversed(a_list))

    return ancestors(proc), proc["name"]


def build_proc_model(proc: Dict) -> BaseModel:
    """
    Build a process model based on the given process dictionary.

    Args:
        proc (Dict): A dictionary containing process information.

    Returns:
        BaseModel: The constructed process model.

    """
    proc_model = schemas.ProcessNodeModel(
        name=proc["name"],
        exe=[proc["exe"]],
        euser=[proc["euser"]],
        id="__PLACEHOLDER__",
    )
    return proc_model


def find_missing_parents_in_container(ppuids: List[str]):
    """
    Find missing parents in a container using the objects API.

    Args:
        ppuids (List[str]): A list of process IDs.

    Returns:
        Dict[str, Dict]: A dictionary mapping missing parent process IDs to
            their records.
    """
    ctx = cfg.get_current_context()
    rv = {}
    while ppuids:
        lib.try_log("Loading parent processes")
        resp = safe_get_objects(ctx, ppuids)
        new_missing = set()
        for pproc in resp:
            if pproc.get("container"):
                rv[pproc["id"]] = pproc
                new_missing.add(pproc["ppuid"])
        ppuids = list(new_missing)
    return rv


def make_proc_id(proc_model: ProcModel, pol_inp: PolicyInputs):
    """
    Generates a unique process ID for the given `proc_model`
    and adds it to the `pol_inp.proc_ids` set.

    Args:
        proc_model (ProcModel): The process model for which to generate the ID.
        pol_inp (PolicyInputs): The policy inputs object containing the set of
            existing process IDs.

    Returns:
        None
    """
    counter = 0
    proc_id = f"{proc_model.rec['name']}_{counter}"
    while proc_id in pol_inp.proc_ids:
        counter += 1
        proc_id = f"{proc_model.rec['name']}_{counter}"
    pol_inp.proc_ids.add(proc_id)
    proc_model.base_model.id = proc_id


def safe_get_objects(ctx: cfg.Context, uids: List[str]) -> List[Dict]:
    """
    Safely get objects from the API given that the
    objects API only accepts 500 ids at a time.

    Args:
        ctx (cfg.Context): The current context.
        uids (List[str]): A list of object UIDs.

    Returns:
        List[Dict]: A list of object dictionaries.
    """
    rv = []
    while uids:
        resp = get_objects(*ctx.get_api_data(), uids[:500])
        rv.extend(resp)
        uids = uids[500:]
    return rv
