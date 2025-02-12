from dataclasses import dataclass, field
from typing import Dict, Set, Tuple

from tabulate import tabulate

import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.athena_search import search_athena
from spyctl.api.objects import get_objects

MACHINE_FIELDS = {"hostname"}

PROPERTY_MAP = {
    "service_name": "service_name",
    "hostname": "hostname",
    "nodes": "muid",
}


def linux_svc_query(name_or_id: str, **kwargs):

    def make_query_key(key):
        if key == "service_name":
            return "cgroup"
        if key in MACHINE_FIELDS:
            return f"machine.{key}"
        return key

    def make_query_value(key: str, value: str):
        if key == "service_name":
            # cgroup pattern is */system.slice/<service_name>.service
            value = value if value.startswith("*") else f"*{value}"
            value = "*/system.slice/" + value
            value = value if value.endswith(".service") else f"{value}.service"
        return value

    kwargs = {PROPERTY_MAP[k]: v for k, v in kwargs.items() if k in PROPERTY_MAP}
    query = 'cgroup ~= "*/system.slice/*.service"'
    if name_or_id:
        query += f' and cgroup ~= "*{name_or_id.strip("*")}*"'
    for key, value in kwargs.items():
        query_key = make_query_key(key)
        query_value = make_query_value(key, value)
        if isinstance(query_value, dict):
            for qk, qv in query_value.items():
                if "*" in qv:
                    op = "~="
                else:
                    op = "="
                query += f' and {query_key}["{qk}"] {op} "{qv}"'
        else:
            if "*" in query_value:
                op = "~="
            else:
                op = "="
            query += f' and {query_key} {op} "{query_value}"'
    return query


SUMMARY_HEADERS = [
    "SERVICE_NAME",
    "CGROUP",
    "HOSTNAME",
    "LATEST_TIMESTAMP",
]


@dataclass
class LinuxSvc:
    service_name: str
    latest_timestamp: float = 0
    cgroups: Set = field(default_factory=set)
    hostnames: Set = field(default_factory=set)

    def add_proc(self, proc: Dict, machine: Dict):
        self.latest_timestamp = max(self.latest_timestamp, proc["time"])
        self.cgroups.add(proc["cgroup"])
        self.hostnames.add(machine["hostname"])

    def summary_data(self):
        return [
            self.service_name,
            (
                next(iter(self.cgroups))
                if len(self.cgroups) == 1
                else f"Multiple ({len(self.cgroups)})"
            ),
            (
                next(iter(self.hostnames))
                if len(self.hostnames) == 1
                else f"Multiple ({len(self.hostnames)})"
            ),
            lib.epoch_to_zulu(self.latest_timestamp),
        ]

    def as_dict(self):
        rv = {
            "service_name": self.service_name,
            "cgroups": list(self.cgroups),
            "hostnames": list(self.hostnames),
            "latest_timestamp": lib.epoch_to_zulu(self.latest_timestamp),
        }
        return rv


def linux_svc_summary_output(
    ctx: cfg.Context, name_or_id: str, time: Tuple[float, float], **filters
):
    def extract_svc_name_id(proc: Dict) -> str:
        cgroup: str = proc["cgroup"]
        service_name = cgroup.rsplit("/", 1)[-1]
        return service_name

    query = linux_svc_query(name_or_id, **filters)
    procs = search_athena(
        *ctx.get_api_data(),
        "model_process",
        query,
        start_time=time[0],
        end_time=time[1],
        desc="Retrieving Linux Services",
    )
    muids = {proc["muid"] for proc in procs}
    cli.try_log(f"Retrieving {len(muids)} machines...")
    machines = get_objects(*ctx.get_api_data(), list(muids))
    machine_data = {m["id"]: m for m in machines}
    data: Dict[str, LinuxSvc] = {}  # service_name -> LinuxSvc
    for proc in procs:
        service_name = extract_svc_name_id(proc)
        if service_name not in data:
            data[service_name] = LinuxSvc(
                service_name,
                proc["time"],
                {proc["cgroup"]},
                {machine_data[proc["muid"]]["hostname"]},
            )
        else:
            data[service_name].add_proc(proc, machine_data[proc["muid"]])
    rows = [lsv.summary_data() for lsv in data.values()]
    rows.sort(key=lambda x: x[0])
    return tabulate(rows, headers=SUMMARY_HEADERS, tablefmt="plain")


def get_linux_services(
    ctx: cfg.Context, name_or_id: str, time: Tuple[float, float], **filters
):
    def extract_svc_name_id(proc: Dict) -> str:
        cgroup: str = proc["cgroup"]
        service_name = cgroup.rsplit("/", 1)[-1]
        return service_name

    query = linux_svc_query(name_or_id, **filters)
    procs = search_athena(
        *ctx.get_api_data(),
        "model_process",
        query,
        start_time=time[0],
        end_time=time[1],
        desc="Retrieving Linux Services",
    )
    muids = {proc["muid"] for proc in procs}
    cli.try_log(f"Retrieving {len(muids)} machines...")
    machines = get_objects(*ctx.get_api_data(), list(muids))
    machine_data = {m["id"]: m for m in machines}
    data: Dict[str, LinuxSvc] = {}  # service_name -> LinuxSvc
    for proc in procs:
        service_name = extract_svc_name_id(proc)
        if service_name not in data:
            data[service_name] = LinuxSvc(
                service_name,
                proc["time"],
                {proc["cgroup"]},
                {machine_data[proc["muid"]]["hostname"]},
            )
        else:
            data[service_name].add_proc(proc, machine_data[proc["muid"]])
    return [lsv.as_dict() for lsv in data.values()]
