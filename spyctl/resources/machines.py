"""A library for handling machine records."""

from typing import Dict, List

from tabulate import tabulate

import spyctl.spyctl_lib as lib

SUMMARY_HEADERS = ["HOSTNAME", "UID", "OS", "CLOUD_TYPE", "AGE", "CLUSTER"]


def machines_summary_output(machines: List[Dict]) -> str:
    """Output a summary of machines."""
    data = []
    for machine in machines:
        data.append(__machine_summary_data(machine))
    data.sort(key=lambda x: [x[0], lib.to_timestamp(x[3])])
    return tabulate(data, SUMMARY_HEADERS, tablefmt="plain")


def __machine_summary_data(machine: Dict):
    cloud_type = machine.get("cloud_type")
    if not cloud_type:
        cloud_type = lib.NOT_AVAILABLE
    cluster = machine.get("cluster_name")
    if not cluster:
        cluster = lib.NOT_AVAILABLE
    rv = [
        machine[lib.HOSTNAME_FIELD],
        machine[lib.ID_FIELD],
        machine["os_version"],
        cloud_type,
        lib.calc_age(machine["boot_time"]),
        cluster,
    ]
    return rv
