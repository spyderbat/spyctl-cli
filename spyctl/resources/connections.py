import ipaddress
from typing import Dict, List, Tuple

import zulu
from tabulate import tabulate

import spyctl.spyctl_lib as lib

NOT_AVAILABLE = lib.NOT_AVAILABLE


WIDE_HEADERS = [
    "START_TIME",
    "FIRST_UID",
    "DURATION",
    "STATUS",
    "DIRECTION",
    "TYPE",
    "PROCESS_NAME",
    "LOCAL_IP",
    "LOCAL_PORT",
    "REMOTE_IP",
    "REMOTE_PORT",
    "PROCESS_NAME",
    "COUNT",
]

SUMMARY_HEADERS = [
    "START_TIME",
    "FIRST_UID",
    "DURATION",
    "STATUS",
    "DIRECTION",
    "TYPE",
    "PROCESS_NAME",
    "COUNT",
]


class ConnectionGroup:
    def __init__(self) -> None:
        self.ref_conn = None
        self.latest_timestamp = NOT_AVAILABLE
        self.count = 0
        self.ip = None

    def add_conn(self, conn: Dict):
        self.__update_latest_timestamp(conn.get("time"))
        if self.ref_conn is None:
            self.ref_conn = conn
        self.count += 1
        ip = ipaddress.ip_address(conn["remote_ip"])
        if self.ip is None:
            self.ip = ip.exploded
        else:
            self.ip = _loose_abbrev_ips(self.ip, ip.exploded)

    def __update_latest_timestamp(self, timestamp):
        if timestamp is None:
            return
        if self.latest_timestamp == NOT_AVAILABLE:
            self.latest_timestamp = timestamp
        elif timestamp > self.latest_timestamp:
            self.latest_timestamp = timestamp

    def as_wide_row(self) -> List:
        timestamp = lib.epoch_to_zulu(self.latest_timestamp)
        duration = lib.convert_to_duration(self.ref_conn["duration"])
        rv = [
            timestamp,
            self.ref_conn["id"],
            duration,
            self.ref_conn["status"],
            self.ref_conn["direction"],
            self.ref_conn["proto"],
            self.ref_conn["proc_name"],
            self.ref_conn["local_ip"],
            self.ref_conn["local_port"],
            self.ref_conn["remote_ip"],
            self.ref_conn["remote_port"],
            self.ref_conn["proc_name"],
            self.count,
        ]
        return rv

    def summary_data(self, ignore_ips) -> List[str]:
        timestamp = NOT_AVAILABLE
        if self.latest_timestamp != NOT_AVAILABLE:
            timestamp = str(
                zulu.Zulu.fromtimestamp(self.latest_timestamp).format(
                    "YYYY-MM-ddTHH:mm:ss"
                )
            )
        duration = lib.convert_to_duration(self.ref_conn["duration"])
        rv = [
            timestamp,
            self.ref_conn["id"],
            duration,
            self.ref_conn["status"],
            self.ref_conn["direction"],
            self.ref_conn["proto"],
            self.ref_conn["proc_name"],
            str(self.count),
        ]
        if ignore_ips:
            rv = rv[1:]
        return rv


def _loose_abbrev_ips(ip1, ip2):
    if ip1 == ip2:
        return ip1
    ret = ""
    for char1, char2 in zip(ip1, ip2, strict=False):
        if char1 == char2:
            ret += char1
        else:
            ret += "*"
            return ret
    return ret + "*"


def _shorten_v6(ip):
    if ":" not in ip:
        return ip
    ip = ip.replace("0000", "zero")
    i = 0
    pos = -1
    most = 0
    last = 0
    num = 0
    while i < len(ip):
        if ip[i : i + 4] == "zero":
            if num == 0:
                last = i
            num += 1
            if num > most:
                most = num
                pos = last
        else:
            num = 0
        i += 5
    len_diff = 39 - len(ip)
    if ip.endswith("*"):
        len_diff += 1
    if pos != -1:
        ip = ip[:pos] + ":" + ip[pos + most * 5 :]
        if pos == 0:
            ip = ":" + ip
    ip = ip.replace("0", "")
    ip = ip.replace("zero", "0")
    if len_diff > 0:
        ip += f" (+{len_diff})"
    return ip


def connections_output(conns: List[Dict]) -> Dict:
    if len(conns) == 1:
        return conns[0]
    elif len(conns) > 1:
        return {
            lib.API_FIELD: lib.API_VERSION,
            lib.ITEMS_FIELD: conns,
        }
    else:
        return {}


def connection_stream_output_summary(
    connections: List[Dict],
    wide: bool,
    ignore_ips: bool,
) -> str:
    def make_key(conn: Dict) -> Tuple:
        """Generate a unique key based on connection attributes."""
        return _key(conn, ignore_ips)

    groups: Dict[Tuple, ConnectionGroup] = {}
    for conn in connections:
        key = make_key(conn)
        if key not in groups:
            groups[key] = ConnectionGroup()
        groups[key].add_conn(conn)

    data = []
    for group in groups.values():
        data.append(group.summary_data(ignore_ips))

    headers = SUMMARY_HEADERS

    rv = []
    if wide:
        headers = WIDE_HEADERS
        data = [row.as_wide_row() for row in groups.values()]
    else:
        headers = SUMMARY_HEADERS
        data = [group.summary_data(ignore_ips) for group in groups.values()]

    sorted_data = sorted(data, key=lambda x: [x[0]], reverse=True)

    rv.append(
        tabulate(
            sorted_data,
            headers=headers,
            tablefmt="plain",
        )
    )
    return "\n".join(rv)


def _key(connection: Dict, ignore_ips):
    if ignore_ips:
        return (
            connection["direction"],
            connection["proc_name"],
        )
    ip = ipaddress.ip_address(connection["remote_ip"])
    ip_str = ip.exploded
    found = 0
    for i, char in enumerate(ip_str):
        if not char.isdigit():
            found += 1
            if found == 2:
                ip_str = ip_str[: i + 1]
                break
    return (
        ip.version,
        ip_str,
        connection["direction"],
        connection["proc_name"],
    )
