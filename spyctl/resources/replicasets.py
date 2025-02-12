from typing import Dict, List, Tuple

from tabulate import tabulate

import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
from spyctl.api.source_query_resources import get_replicaset

SUMMARY_HEADERS = [
    "NAME",
    "D/C/R",
    "AVAILABLE",
    "LAST_STATUS_SEEN",
    "LAST_SEEN",
    "AGE",
    "NAMESPACE",
    "CLUSTER",
]


def replicaset_output_summary(
    ctx: cfg.Context,
    clusters: List[str],
    time: Tuple[float, float],
    pipeline=None,
    limit_mem=False,
) -> str:
    data = []
    for replicaset in get_replicaset(
        *ctx.get_api_data(), clusters, time, pipeline, limit_mem
    ):
        data.append(replicaset_summary_data(replicaset))
    rv = tabulate(
        sorted(data, key=lambda x: [x[2], x[5]]),
        headers=SUMMARY_HEADERS,
        tablefmt="plain",
    )
    print("\nD/C/R = desired/current/ready pod replicas\n")
    return rv


def replicaset_summary_data(replicaset: Dict) -> List[str]:
    last_status_seen = replicaset["status"]
    cluster_name = replicaset["cluster_name"]
    meta = replicaset[lib.METADATA_FIELD]
    name = meta["name"]
    namespace = meta["namespace"]
    k8s_status = replicaset[lib.BE_K8S_STATUS]
    desired = k8s_status["replicas"]
    if "availableReplicas" in k8s_status:
        current = k8s_status["availableReplicas"]
        available = k8s_status["availableReplicas"]
    else:
        current = 0
        available = 0
    if "readyReplicas" in k8s_status:
        ready = k8s_status["readyReplicas"]
    else:
        ready = 0
    age = lib.calc_age(lib.to_timestamp(meta[lib.METADATA_CREATE_TIME]))
    d_c_r = f"{desired}/{current}/{ready}"
    rv = [
        name,
        d_c_r,
        available,
        last_status_seen,
        lib.epoch_to_zulu(replicaset["time"]),
        age,
        namespace,
        cluster_name,
    ]
    return rv
