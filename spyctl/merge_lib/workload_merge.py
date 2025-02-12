"""
Module containing merge code specific to workload policies
"""

# pylint: disable=protected-access, raise-missing-from, too-many-lines

from __future__ import annotations

import fnmatch
import ipaddress as ipaddr
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Union

import spyctl.merge_lib.merge_lib as m_lib
import spyctl.spyctl_lib as lib
from spyctl import cli

if TYPE_CHECKING:
    from spyctl.merge_lib.merge_object import MergeObject


class InvalidNetworkNode(Exception):
    pass


class ProcessNode:
    def __init__(
        self,
        node_list: "ProcessNodeList",
        node_data: Dict,
        eusers=None,
        parent=None,
    ) -> None:
        if not eusers:
            eusers = []
        self.node = node_data.copy()
        self.name = node_data[lib.NAME_FIELD]
        self.id = node_data[lib.ID_FIELD]
        self.merged_id = None  # New id if merged
        self.exes: List[str] = node_data[lib.EXE_FIELD]
        self.eusers: List[str] = self.node.get(lib.EUSER_FIELD, eusers)
        self.node_list = node_list
        self.parent = parent
        self.children = []
        self.listening_sockets: List["PortRange"] = []
        self.__parse_listening_sockets()
        if lib.CHILDREN_FIELD in self.node:
            self.children = [
                child[lib.ID_FIELD] for child in self.node[lib.CHILDREN_FIELD]
            ]

    def symmetrical_merge(self, other_node: "ProcessNode"):
        self.name = m_lib.make_wildcard([self.name, other_node.name])
        self.__merge_exes(other_node.exes)
        self.__merge_eusers(other_node.eusers)
        self.__merge_listening_socks(other_node.listening_sockets)
        other_node.merged_id = self.id

    def asymmetrical_merge(self, other_node: "ProcessNode"):
        if not fnmatch.fnmatch(other_node.name, self.name):
            raise m_lib.InvalidMergeError("Bug detected, name mismatch in merge.")
        self.__merge_exes(other_node.exes)
        self.__merge_eusers(other_node.eusers)
        self.__merge_listening_socks(other_node.listening_sockets)
        other_node.merged_id = self.id

    def as_dict(self, parent_eusers: List[str] = None) -> Dict:
        rv = {}
        rv[lib.NAME_FIELD] = self.name
        rv[lib.EXE_FIELD] = sorted(self.exes)
        rv[lib.ID_FIELD] = self.id
        if parent_eusers and set(parent_eusers) != set(self.eusers):
            rv[lib.EUSER_FIELD] = sorted(self.eusers)
        elif not parent_eusers:
            rv[lib.EUSER_FIELD] = sorted(self.eusers)
        if self.listening_sockets:
            rv[lib.LISTENING_SOCKETS] = sorted(
                [l_sock.as_dict() for l_sock in self.listening_sockets],
                key=lambda d: d[lib.PORT_FIELD],
            )
        if len(self.children) > 0:
            child_nodes = [self.node_list.get_node(c_id) for c_id in self.children]
            rv[lib.CHILDREN_FIELD] = [n.as_dict(self.eusers) for n in child_nodes]
            rv[lib.CHILDREN_FIELD].sort(key=lambda x: x[lib.NAME_FIELD])
        return rv

    def symmetrical_in(self, other) -> bool:
        if isinstance(other, __class__):
            if not self.__match_exes(other.exes):
                return False
            wildcard_name = m_lib.make_wildcard([self.name, other.name])
            if not fnmatch.fnmatch(other.name, self.name) and not wildcard_name:
                return False
            return True
        return False

    def __parse_listening_sockets(self):
        socket_list = self.node.get(lib.LISTENING_SOCKETS)
        if socket_list:
            for sock in socket_list:
                port = sock[lib.PORT_FIELD]
                proto = sock[lib.PROTO_FIELD]
                endport = sock.get(lib.ENDPORT_FIELD)
                self.listening_sockets.append(PortRange(port, proto, endport))

    def __contains__(self, other):
        if isinstance(other, __class__):
            if not fnmatch.fnmatch(other.name, self.name):
                return False
            if not self.__match_exes(other.exes):
                return False
            return True
        return False

    def __eq__(self, other):
        if isinstance(other, __class__):
            if not (
                fnmatch.fnmatch(other.name, self.name)
                or fnmatch.fnmatch(self.name, other.name)
            ):
                return False
            if not self.__match_exes(other.exes, strict=True, single_match=True):
                return False
            if not self.__match_eusers(other.eusers):
                return False
            if not self.__match_listening_socks(other.listening_sockets):
                return False
            return True
        return False

    def __match_exe(self, other_exe: List[str], strict=False) -> bool:
        if other_exe in self.exes:
            return True
        other_name = Path(other_exe).name
        for exe in self.exes:
            if fnmatch.fnmatch(other_exe, exe):
                return True
            if not strict:
                exe_name = Path(exe).name
                if fnmatch.fnmatch(other_name, exe_name):
                    return True
        return False

    def __match_exes(self, other_exes: str, strict=False, single_match=False) -> bool:
        match = False
        for other_exe in other_exes:
            if single_match:
                if self.__match_exe(other_exe, strict):
                    match = True
                    break
            if not self.__match_exe(other_exe, strict):
                return False
        # For symmetrical in, we only care if two processes share at least one
        # overlapping exe, hence the single match logic.
        if single_match and not match:
            return False
        return True

    def __match_euser(self, other_euser: str):
        if other_euser in self.eusers:
            return True
        for euser in self.eusers:
            if fnmatch.fnmatch(other_euser, euser):
                return True
        return False

    def __match_eusers(self, other_eusers: List[str]) -> bool:
        for other_euser in other_eusers:
            if not self.__match_euser(other_euser):
                return False
        return True

    def __match_listening_sock(self, other_sock: "PortRange") -> bool:
        for sock in self.listening_sockets:
            if other_sock in sock:
                return True
        return False

    def __match_listening_socks(self, other_socks: List["PortRange"]) -> bool:
        for o_sock in other_socks:
            if not self.__match_listening_sock(o_sock):
                return False
        return True

    def __merge_exes(self, other_exes: List[str]):
        for other_exe in other_exes:
            match = False
            if other_exe not in self.exes:
                for exe in self.exes:
                    if fnmatch.fnmatch(other_exe, exe):
                        match = True
                        break
                if not match:
                    self.exes.append(other_exe)

    def __merge_eusers(self, other_eusers: List[str]):
        for other_euser in other_eusers:
            if other_euser not in self.eusers:
                self.eusers.append(other_euser)

    def __contains_socket(self, o_sock: "PortRange"):
        for sock in self.listening_sockets:
            if o_sock in sock:
                return True
        return False

    def __merge_listening_socks(self, other_socks: List["PortRange"]):
        for o_sock in other_socks:
            if not self.__contains_socket(o_sock):
                self.listening_sockets.append(o_sock)


class ProcessNodeList:
    def __init__(
        self, nodes_data: List[Dict], base_node_list: ProcessNodeList = None
    ) -> None:
        self.proc_nodes: Dict[str, ProcessNode] = {}  # id > ProcessNode
        self.proc_name_index: Dict[str, List[str]] = {}
        self.roots: List[ProcessNode] = []
        self.ids = set()
        # Node lists from deviations or suggestions may
        # be treated differently in some cases
        self.dev_or_sug = False
        self.base_node_list = base_node_list
        for node_data in nodes_data:
            root_node = self.__add_node(node_data)
            if len(root_node.eusers) == 0:
                raise m_lib.InvalidMergeError("Root process has no eusers")
            self.roots.append(root_node)

    def get_node(self, node_id: str) -> Optional[ProcessNode]:
        return self.proc_nodes.get(node_id)

    def symmetrical_merge(self, other_list: "ProcessNodeList"):
        for other_node in other_list.roots:
            match = False
            node = None
            for node in self.roots:
                if node.symmetrical_in(other_node) or other_node.symmetrical_in(node):
                    match = True
                    break
            if match:
                node.symmetrical_merge(other_node)
                self.__symmetrical_merge_helper(node, other_node)
            else:
                self.__add_merged_root(other_node)

    def asymmetrical_merge(self, other_list: "ProcessNodeList"):
        for other_node in other_list.roots:
            match = False
            node = None
            for node in self.roots:
                if other_node in node:
                    match = True
                    break
            if match:
                node.asymmetrical_merge(other_node)
                self.__asymmetrical_merge_helper(node, other_node)
            else:
                self.__add_merged_root(other_node)

    def get_data(self) -> List[Dict]:
        rv = []
        for node in self.roots:
            rv.append(node.as_dict())
        return rv

    def __unique_id(self, curr_id: str) -> str:
        if curr_id not in self.ids:
            return curr_id
        new_id = curr_id
        while new_id in self.ids:
            id_parts = new_id.split("_")
            if len(id_parts) > 1 and id_parts[-1].isdigit():
                id_parts[-1] = str(int(id_parts[-1]) + 1)
                new_id = "_".join(id_parts)
            else:
                id_parts.append("0")
                new_id = "_".join(id_parts)
        return new_id

    def __symmetrical_merge_helper(self, node: ProcessNode, other_node: ProcessNode):
        for o_child_id in other_node.children:
            match = False
            o_child_node = other_node.node_list.get_node(o_child_id)
            if not o_child_node:
                raise m_lib.InvalidMergeError("Bug, node list missing ID")
            for child_id in node.children:
                child_node = self.get_node(child_id)
                if not child_node:
                    raise m_lib.InvalidMergeError("Bug, node list missing ID")
                if child_node.symmetrical_in(
                    o_child_node
                ) or o_child_node.symmetrical_in(child_node):
                    match = True
                    break
            if match:
                child_node.symmetrical_merge(o_child_node)
                self.__symmetrical_merge_helper(child_node, o_child_node)
            else:
                self.__add_merged_subtree(o_child_node, node)

    def __asymmetrical_merge_helper(self, node: ProcessNode, other_node: ProcessNode):
        for o_child_id in other_node.children:
            match = False
            o_child_node = other_node.node_list.get_node(o_child_id)
            if not o_child_node:
                raise m_lib.InvalidMergeError("Bug, node list missing ID")
            for child_id in node.children:
                child_node = self.get_node(child_id)
                if not child_node:
                    raise m_lib.InvalidMergeError("Bug, node list missing ID")
                if o_child_node in child_node:
                    match = True
                    break
            if match:
                child_node.asymmetrical_merge(o_child_node)
                self.__asymmetrical_merge_helper(child_node, o_child_node)
            else:
                self.__add_merged_subtree(o_child_node, node)

    def __add_node(self, node_data: Dict, eusers=None, parent=None) -> "ProcessNode":
        if not eusers:
            eusers = []
        if "policyNode" in node_data:
            self.dev_or_sug = True
            node_id = node_data["policyNode"]["id"]
            children = node_data["policyNode"].get(lib.CHILDREN_FIELD)
            if node_id not in self.base_node_list.ids:
                raise m_lib.InvalidMergeError(
                    f"Deviation process node ID ({node_id}) is missing in base"
                    " policy"
                )
            node = self.base_node_list.get_node(node_id)
            node_data = node.node.copy()
            node_data.pop(lib.CHILDREN_FIELD, None)
            if children:
                node_data[lib.CHILDREN_FIELD] = children
            while node.parent:
                parent = self.base_node_list.get_node(node.parent)
                parent_data = parent.node.copy()
                parent_data[lib.CHILDREN_FIELD] = [node_data]
                node_data = parent_data
                node = parent
        proc_node = ProcessNode(self, node_data, eusers, parent)
        self.proc_nodes[proc_node.id] = proc_node
        self.proc_name_index.setdefault(proc_node.name, [])
        self.proc_name_index[proc_node.name].append(proc_node.id)
        if proc_node.id in self.ids:
            if not self.dev_or_sug:
                raise m_lib.InvalidMergeError(
                    f"Duplicate process id detected. ({proc_node.id})"
                )
            # deviations or suggestions can have ids that already exist in
            # the base policy, so we need to generate a new id for the
            # deviation
            new_id = self.__unique_id(proc_node.id)
            proc_node.id = new_id
        self.ids.add(proc_node.id)
        for child_data in node_data.get(lib.CHILDREN_FIELD, []):
            self.__add_node(child_data, proc_node.eusers, proc_node.id)
        return proc_node

    def __add_merged_root(self, other_node: ProcessNode):
        root_node = self.__add_merged_node(other_node, other_node.eusers)
        if len(root_node.eusers) == 0:
            raise m_lib.InvalidMergeError("Root process has no eusers")
        self.roots.append(root_node)

    def __add_merged_subtree(self, other_node: ProcessNode, parent_node: ProcessNode):
        sub_tree_root = self.__add_merged_node(
            other_node, other_node.eusers, parent_node.id
        )
        parent_node.children.append(sub_tree_root.id)

    def __add_merged_node(
        self, other_node: ProcessNode, eusers=None, parent=None
    ) -> ProcessNode:
        if not eusers:
            eusers = []
        proc_node = ProcessNode(self, other_node.node, eusers, parent)
        if proc_node.id in self.ids:
            new_id = self.__unique_id(proc_node.id)
            proc_node.id = new_id
        other_node.merged_id = proc_node.id
        self.proc_nodes[proc_node.id] = proc_node
        self.proc_name_index.setdefault(proc_node.name, [])
        self.proc_name_index[proc_node.name].append(proc_node.id)
        self.ids.add(proc_node.id)
        if lib.CHILDREN_FIELD in proc_node.node:
            new_children_ids = []
            for child_data in proc_node.node.get(lib.CHILDREN_FIELD):
                child_id = child_data[lib.ID_FIELD]
                child_node = other_node.node_list.get_node(child_id)
                if not child_node:
                    raise m_lib.InvalidMergeError("Bug, node list missing ID")
                added_child = self.__add_merged_node(
                    child_node, proc_node.eusers, proc_node.id
                )
                new_children_ids.append(added_child.id)
            proc_node.children = new_children_ids
        return proc_node


class IPBlock:
    def __init__(
        self,
        ip_network: Union[ipaddr.IPv4Network, ipaddr.IPv6Network],
        except_networks: List = None,
    ) -> None:
        self.network = ip_network
        self.except_networks = except_networks
        if except_networks is not None:
            for net in except_networks:
                if not ip_network.supernet_of(net):
                    raise InvalidNetworkNode(
                        "Except block must be completely within cidr network"
                    )

    def as_dict(self) -> Dict:
        ipblock_dict = {lib.CIDR_FIELD: str(self.network)}
        if self.except_networks:
            ipblock_dict[lib.EXCEPT_FIELD] = [str(net) for net in self.except_networks]
        rv = {lib.IP_BLOCK_FIELD: ipblock_dict}
        return rv

    def __contains__(self, other):
        if isinstance(other, IPBlock):
            if self.except_networks is not None:
                for net in self.except_networks:
                    try:
                        if net.supernet_of(other.network):
                            return False
                    except TypeError:
                        # Occurs when comparing ipv4 with ipv6
                        continue
            try:
                if self.network.supernet_of(other.network):
                    return True
            except TypeError:
                return False
        return False

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, IPBlock):
            return False
        return (
            self.network == __o.network and self.except_networks == __o.except_networks
        )


class PortRange:
    def __init__(self, port: int, proto: str, endport: int = None) -> None:
        self.port = port
        self.proto = proto
        self.endport = endport if endport is not None else self.port
        if self.endport < self.port:
            raise InvalidNetworkNode(
                f"The {lib.ENDPORT_FIELD} value must be greater than or equal"
                f" to {lib.PORT_FIELD} value."
            )

    def as_dict(self) -> Dict:
        rv = {lib.PROTO_FIELD: self.proto, lib.PORT_FIELD: self.port}
        if self.endport != self.port:
            rv[lib.ENDPORT_FIELD] = self.endport
        return rv

    def __contains__(self, other):
        if isinstance(other, PortRange):
            if (
                self.port <= other.port <= self.endport
                and self.port <= other.endport <= self.endport
                and self.proto == other.proto
            ):
                return True
        return False


class NetworkNode:
    def __init__(
        self,
        node_list: "NetworkNodeList",
        node_data: Dict,
        proc_node_list: ProcessNodeList,
    ) -> None:
        self.ip_blocks: List[IPBlock] = []
        self.proc_node_list = proc_node_list
        self.dns_names = []
        self.port_ranges: List[PortRange] = []
        self.processes = node_data.get(lib.PROCESSES_FIELD, [])
        self.node_list = node_list
        # Anded blocks are not supported
        self.anded_blocks = []
        if lib.TO_FIELD in node_data:
            self.type = m_lib.NODE_TYPE_EGRESS
            self.__parse_or_blocks(node_data[lib.TO_FIELD])
        elif lib.FROM_FIELD in node_data:
            self.type = m_lib.NODE_TYPE_INGRESS
            self.__parse_or_blocks(node_data[lib.FROM_FIELD])
        else:
            raise InvalidNetworkNode(
                f"Missing {lib.TO_FIELD} or {lib.FROM_FIELD} field."
            )
        self.__parse_port_block(node_data[lib.PORTS_FIELD])

    def symmetrical_merge(
        self,
        other_node: "NetworkNode",
    ):
        self.__merge_ip_blocks(
            other_node.ip_blocks,
            symmetrical=True,
        )
        self.__merge_dns_names(
            other_node.dns_names,
            symmetrical=True,
        )
        self.__merge_process_ids(other_node.processes)

    def asymmetrical_merge(self, other_node: "NetworkNode"):
        self.__merge_ip_blocks(
            other_node.ip_blocks,
            symmetrical=False,
        )
        self.__merge_dns_names(
            other_node.dns_names,
            symmetrical=False,
        )
        self.__merge_process_ids(other_node.processes)

    def internal_merge(self):
        if self.node_list.ignore_procs:
            self.proc_node_list = []
        new_blocks = []
        for i, block in enumerate(self.ip_blocks):
            if any([block in nb for nb in new_blocks]):
                continue
            if self.node_list.ignore_private and block.network.is_private:
                continue
            if self.node_list.ignore_public and not block.network.is_private:
                continue
            next_index = i + 1
            if any([block in ob for ob in self.ip_blocks[next_index:]]):
                continue
            new_blocks.append(block)
        self.ip_blocks = new_blocks
        dns_names = set()
        for dns_name in self.dns_names:
            if self.node_list.ignore_private and lib.is_private_dns(dns_name):
                continue
            if self.node_list.ignore_public and lib.is_public_dns(dns_name):
                continue
            dns_names.add(dns_name)
        self.dns_names = list(dns_names)

    def as_dict(self) -> Optional[Dict]:
        or_field_string = (
            lib.TO_FIELD if self.type == m_lib.NODE_TYPE_EGRESS else lib.FROM_FIELD
        )
        rv = {}
        dns_names = [
            {lib.DNS_SELECTOR_FIELD: [name]} for name in sorted(self.dns_names)
        ]
        ipv4_blocks = [
            b for b in self.ip_blocks if isinstance(b.network, ipaddr.IPv4Network)
        ]
        ipv4_blocks.sort(key=lambda x: x.network)
        ipv4_blocks = [b.as_dict() for b in ipv4_blocks]
        ipv6_blocks = [
            b for b in self.ip_blocks if isinstance(b.network, ipaddr.IPv6Network)
        ]
        ipv6_blocks.sort(key=lambda x: x.network)
        ipv6_blocks = [b.as_dict() for b in ipv6_blocks]
        or_blocks = dns_names + ipv4_blocks + ipv6_blocks
        if not or_blocks:
            return None
        rv[or_field_string] = or_blocks
        if self.processes:
            rv[lib.PROCESSES_FIELD] = self.processes
        rv[lib.PORTS_FIELD] = [p.as_dict() for p in self.port_ranges]
        return rv

    @property
    def converted(self) -> "NetworkNode":
        """Makes a copy of self and updates the process ids of the
        copy to the merged ids if this node has been merged.
        Used in symmetrical merges.

        Returns:
            NetworkNode: a converted copy of this network node
        """
        rv = deepcopy(self)
        if self.node_list.ignore_procs:
            rv.processes = []
        else:
            for i, node_id in enumerate(rv.processes.copy()):
                proc_node = rv.__find_proc_node(node_id, self.proc_node_list)
                if proc_node is None:
                    raise InvalidNetworkNode("Unable to find process node to convert")
                if proc_node.merged_id is not None:
                    rv.processes[i] = proc_node.merged_id
            rv.processes = list(set(rv.processes))
        rv.proc_node_list = self.node_list.base_node_list
        return rv

    def __parse_or_blocks(self, or_blocks: List[Dict]):
        for block in or_blocks:
            if lib.IP_BLOCK_FIELD in block and lib.DNS_SELECTOR_FIELD in block:
                cli.try_log(
                    "Warning: Anded blocks not yet supported. Separate ipBlock"
                    " and dnsSelector into their own list items. Skipping this"
                    " block.."
                )
                continue
            elif lib.IP_BLOCK_FIELD in block:
                ip_block = block[lib.IP_BLOCK_FIELD]
                try:
                    ip_network = ipaddr.IPv4Network(ip_block[lib.CIDR_FIELD])
                    except_block = ip_block.get(lib.EXCEPT_FIELD)
                    except_networks = []
                    if except_block:
                        for except_cidr in except_block:
                            except_net = ipaddr.IPv4Network(except_cidr)
                            except_networks.append(except_net)
                except ipaddr.AddressValueError:
                    try:
                        ip_network = ipaddr.IPv6Network(ip_block[lib.CIDR_FIELD])
                        except_block = ip_block.get(lib.EXCEPT_FIELD)
                        except_networks = []
                        if except_block:
                            for except_cidr in except_block:
                                except_net = ipaddr.IPv6Network(except_cidr)
                                except_networks.append(except_net)
                    except ipaddr.AddressValueError:
                        raise InvalidNetworkNode("Invalid IP block.")
                block = IPBlock(ip_network, except_networks)
                # Prevent duplicates
                if block not in self.ip_blocks:
                    self.ip_blocks.append(block)
            elif lib.DNS_SELECTOR_FIELD in block:
                for dns_name in block[lib.DNS_SELECTOR_FIELD]:
                    self.dns_names.append(dns_name)

    def __parse_port_block(self, port_block: List[Dict]):
        for port in port_block:
            self.port_ranges.append(
                PortRange(
                    port[lib.PORT_FIELD],
                    port[lib.PROTO_FIELD],
                    port.get(lib.ENDPORT_FIELD),
                )
            )

    def __merge_process_ids(self, other_processes: List[str]):
        if self.node_list.ignore_procs:
            self.processes = []
            return
        self.processes.extend(other_processes)
        self.processes = sorted(list(set(self.processes)))

    def __merge_ip_block(
        self,
        other_ip_block: IPBlock,
        symmetrical=False,
    ):
        if symmetrical:
            match = False
            for i, ip_block in enumerate(self.ip_blocks):
                if other_ip_block in ip_block:
                    match = True
                    break
                elif ip_block in other_ip_block:
                    self.ip_blocks[i] = other_ip_block
                    match = True
                    break
            if not match:
                self.ip_blocks.append(other_ip_block)
        else:
            match = False
            for ip_block in self.ip_blocks:
                if other_ip_block in ip_block:
                    match = True
                    break
            if not match:
                self.ip_blocks.append(other_ip_block)

    def __merge_ip_blocks(
        self,
        other_ip_blocks: List[IPBlock],
        symmetrical=False,
    ):
        for o_ip_block in other_ip_blocks:
            if self.node_list.ignore_private and o_ip_block.network.is_private:
                continue
            if self.node_list.ignore_public and not o_ip_block.network.is_private:
                continue
            self.__merge_ip_block(o_ip_block, symmetrical)

    def __merge_dns_name(
        self,
        other_dns_name: str,
        symmetrical=False,
    ):
        if symmetrical:
            match = False
            for i, dns_name in enumerate(self.dns_names):
                if fnmatch.fnmatch(other_dns_name, dns_name):
                    match = True
                    break
                if fnmatch.fnmatch(dns_name, other_dns_name):
                    match = True
                    self.dns_names[i] = other_dns_name
                    break
            if not match:
                self.dns_names.append(other_dns_name)
        else:
            match = False
            for dns_name in self.dns_names:
                if fnmatch.fnmatch(other_dns_name, dns_name):
                    match = True
                    break
            if not match:
                self.dns_names.append(other_dns_name)

    def __merge_dns_names(
        self,
        other_dns_names: List[str],
        symmetrical=False,
    ):
        for o_dns_name in other_dns_names:
            if self.node_list.ignore_private and lib.is_private_dns(o_dns_name):
                continue
            if self.node_list.ignore_public and lib.is_public_dns(o_dns_name):
                continue
            self.__merge_dns_name(o_dns_name, symmetrical)

    def __find_proc_node(
        self, proc_id, node_list: ProcessNodeList
    ) -> Optional[ProcessNode]:
        return node_list.get_node(proc_id)

    def __contains_ip_block(self, other_ip_block: IPBlock) -> bool:
        for ip_block in self.ip_blocks:
            if other_ip_block in ip_block:
                return True
        return False

    def __contains_ip_blocks(self, other_ip_blocks: List[IPBlock]) -> bool:
        for o_ip_block in other_ip_blocks:
            if self.node_list.ignore_private and o_ip_block.network.is_private:
                continue
            if self.node_list.ignore_public and not o_ip_block.network.is_private:
                continue
            if not self.__contains_ip_block(o_ip_block):
                return False
        return True

    def __contains_port_range(self, other_port_range: PortRange) -> bool:
        for port_range in self.port_ranges:
            if other_port_range in port_range:
                return True
        return False

    def __contains_port_ranges(self, other_port_ranges: List[PortRange]) -> bool:
        for o_port_range in other_port_ranges:
            if not self.__contains_port_range(o_port_range):
                return False
        return True

    def __contains_dns_name(self, other_dns_name: str) -> bool:
        for dns_name in self.dns_names:
            if fnmatch.fnmatch(other_dns_name, dns_name):
                return True
        return False

    def __contains_dns_names(self, other_dns_names: List[str]) -> bool:
        for o_dns_name in other_dns_names:
            if self.node_list.ignore_private and lib.is_private_dns(o_dns_name):
                continue
            if self.node_list.ignore_public and lib.is_public_dns(o_dns_name):
                continue
            if not self.__contains_dns_name(o_dns_name):
                return False
        return True

    def __contains_process(
        self, other_process_id: str, other_proc_list: ProcessNodeList
    ) -> bool:
        other_node = self.__find_proc_node(other_process_id, other_proc_list)
        if other_node is None:
            raise InvalidNetworkNode("Unable to find process node")
        # First check if the IDs are a match
        cmp_id = other_node.id
        if other_node.merged_id is not None:
            cmp_id = other_node.merged_id
        if cmp_id in self.processes:
            return True
        # If not a match check that the processes are comparable
        # Here we disregard place in the process tree and we're
        # just looking for processes with the same name and exes
        for node_id in self.processes:
            node = self.proc_node_list.get_node(node_id)
            if other_node in node or node in other_node:
                return True
        return False

    def __contains_processes(
        self, other_processes: List[str], other_proc_list: ProcessNodeList
    ) -> bool:
        if len(self.processes) == 0 or self.node_list.ignore_procs:
            # processes of len 0 means any process
            return True
        for o_process_id in other_processes:
            if not self.__contains_process(o_process_id, other_proc_list):
                return False
        return True

    def __contains__(self, other):
        if isinstance(other, NetworkNode):
            if self.type != other.type:
                return False
            if not self.__contains_port_ranges(other.port_ranges):
                return False
            if len(self.port_ranges) > 1 or len(other.port_ranges) > 1:
                # Assuming stricter conditions when multiple port ranges
                # are involved given that additional ports likely means
                # different services
                if not self.__contains_ip_blocks(other.ip_blocks):
                    return False
                if not self.__contains_dns_names(other.dns_names):
                    return False
            if not self.__contains_processes(other.processes, other.proc_node_list):
                return False
            return True
        return False

    def __eq__(self, other):
        if isinstance(other, NetworkNode):
            if self.type != other.type:
                return False
            if not self.__contains_port_ranges(other.port_ranges):
                return False
            if not self.__contains_ip_blocks(other.ip_blocks):
                return False
            if not self.__contains_dns_names(other.dns_names):
                return False
            if not self.__contains_processes(other.processes, other.proc_node_list):
                return False
            return True
        return False


class NetworkNodeList:
    def __init__(
        self,
        nodes_data: List[Dict],
        proc_node_list: ProcessNodeList,
        base_node_list: ProcessNodeList,
        ignore_private=False,
        ignore_public=False,
        ignore_procs=False,
    ) -> None:
        self.nodes: List[NetworkNode] = []
        self.base_node_list = base_node_list
        self.proc_node_list = proc_node_list
        self.ignore_private = ignore_private
        self.ignore_public = ignore_public
        self.ignore_procs = ignore_procs
        for node_data in nodes_data:
            self.__add_node(node_data)
        if self.nodes:
            self.type = self.nodes[0].type
        else:
            self.type = None

    def symmetrical_merge(
        self,
        other_list: "NetworkNodeList",
    ):
        for other_node in other_list.nodes:
            self.__symmetrical_merge_helper(other_node)

    def asymmetrical_merge(
        self,
        other_list: "NetworkNodeList",
    ):
        for other_node in other_list.nodes:
            self.__asymmetrical_merge_helper(other_node)

    def internal_merge(
        self,
    ):
        if len(self.nodes) <= 1:
            if len(self.nodes) == 1:
                self.nodes[0].internal_merge()
            return
        skip_index = set()
        new_nodes = []
        for i, node in enumerate(self.nodes):
            node.internal_merge()
            if i in skip_index:
                continue
            if i == len(self.nodes) - 1:
                new_nodes.append(self.nodes[i])
                break
            x = i + 1
            new_nodes.append(node)
            for j, other_node in enumerate(self.nodes[x:]):
                if other_node in node or node in other_node:
                    node.symmetrical_merge(other_node)
                    skip_index.add(j + x)
        self.nodes = new_nodes

    def get_data(self) -> List[Dict]:
        rv = []
        for node in self.nodes:
            node_dict = node.as_dict()
            if node_dict:
                rv.append(node_dict)
        return rv

    def __add_node(self, node_data: Dict):
        new_node = NetworkNode(self, node_data, self.proc_node_list)
        self.nodes.append(new_node)

    def __symmetrical_merge_helper(self, other_node: "NetworkNode"):
        match = False
        cvt_other_node = other_node.converted
        for node in list(self.nodes):
            if cvt_other_node in node:
                match = True
                node.symmetrical_merge(cvt_other_node)
                break
            if node in cvt_other_node:
                node.symmetrical_merge(cvt_other_node)
                match = True
        if not match:
            self.nodes.append(cvt_other_node)

    def __asymmetrical_merge_helper(
        self,
        other_node: "NetworkNode",
    ):
        match = False
        cvt_other_node = other_node.converted
        for node in list(self.nodes):
            if cvt_other_node in node:
                match = True
                node.asymmetrical_merge(cvt_other_node)
                break
        if not match:
            self.nodes.append(cvt_other_node)


def merge_proc_policies(
    mo: MergeObject,
    proc_data: List[Dict],
    other_proc_data: List[Dict],
    symmetric: bool,
):
    base_node_list = getattr(mo, "base_node_list", None)
    if mo.disable_procs:
        base_node_list = ProcessNodeList([])
        setattr(mo, "base_node_list", base_node_list)
        setattr(mo, "merging_node_list", ProcessNodeList([], base_node_list))
        return []
    if base_node_list is None:
        base_node_list = ProcessNodeList(proc_data)
        setattr(mo, "base_node_list", base_node_list)
    merging_node_list = ProcessNodeList(other_proc_data, base_node_list)
    setattr(mo, "merging_node_list", merging_node_list)
    result = []
    if symmetric:
        base_node_list.symmetrical_merge(merging_node_list)
    else:
        base_node_list.asymmetrical_merge(merging_node_list)
    result = base_node_list.get_data()
    return result


def merge_ingress_or_egress(
    mo: MergeObject,
    base_data: List[Dict],
    other_data: List[Dict],
    symmetric: bool,
):
    if mo.disable_conns == lib.DISABLE_CONNS_ALL:
        return []
    disable_private = mo.disable_private_conns == lib.DISABLE_CONNS_ALL
    disable_public = mo.disable_public_conns == lib.DISABLE_CONNS_ALL
    disable_procs = mo.disable_procs == lib.DISABLE_PROCS_ALL
    base_node_list = getattr(mo, "base_node_list", None)
    merging_node_list = getattr(mo, "merging_node_list", None)
    net_node_list = NetworkNodeList(
        base_data,
        base_node_list,
        base_node_list,
        disable_private,
        disable_public,
        disable_procs,
    )
    other_node_list = NetworkNodeList(
        other_data,
        merging_node_list,
        base_node_list,
        disable_private,
        disable_public,
        disable_procs,
    )
    direction = net_node_list.type or other_node_list.type
    if not direction:
        return []
    if direction == lib.EGRESS_FIELD:
        if mo.disable_conns == lib.DISABLE_CONNS_EGRESS:
            return []
        if mo.disable_private_conns == lib.DISABLE_CONNS_EGRESS:
            net_node_list.ignore_private = True
            other_node_list.ignore_private = True
        if mo.disable_public_conns == lib.DISABLE_CONNS_EGRESS:
            net_node_list.ignore_public = True
            other_node_list.ignore_public = True
    else:
        if mo.disable_conns == lib.DISABLE_CONNS_INGRESS:
            return []
        if mo.disable_private_conns == lib.DISABLE_CONNS_INGRESS:
            net_node_list.ignore_private = True
            other_node_list.ignore_private = True
        if mo.disable_public_conns == lib.DISABLE_CONNS_INGRESS:
            net_node_list.ignore_public = True
            other_node_list.ignore_public = True
    net_node_list.internal_merge()
    other_node_list.internal_merge()
    if symmetric:
        net_node_list.symmetrical_merge(other_node_list)
    else:
        net_node_list.asymmetrical_merge(other_node_list)
    net_node_list.internal_merge()
    result = net_node_list.get_data()
    return result
