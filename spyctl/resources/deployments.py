from typing import Dict, List

from tabulate import tabulate

import spyctl.spyctl_lib as lib

SUMMARY_HEADERS = [
    "NAME",
    "READY",
    "UP-TO-DATE",
    "AVAILABLE",
    "AGE",
    "NAMESPACE",
    "CLUSTER",
]


def deployment_summary_data(deployment: Dict) -> List:
    k8s_status = deployment[lib.BE_K8S_STATUS]
    replicas = k8s_status.get(lib.REPLICAS_FIELD, "0")
    available_replicas = k8s_status.get(lib.AVAILABLE_REPLICAS_FIELD, "0")
    ready_replicas = k8s_status.get(lib.READY_REPLICAS_FIELD, "0")
    updated_replicas = k8s_status.get(lib.UPDATED_REPLICAS_FIELD, "0")
    meta = deployment[lib.METADATA_FIELD]
    rv = [
        meta["name"],
        f"{ready_replicas}/{replicas}",
        f"{updated_replicas}",
        f"{available_replicas}",
        lib.calc_age(lib.to_timestamp(meta[lib.METADATA_CREATE_TIME])),
        meta[lib.NAMESPACE_FIELD],
        deployment["cluster_name"] or deployment["cluster_uid"],
    ]
    return rv


def deployments_stream_summary_output(
    deployments: List[Dict],
) -> str:
    data = []
    for deployment in deployments:
        data.append(deployment_summary_data(deployment))
    rv = tabulate(
        sorted(data, key=lambda x: [x[6], x[0]]),
        headers=SUMMARY_HEADERS,
        tablefmt="plain",
    )
    return rv
