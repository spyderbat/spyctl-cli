from typing import Dict, List

from tabulate import tabulate

import spyctl.spyctl_lib as lib

SUMMARY_HEADERS = [
    "NAME",
    "KIND/ROLE",
    "CREATED_AT",
    "STATUS",
    "AGE",
    "CLUSTER",
]


def clusterrolebinding_output_summary(crbs: List[Dict]) -> str:
    data = []
    for crb in crbs:
        data.append(clusterrolebinding_summary_data(crb))
    rv = tabulate(
        sorted(data, key=lambda x: [x[0], x[4]]),
        headers=SUMMARY_HEADERS,
        tablefmt="plain",
    )
    return rv


def clusterrolebinding_summary_data(crb: Dict) -> List[str]:
    cluster_name = crb["cluster_name"]
    meta = crb[lib.METADATA_FIELD]
    name = meta["name"]
    k8s_status = crb["status"]
    created_at = meta[lib.METADATA_CREATE_TIME]
    if "roleRef" in crb:
        role = crb["roleRef"]["name"]
        kind = crb["roleRef"]["kind"]
        role_name = kind + "/" + role
    rv = [
        name,
        role_name,
        created_at,
        k8s_status,
        lib.calc_age(lib.to_timestamp(meta[lib.METADATA_CREATE_TIME])),
        cluster_name,
    ]
    return rv
