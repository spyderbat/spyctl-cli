"""
Contains the logic for creating linux service policies from athena results
"""

import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

import spyctl.config.configs as cfg
import spyctl.merge_lib.merge_object_helper as _moh
import spyctl.schemas_v2 as schemas
import spyctl.spyctl_lib as lib
from spyctl.resources.container_policies import (
    PolicyInputs,
    build_egress_model,
    build_ingress_model,
    make_proc_id,
    safe_get_objects,
)


def create_service_policies(
    procs: List[Dict],
    conns: List[Dict],
    mode: str,
    **kwargs,
) -> List[Dict]:
    """
    Create Linux service policies based on the provided process and connection
    data.

    Args:
        procs (List[Dict]): A list of dictionaries representing process data.
        conns (List[Dict]): A list of dictionaries representing connection
            data.

    Returns:
        List[Dict]: A list of dictionaries representing the created Linux
            service policies.
    """
    procs.sort(key=lambda x: x["pid"])  # sort for improved id generation
    svc_map = build_svc_mappings(procs)
    build_proc_models(svc_map, procs)
    build_conn_models(svc_map, conns)
    policies = assemble_policies(svc_map, mode, **kwargs)
    return policies


def assemble_policies(svc_map: "ServiceMappings", mode: str, **kwargs) -> List[Dict]:
    """
    Assemble the Linux service policies from the given service mappings.

    Args:
        svc_map (ServiceMappings): The service mappings.

    Returns:
        List[Dict]: A list of dictionaries representing the Linux service
            policies.
    """
    rv = []
    for svc_pat, pol_inp in svc_map.svc_pat_to_pol_inputs.items():
        spec_dict = {
            **build_selectors(svc_pat, **kwargs),
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
        name = f"Pol for {svc_pat}"[:127]
        metadata = schemas.GuardianMetadataModel(name=name, type=lib.POL_TYPE_SVC)
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


def build_selectors(svc_pat: str, **kwargs) -> Dict:
    """
    Build selectors for the given svc pattern.

    Args:
        svc_pat (str): The svc pattern.

    Returns:
        List[Dict]: A list of dictionaries representing the selectors.
    """
    rv = {}
    svc_s = schemas.ServiceSelectorModel(
        matchFields={
            "cgroup": svc_pat,
        }
    )
    rv[lib.SVC_SELECTOR_FIELD] = svc_s.model_dump(by_alias=True, exclude_none=True)
    if "service_name" in kwargs:
        rv[lib.SVC_SELECTOR_FIELD]["matchFields"]["name"] = kwargs["service_name"]
    if "clustername" in kwargs:
        cls = schemas.ClusterSelectorModel(
            matchFields={
                "name": kwargs["clustername"],
            }
        )
        rv[lib.CLUS_SELECTOR_FIELD] = cls.model_dump(by_alias=True, exclude_none=True)
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
class ServiceMappings:
    """Maps cgroups to svc patterns and svc patterns to policy
    inputs. There should be one policy per svc pattern.
    """

    cgroup_to_svc_pat: Dict[str, str] = field(default_factory=dict)
    svc_pat_to_pol_inputs: Dict[str, PolicyInputs] = field(default_factory=dict)


@dataclass
class SvcTracker:
    """
    Tracks Linux service information. Ultimately, this will be used to
    determine how many policies to generate and where to place wildcards
    """

    cgroup_paths: Set[str] = field(default_factory=set)
    cgroups: Set[str] = field(default_factory=set)


def build_svc_mappings(procs: List[Dict]) -> ServiceMappings:
    """
    Builds service mappings based on the provided list of processes.

    Args:
        procs (List[Dict]): A list of dictionaries representing processes.

    Returns:
        ServiceMappings: An instance of the ServiceMappings class containing
            the service mappings.

    """
    rv = ServiceMappings()
    svc_trackers: Dict[str, SvcTracker] = defaultdict(SvcTracker)
    for proc in procs:
        cgroup: str = proc["cgroup"]
        cgroup_path, svc_name = cgroup.rsplit("/", 1)
        svc_trackers[svc_name].cgroup_paths.add(cgroup_path)
        svc_trackers[svc_name].cgroups.add(cgroup)
    # Build svc mappings
    for svc_name, svc_t in svc_trackers.items():
        if len(svc_t.cgroup_paths) > 1:
            cgroup_path = "*/system.slice/*"
        else:
            cgroup_path = svc_t.cgroup_paths.pop()
        svc_pat = f"{cgroup_path}/{svc_name}"
        rv.svc_pat_to_pol_inputs[svc_pat] = PolicyInputs()
        rv.cgroup_to_svc_pat.update({cgroup: svc_pat for cgroup in svc_t.cgroups})
    return rv


def build_conn_models(svc_map: ServiceMappings, conns: List[Dict]):
    """
    Builds connection models based on service mappings and connection
    information.

    Args:
        svc_map (ServiceMappings): The service mappings object containing
            the policy information.
        conns (List[Dict]): The list of connection dictionaries.

    Returns:
        None
    """
    for conn in conns:
        cgroup = conn.get("cgroup")
        if not cgroup:
            continue
        svc_pat = svc_map.cgroup_to_svc_pat[cgroup]
        pol_inp = svc_map.svc_pat_to_pol_inputs[svc_pat]
        puid = sorted(conn["puids"])[-1]
        proc_model = pol_inp.procs.get(puid)
        if not proc_model:
            continue
        key = proc_model.key
        if not key:
            continue
        if conn["direction"] == "inbound":
            conn_model = build_ingress_model(pol_inp, conn, proc_model)
            pol_inp.ingress[key] = conn_model
        elif conn["direction"] == "outbound":
            conn_model = build_egress_model(pol_inp, conn, proc_model)
            pol_inp.egress[key] = conn_model


def build_proc_models(svc_map: ServiceMappings, procs: List[Dict]):
    """
    Builds process tree for policy based on service mappings and a list
    of processes.

    Args:
        svc_map (ServiceMappings): The service mappings object.
        procs (List[Dict]): A list of process dictionaries.

    Returns:
        None
    """
    # First pass to make a dictionary of processes
    proc_recs = {}
    for proc in procs:
        if not proc.get("name") or not proc.get("exe"):
            continue
        proc_recs[proc["id"]] = proc
    # Second pass find missing parents
    missing_ppuids = defaultdict(set)  # ppuid -> cgroup
    for proc in proc_recs.values():
        ppuid = proc["ppuid"]
        cgroup = proc["cgroup"]
        if ppuid not in proc_recs:
            missing_ppuids[ppuid].add(cgroup)
    if missing_ppuids:
        proc_recs.update(find_missing_parents_in_cgroup(missing_ppuids))
    # Third pass to build the process models
    for proc in proc_recs.values():
        svc_pat = svc_map.cgroup_to_svc_pat[proc["cgroup"]]
        pol_inp = svc_map.svc_pat_to_pol_inputs[svc_pat]
        key = _proc_key(proc, proc_recs)
        pol_inp.add_proc(proc, key)
    # Link up the nodes
    for pol_inp in svc_map.svc_pat_to_pol_inputs.values():
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


def find_missing_parents_in_cgroup(ppuids: Dict[str, Set[str]]):
    """
    Find missing parents in a service using the objects API.

    Args:
        ppuids (Dict[str, Set[str]]): A dict of process ids to child cgroups.

    Returns:
        Dict[str, Dict]: A dictionary mapping missing parent process IDs to
            their records.
    """
    ctx = cfg.get_current_context()
    rv = {}
    while ppuids:
        lib.try_log("Loading parent processes")
        resp = safe_get_objects(ctx, list(ppuids))
        new_missing = defaultdict(set)  # ppuid -> cgroup
        for pproc in resp:
            ppuid = pproc["id"]
            p_cgroup = pproc.get("cgroup")
            if (
                pproc.get("cgroup") in ppuids[ppuid]
                and pproc.get("name")
                and pproc.get("exe")
            ):
                rv[ppuid] = pproc
                new_missing[pproc["ppuid"]].add(p_cgroup)
        ppuids = new_missing
    return rv
