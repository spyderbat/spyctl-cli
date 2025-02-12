"""Contains functions specific to the Bashcmds resource."""

from typing import Dict, List

from tabulate import tabulate

import spyctl.spyctl_lib as lib

SUMMARY_HEADERS = [
    "UID",
    "CMD",
    "EUSER",
    "TIMESTAMP",
    "PROCESS_UID",
]

WIDE_HEADERS = [
    "UID",
    "CMD",
    "EUSER",
    "TIMESTAMP",
    "PROCESS_UID",
    "MACHINE_UID",
    "CWD",
]


PROPERTY_MAP = {
    "cwd": "cwd",
    "euser": "euser",
    "machine_uid": "muid",
    "process_uid": "puid",
}


def bash_cmds_summary_output(bash_cmds: List[Dict], wide: bool) -> str:
    """Generate a summary output of bash commands."""
    if wide:
        headers = WIDE_HEADERS
        data = [make_wide_row(bash_cmd) for bash_cmd in bash_cmds]
    else:
        headers = SUMMARY_HEADERS
        data = [make_row(bash_cmd) for bash_cmd in bash_cmds]
    data.sort(key=lambda x: (x[4], lib.to_timestamp(x[3])), reverse=True)
    return tabulate(data, headers=headers, tablefmt="plain")


def make_row(bash_cmd: Dict) -> List[str]:
    """Make a summary row for a bash command."""
    return [
        bash_cmd["id"],
        bash_cmd["cmd"],
        bash_cmd["euser"],
        lib.epoch_to_zulu(bash_cmd["time"]),
        bash_cmd["puid"],
    ]


def make_wide_row(bash_cmd: Dict) -> List[str]:
    """Make a wide summary row for a bash command."""
    return [
        bash_cmd["id"],
        bash_cmd["cmd"],
        bash_cmd["euser"],
        lib.epoch_to_zulu(bash_cmd["time"]),
        bash_cmd["puid"],
        bash_cmd["muid"],
        bash_cmd["cwd"],
    ]


def bash_cmds_query(name_or_uid: str, **filters) -> Dict:
    """Generate a query for bash commands."""

    def make_query_value(_key, value):
        if isinstance(value, int):
            return value
        return f'"{value}"'

    def find_op(_key, value):
        if isinstance(value, str) and "*" in value:
            return "~="
        return "="

    query = "*"  # Return all bash commands
    query_kv = {
        PROPERTY_MAP[k]: (k, make_query_value(k, v))
        for k, v in filters.items()
        if k in PROPERTY_MAP
    }
    if name_or_uid or query_kv:
        # Reset the query to an empty string
        query = ""
    if name_or_uid:
        query = f'(cmd ~= "{name_or_uid}" OR id ~= "{name_or_uid}")'
    for key, value_tup in query_kv.items():
        filter_key, value = value_tup
        op = find_op(filter_key, value)
        if query:
            query += " AND "
        query += f"{key} {op} {value}"

    return query
