from typing import Dict, List, Tuple

import zulu
from tabulate import tabulate

import spyctl.spyctl_lib as lib

NOT_AVAILABLE = lib.NOT_AVAILABLE
SUMMARY_HEADERS = [
    "NAME",
    "FIRST_UID",
    "EXE",
    "DURATION",
    "STATUS",
    "ROOT_EXECUTION",
    "PID",
    "LATEST_EXECUTED",
    "COUNT",
]


class ProcessGroup:
    def __init__(self, multiple_exes) -> None:
        self.ref_proc = None
        self.latest_timestamp = NOT_AVAILABLE
        self.count = 0
        self.root = False
        self.duration = 0
        self.status = " "
        self.multiple_exes = multiple_exes

    def add_proc(self, proc: Dict):
        self.__update_latest_timestamp(proc.get("create_time"))
        if self.ref_proc is None:
            self.ref_proc = proc
        if proc.get("euid") == 0:
            self.root = True
        self.count += 1

    def __update_latest_timestamp(self, timestamp):
        if timestamp is None:
            return
        if self.latest_timestamp == NOT_AVAILABLE:
            self.latest_timestamp = timestamp
        elif timestamp > self.latest_timestamp:
            self.latest_timestamp = timestamp

    def summary_data(self) -> List[str]:
        timestamp = NOT_AVAILABLE
        if self.latest_timestamp != NOT_AVAILABLE:
            timestamp = str(
                zulu.Zulu.fromtimestamp(self.latest_timestamp).format(
                    "YYYY-MM-ddTHH:mm:ss"
                )
            )
        exe = "MULTIPLE" if self.multiple_exes else self.ref_proc["exe"]
        duration = lib.convert_to_duration(self.ref_proc["duration"])
        status = self.ref_proc["status"]
        pid = self.ref_proc["pid"]
        rv = [
            self.ref_proc["name"],
            self.ref_proc["id"],
            exe,
            duration,
            status,
            "YES" if self.root else "NO",
            pid,
            timestamp,
            str(self.count),
        ]
        return rv


PROPERTY_MAP = {
    "uid": "uid",
    "machine_uid": "muid",
    "pid_equals": "pid",
    "pid_above": "pid",
    "pid_below": "pid",
    "ppuid": "ppuid",
}


def processes_query(name_or_uid: str, **filters) -> Dict:
    def make_query_value(key, value):
        if isinstance(value, int) or (
            isinstance(value, str) and value.isdigit()
        ):
            return int(value)

        return f'"{value}"'

    def find_op(key, value):
        if key == "pid_equals":
            return "="
        if key == "pid_above":
            return ">="
        if key == "pid_below":
            return "<="
        if isinstance(value, str) and "*" in value:
            return "~="
        return "="

    query = ""

    query_kv = {
        PROPERTY_MAP[k]: (k, make_query_value(k, v))
        for k, v in filters.items()
        if k in PROPERTY_MAP
    }

    if name_or_uid:
        if query:  # Only add 'AND' if there is already content in the query
            query += " AND "
        if name_or_uid.__contains__("proc:"):
            query += f'(id ~= "{name_or_uid}")'
        else:
            query += f'(name ~= "{name_or_uid}")'

    for key, value_tup in query_kv.items():
        filter_key, value = value_tup
        if not query:
            query = f"{key} {find_op(filter_key, value)} {value}"
        else:
            query += f" AND {key} {find_op(filter_key, value)} {value}"
    if len(query) == 0:
        query = "*"
    return query


def processes_stream_output_summary(
    processes: List[Dict],
    wide: bool,
) -> str:
    # Grouping processes
    groups: Dict[Tuple, ProcessGroup] = {}
    for proc in processes:
        key = _key(proc)
        if key not in groups:
            groups[key] = ProcessGroup(multiple_exes=False)
        groups[key].add_proc(proc)

    data = []
    for group in groups.values():
        data.append(group.summary_data())

    sorted_data = sorted(
        data,
        key=lambda x: [x[0], x[2], lib.to_timestamp(x[4])],
    )

    headers = SUMMARY_HEADERS

    rv = []
    rv.append(
        tabulate(
            sorted_data,
            headers=headers,
            tablefmt="plain",
        )
    )
    return "\n".join(rv)


def _key(process: Dict) -> Tuple:
    name = process["name"]
    exe = process["exe"]
    if exe.endswith(name):
        return False, (name, exe)
    return True, name
