"""Library for handling rolebindings."""

from typing import Dict, List

from tabulate import tabulate

import spyctl.spyctl_lib as lib

SUMMARY_HEADERS = [
    "NAME",
    "KIND/ROLE",
    "CREATED_AT",
    "STATUS",
    "AGE",
    "NAMESPACE",
    "CLUSTER",
]


def rolebinding_output_summary(
    rolebindings: List[Dict],
) -> str:
    """Output rolebindings in a table format."""
    data = []
    for rolebinding in rolebindings:
        data.append(rolebinding_summary_data(rolebinding))
    rv = tabulate(
        sorted(data, key=lambda x: [x[0], x[4], x[5]]),
        headers=SUMMARY_HEADERS,
        tablefmt="plain",
    )
    return rv


def rolebinding_summary_data(rolebinding: Dict) -> List[str]:
    """Builds a row of data for a rolebinding summary."""
    cluster_name = rolebinding["cluster_name"]
    meta = rolebinding[lib.METADATA_FIELD]
    name = meta["name"]
    namespace = meta["namespace"]
    k8s_status = rolebinding["status"]
    created_at = meta[lib.METADATA_CREATE_TIME]
    role_name = ""
    if "roleRef" in rolebinding:
        crb_role = rolebinding["roleRef"]["name"]
        kind = rolebinding["roleRef"]["kind"]
        role_name = kind + "/" + crb_role
    rv = [
        name,
        role_name,
        created_at,
        k8s_status,
        lib.calc_age(lib.to_timestamp(meta[lib.METADATA_CREATE_TIME])),
        namespace,
        cluster_name,
    ]
    return rv
