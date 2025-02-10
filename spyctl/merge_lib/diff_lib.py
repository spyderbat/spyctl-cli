"""Module containing diff-specific logic"""

import json
from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

import spyctl.spyctl_lib as lib


def guardian_object_diff(original_data: Dict, other_data: Dict):
    """
    Calculate the difference between two guardian objects.
    This is an alternative
    output to string-based diffs focusing specifically on the process, and
    connection nodes within the guardian objects.

    Args:
        original_data (Dict): The original guardian object.
        other_data (Dict): The other guardian object to compare with.

    Returns:
        Dict: The difference between the two guardian objects.
    """
    rv = other_data.copy()
    rv[lib.SPEC_FIELD] = other_data[lib.SPEC_FIELD].copy()
    rv[lib.SPEC_FIELD][lib.PROC_POLICY_FIELD] = []
    rv[lib.SPEC_FIELD][lib.NET_POLICY_FIELD] = other_data[lib.SPEC_FIELD][
        lib.NET_POLICY_FIELD
    ].copy()
    rv[lib.SPEC_FIELD][lib.NET_POLICY_FIELD][lib.INGRESS_FIELD] = []
    rv[lib.SPEC_FIELD][lib.NET_POLICY_FIELD][lib.EGRESS_FIELD] = []
    orig_spec = original_data[lib.SPEC_FIELD]
    other_spec = other_data[lib.SPEC_FIELD]
    rv[lib.SPEC_FIELD][lib.PROC_POLICY_FIELD] = guardian_procs_diff(
        orig_spec, other_spec
    )
    rv[lib.SPEC_FIELD][lib.NET_POLICY_FIELD] = guardian_network_diff(
        orig_spec, other_spec
    )
    return rv


def guardian_procs_diff(original_spec, other_spec):
    def guardian_proc_diff(
        other_proc: Dict, orig_procs: List[Dict], rv: List[Dict]
    ):
        diff_proc = other_proc.copy()
        diff_proc.pop(lib.CHILDREN_FIELD, None)
        match_proc = None
        if not orig_procs:
            # If the process is new, document the node as added
            diff_proc["diff"] = "added"
        else:
            # Check to see if another process has a matching ID
            for orig_proc in orig_procs:
                if diff_proc[lib.ID_FIELD] == orig_proc[lib.ID_FIELD]:
                    cmp1 = diff_proc.copy()
                    cmp1.pop(lib.CHILDREN_FIELD, None)
                    cmp2 = orig_proc.copy()
                    cmp2.pop(lib.CHILDREN_FIELD, None)
                    # The processes are different, document the node as changed
                    if cmp1 != cmp2:
                        diff_proc["diff"] = "changed"
                    match_proc = orig_proc
                    break
            # We didn't find a matching ID so document the node as added
            if not match_proc:
                diff_proc["diff"] = "added"
        # Recursively check
        if lib.CHILDREN_FIELD in other_proc:
            diff_proc[lib.CHILDREN_FIELD] = []
            orig_children = (
                match_proc.get(lib.CHILDREN_FIELD, []) if match_proc else []
            )
            for c_proc in other_proc[lib.CHILDREN_FIELD]:
                guardian_proc_diff(
                    c_proc,
                    orig_children,
                    diff_proc[lib.CHILDREN_FIELD],
                )
        rv.append(diff_proc)

    def guardian_proc_check_removed(
        orig_proc: Dict, other_procs: List[Dict], rv: List[Dict]
    ):
        # Check to see if another process has a matching ID
        match_proc = None
        for other_proc in other_procs:
            if orig_proc[lib.ID_FIELD] == other_proc[lib.ID_FIELD]:
                match_proc = other_proc
                break
        if not match_proc:
            # If the process is removed, document
            # the node and all of its children as removed
            diff_proc = deepcopy(orig_proc)
            guardian_proc_set_removed(diff_proc)
            rv.append(diff_proc)
        else:
            # Recursively check
            if lib.CHILDREN_FIELD in orig_proc:
                for c_proc in orig_proc[lib.CHILDREN_FIELD]:
                    guardian_proc_check_removed(
                        c_proc,
                        match_proc.get(lib.CHILDREN_FIELD, []),
                        orig_proc[lib.CHILDREN_FIELD],
                    )

    def guardian_proc_set_removed(diff_proc):
        diff_proc["diff"] = "removed"
        if lib.CHILDREN_FIELD in diff_proc:
            for c_proc in diff_proc[lib.CHILDREN_FIELD]:
                guardian_proc_set_removed(c_proc)

    rv = []
    orig_procs = original_spec[lib.PROC_POLICY_FIELD]
    other_procs = other_spec[lib.PROC_POLICY_FIELD]
    for other_proc in other_procs:
        guardian_proc_diff(other_proc, orig_procs, rv)
    for orig_proc in orig_procs:
        guardian_proc_check_removed(orig_proc, other_procs, rv)
    return rv


def guardian_network_diff(original_spec, other_spec):
    @dataclass(frozen=True)
    class GuardianNetNode:
        to_or_from: List
        ports: List[str]
        type: str
        processes: List[str] = None

        def as_dict(self):
            tf_str = (
                lib.FROM_FIELD
                if self.type == lib.INGRESS_FIELD
                else lib.TO_FIELD
            )
            rv = {
                tf_str: self.to_or_from,
                lib.PORTS_FIELD: self.ports,
            }
            if self.processes:
                rv[lib.PROCESSES_FIELD] = self.processes
            return rv

        def __hash__(self) -> int:
            return hash(json.dumps(self.as_dict(), sort_keys=True))

    def guardian_net_node_diff(
        other_nodes: Set[GuardianNetNode],
        orig_nodes: Set[GuardianNetNode],
        rv_nodes: List[Dict],
    ):
        added = other_nodes.difference(orig_nodes)
        for node in added:
            rv_node = node.as_dict()
            rv_node["diff"] = "added"
            rv_nodes.append(rv_node)
        removed = orig_nodes.difference(other_nodes)
        for node in removed:
            rv_node = node.as_dict()
            rv_node["diff"] = "removed"
            rv_nodes.append(rv_node)
        unchanged = other_nodes.intersection(orig_nodes)
        for node in unchanged:
            rv_node = node.as_dict()
            rv_nodes.append(rv_node)

    def make_individual_node_set(nodes: List[Dict]) -> Set[GuardianNetNode]:
        rv = set()
        for node in nodes:
            if lib.FROM_FIELD in node:
                net_type = lib.INGRESS_FIELD
            else:
                net_type = lib.EGRESS_FIELD
            to_or_from = node.get(lib.TO_FIELD, node.get(lib.FROM_FIELD, []))
            processes = node.get(lib.PROCESSES_FIELD, [])
            ports = node.get(lib.PORTS_FIELD, [])
            for tf in to_or_from:
                parse_to_from(rv, tf, processes, ports, net_type)
        return rv

    def parse_to_from(
        rv_set: Set,
        tf: Dict,
        processes: Optional[List[str]],
        ports: List[str],
        net_type: str,
    ):
        if lib.DNS_SELECTOR_FIELD in tf:
            for dns_name in tf[lib.DNS_SELECTOR_FIELD]:
                for port in ports:
                    if processes:
                        for proc in processes:
                            rv_set.add(
                                GuardianNetNode(
                                    [{lib.DNS_SELECTOR_FIELD: [dns_name]}],
                                    [port],
                                    net_type,
                                    [proc],
                                )
                            )
                    else:
                        rv_set.add(
                            GuardianNetNode(
                                {lib.DNS_SELECTOR_FIELD: [dns_name]},
                                [port],
                                net_type,
                            )
                        )
        else:
            for port in ports:
                if processes:
                    for proc in processes:
                        rv_set.add(
                            GuardianNetNode([tf], [port], net_type, [proc])
                        )
                else:
                    rv_set.add(GuardianNetNode([tf], [port], net_type))

    rv = {
        lib.INGRESS_FIELD: [],
        lib.EGRESS_FIELD: [],
    }
    orig_ingress = make_individual_node_set(
        original_spec[lib.NET_POLICY_FIELD][lib.INGRESS_FIELD]
    )
    other_ingress = make_individual_node_set(
        other_spec[lib.NET_POLICY_FIELD][lib.INGRESS_FIELD]
    )
    guardian_net_node_diff(other_ingress, orig_ingress, rv[lib.INGRESS_FIELD])
    orig_egress = make_individual_node_set(
        original_spec[lib.NET_POLICY_FIELD][lib.EGRESS_FIELD]
    )
    other_egress = make_individual_node_set(
        other_spec[lib.NET_POLICY_FIELD][lib.EGRESS_FIELD]
    )
    guardian_net_node_diff(other_egress, orig_egress, rv[lib.EGRESS_FIELD])
    return rv
