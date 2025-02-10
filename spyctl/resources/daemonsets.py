from typing import Dict, List, Tuple

from tabulate import tabulate

import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
from spyctl.api.source_query_resources import get_daemonsets

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


def daemonsets_output_summary(
    ctx: cfg.Context,
    clusters: List[str],
    time: Tuple[float, float],
    pipeline=None,
    limit_mem=False,
) -> str:
    data = []
    for daemonset in get_daemonsets(
        *ctx.get_api_data(), clusters, time, pipeline, limit_mem
    ):
        data.append(daemonsets_summary_data(daemonset))
    rv = tabulate(
        sorted(data, key=lambda x: [x[5]]),
        headers=SUMMARY_HEADERS,
        tablefmt="plain",
    )
    print("\nD/C/R = desired/current/ready pod replicas\n")
    return rv


def daemonsets_summary_data(daemonset: Dict) -> List[str]:
    meta = daemonset[lib.METADATA_FIELD]
    name = meta["name"]
    namespace = meta["namespace"]
    k8s_status = daemonset[lib.BE_K8S_STATUS]
    desired = k8s_status["desiredNumberScheduled"]
    current = k8s_status["currentNumberScheduled"]
    ready = k8s_status["numberReady"]
    last_status_seen = daemonset["status"]
    if "numberAvailable" in k8s_status:
        available = k8s_status["numberAvailable"]
    else:
        available = 0
    cluster_name = daemonset["cluster_name"]
    age = lib.calc_age(lib.to_timestamp(meta[lib.METADATA_CREATE_TIME]))
    d_c_r = f"{desired}/{current}/{ready}"
    rv = [
        name,
        d_c_r,
        available,
        last_status_seen,
        lib.epoch_to_zulu(daemonset["time"]),
        age,
        namespace,
        cluster_name,
    ]
    return rv
