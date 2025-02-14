from typing import Dict, List

from tabulate import tabulate

import spyctl.spyctl_lib as lib

SUMMARY_HEADERS = ["NAME", "LAST_SEEN_STATUS", "AGE", "CLUSTER"]


def namespace_summary_output(
    namespaces: List[Dict],
) -> str:
    """Output namespaces in a table format."""
    data = []
    for namespace in namespaces:
        data.append(__namespace_data(namespace))
    data.sort(key=lambda x: (x[3], x[0]))
    return tabulate(
        data,
        headers=SUMMARY_HEADERS,
        tablefmt="plain",
    )


def __namespace_data(namespace: Dict) -> List:
    meta = namespace[lib.METADATA_FIELD]
    rv = [
        meta[lib.METADATA_NAME_FIELD],
        "Active",
        lib.calc_age(lib.to_timestamp(meta[lib.METADATA_CREATE_TIME])),
        namespace["cluster_name"] or namespace["cluster_uid"],
    ]
    return rv
