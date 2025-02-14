"""Library for handling node records."""

from typing import Dict, List

from tabulate import tabulate

import spyctl.spyctl_lib as lib

SUMMARY_HEADERS = [
    "NAME",
    "SPYDERBAT_STATUS",
    "AGE",
    "VERSION",
    "CLUSTER",
    "MUID",
]


def nodes_output_summary(
    nodes: List[Dict],
) -> str:
    """Output nodes in a table format."""
    data = []
    for node in nodes:
        data.append(__node_summary_data(node))
    rv = tabulate(
        sorted(data, key=lambda x: [x[4], x[1], x[2], x[0]]),
        headers=SUMMARY_HEADERS,
        tablefmt="plain",
    )
    return rv


def __node_summary_data(node: Dict) -> List[str]:
    k8s_status = node[lib.BE_K8S_STATUS]
    node_info = k8s_status[lib.NODE_INFO_FIELD]
    version = node_info.get(lib.KUBELET_VERSION_FIELD, lib.NOT_AVAILABLE)
    cluster = node.get("cluster_name") or node.get("cluster_uid")
    meta = node[lib.METADATA_FIELD]
    rv = [
        meta[lib.METADATA_NAME_FIELD],
        node["status"],
        lib.calc_age(lib.to_timestamp(meta[lib.METADATA_CREATE_TIME])),
        version,
        cluster,
        node.get("muid", lib.NOT_AVAILABLE),
    ]
    return rv
