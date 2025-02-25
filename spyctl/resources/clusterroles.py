from typing import Dict, List

from tabulate import tabulate

import spyctl.spyctl_lib as lib

SUMMARY_HEADERS = ["NAME", "CREATED_AT", "STATUS", "AGE", "CLUSTER"]


def clusterrole_output_summary(
    clusterroles: List[dict],
) -> str:
    data = []
    for clusterrole in clusterroles:
        data.append(clusterrole_summary_data(clusterrole))
    rv = tabulate(
        sorted(data, key=lambda x: [x[0], x[3]]),
        headers=SUMMARY_HEADERS,
        tablefmt="plain",
    )
    return rv


def clusterrole_summary_data(clusterrole: Dict) -> List[str]:
    cluster_name = clusterrole["cluster_name"]
    meta = clusterrole[lib.METADATA_FIELD]
    name = meta["name"]
    k8s_status = clusterrole["status"]
    created_at = meta[lib.METADATA_CREATE_TIME]
    rv = [
        name,
        created_at,
        k8s_status,
        lib.calc_age(lib.to_timestamp(meta[lib.METADATA_CREATE_TIME])),
        cluster_name,
    ]
    return rv
