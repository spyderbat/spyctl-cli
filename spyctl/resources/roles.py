"""Library for handling roles."""

from typing import Dict, List

from tabulate import tabulate

import spyctl.spyctl_lib as lib

SUMMARY_HEADERS = [
    "NAME",
    "CREATED_AT",
    "STATUS",
    "AGE",
    "NAMESPACE",
    "CLUSTER",
]


def role_output_summary(
    roles: List[Dict],
) -> str:
    """Output roles in a table format."""
    data = []
    for role in roles:
        data.append(role_summary_data(role))
    rv = tabulate(
        sorted(data, key=lambda x: [x[0], x[3], x[4]]),
        headers=SUMMARY_HEADERS,
        tablefmt="plain",
    )
    return rv


def role_summary_data(role: Dict) -> List[str]:
    """Builds a row of data for a role summary."""
    cluster_name = role["cluster_name"]
    meta = role[lib.METADATA_FIELD]
    name = meta["name"]
    namespace = meta["namespace"]
    k8s_status = role["status"]
    created_at = meta[lib.METADATA_CREATE_TIME]
    rv = [
        name,
        created_at,
        k8s_status,
        lib.calc_age(lib.to_timestamp(meta[lib.METADATA_CREATE_TIME])),
        namespace,
        cluster_name,
    ]
    return rv
