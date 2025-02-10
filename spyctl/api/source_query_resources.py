"""Handles queries for each of the resources retrieved via source query."""

import sys
from typing import Dict, Generator, Optional, Callable

import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.source_queries import retrieve_data

# ----------------------------------------------------------------- #
#                       Source-Based Resources                      #
# ----------------------------------------------------------------- #


def get_connections(
    api_url,
    api_key,
    org_uid,
    muids,
    time,
    pipeline=None,
    limit_mem: bool = True,
    disable_pbar_on_first: bool = False,
) -> Generator[Dict, None, None]:
    try:
        datatype = lib.DATATYPE_SPYDERGRAPH
        schema = lib.MODEL_CONNECTION_PREFIX
        for connection in retrieve_data(
            api_url,
            api_key,
            org_uid,
            muids,
            datatype,
            schema,
            time,
            pipeline=pipeline,
            limit_mem=limit_mem,
            disable_pbar_on_first=disable_pbar_on_first,
        ):
            yield connection
    except KeyboardInterrupt:
        __log_interrupt()


def get_connection_bundles(
    api_url,
    api_key,
    org_uid,
    sources,
    time,
    pipeline=None,
    limit_mem: bool = True,
    disable_pbar_on_first: bool = False,
):
    try:
        if sources and sources[0].startswith("clus:"):
            datatype = lib.DATATYPE_K8S
        else:
            datatype = lib.DATATYPE_SPYDERGRAPH
        schema = lib.MODEL_CONN_BUN_PREFIX
        for conn_bun in retrieve_data(
            api_url,
            api_key,
            org_uid,
            sources,
            datatype,
            schema,
            time,
            pipeline=pipeline,
            limit_mem=limit_mem,
            disable_pbar_on_first=disable_pbar_on_first,
        ):
            yield conn_bun
    except KeyboardInterrupt:
        __log_interrupt()


def get_containers(
    api_url,
    api_key,
    org_uid,
    sources,
    time,
    pipeline=None,
    limit_mem: bool = True,
    disable_pbar_on_first: bool = False,
) -> Generator[Dict, None, None]:
    try:
        if sources and sources[0].startswith("clus"):
            datatype = lib.DATATYPE_K8S
        else:
            datatype = lib.DATATYPE_SPYDERGRAPH
        schema = lib.MODEL_CONTAINER_PREFIX
        for container in retrieve_data(
            api_url,
            api_key,
            org_uid,
            sources,
            datatype,
            schema,
            time,
            raise_notfound=True,
            pipeline=pipeline,
            limit_mem=limit_mem,
            disable_pbar_on_first=disable_pbar_on_first,
        ):
            yield container
    except KeyboardInterrupt:
        __log_interrupt()


def get_daemonsets(
    api_url,
    api_key,
    org_uid,
    clusters,
    time,
    pipeline=None,
    limit_mem: bool = True,
    disable_pbar_on_first: bool = False,
) -> Generator[Dict, None, None]:
    try:
        datatype = lib.DATATYPE_K8S
        schema = lib.MODEL_DAEMONSET_PREFIX
        for daemonset in retrieve_data(
            api_url,
            api_key,
            org_uid,
            clusters,
            datatype,
            schema,
            time,
            pipeline=pipeline,
            raise_notfound=True,
            limit_mem=limit_mem,
            disable_pbar_on_first=disable_pbar_on_first,
        ):
            yield daemonset
    except KeyboardInterrupt:
        __log_interrupt()


def get_deployments(
    api_url,
    api_key,
    org_uid,
    clusters,
    time,
    pipeline=None,
    limit_mem: bool = True,
    disable_pbar_on_first: bool = False,
) -> Generator[Dict, None, None]:
    try:
        datatype = lib.DATATYPE_K8S
        schema = lib.MODEL_DEPLOYMENT_PREFIX
        for deployment in retrieve_data(
            api_url,
            api_key,
            org_uid,
            clusters,
            datatype,
            schema,
            time,
            raise_notfound=True,
            pipeline=pipeline,
            limit_mem=limit_mem,
            disable_pbar_on_first=disable_pbar_on_first,
        ):
            yield deployment
    except KeyboardInterrupt:
        __log_interrupt()


def get_deviations(
    api_url,
    api_key,
    org_uid,
    policy_uids,
    time,
    pipeline=None,
    limit_mem: bool = True,
    disable_pbar=False,
    disable_pbar_on_first: bool = False,
) -> Generator[Dict, None, None]:
    try:
        datatype = lib.DATATYPE_AUDIT
        schema = lib.EVENT_DEVIATION_PREFIX
        url = f"api/v1/org/{org_uid}/analyticspolicy/logs"
        for deviation in retrieve_data(
            api_url,
            api_key,
            org_uid,
            policy_uids,
            datatype,
            schema,
            time,
            url=url,
            raise_notfound=True,
            pipeline=pipeline,
            limit_mem=limit_mem,
            disable_pbar=disable_pbar,
            disable_pbar_on_first=disable_pbar_on_first,
        ):
            yield deviation
    except KeyboardInterrupt:
        __log_interrupt()


def get_fingerprints(
    api_url,
    api_key,
    org_uid,
    sources,
    time,
    fprint_type=None,
    pipeline=None,
    limit_mem: bool = True,
    disable_pbar_on_first: bool = False,
) -> Generator[Dict, None, None]:
    try:
        datatype = lib.DATATYPE_FINGERPRINTS
        if fprint_type:
            schema = (
                f"{lib.MODEL_FINGERPRINT_PREFIX}:"
                f"{lib.MODEL_FINGERPRINT_SUBTYPE_MAP[fprint_type]}"
            )
        else:
            schema = lib.MODEL_FINGERPRINT_PREFIX
        for fingerprint in retrieve_data(
            api_url,
            api_key,
            org_uid,
            sources,
            datatype,
            schema,
            time,
            pipeline=pipeline,
            limit_mem=limit_mem,
            disable_pbar_on_first=disable_pbar_on_first,
        ):
            if fingerprint.get("metadata", {}).get("type") not in {
                lib.POL_TYPE_CONT,
                lib.POL_TYPE_SVC,
            }:
                continue
            yield fingerprint
    except KeyboardInterrupt:
        __log_interrupt()


def get_guardian_fingerprints(
    api_url,
    api_key,
    org_uid,
    sources,
    time,
    fprint_type=None,
    _unique=False,
    limit_mem: bool = True,
    disable_pbar_on_first: bool = False,
    expr=None,
    **filters,
):
    if fprint_type == lib.POL_TYPE_SVC:
        fprint_type = "linux_svc"
    api_data = {
        "org_uid": org_uid,
        "start_time": time[0],
        "end_time": time[1],
        "fingerprint_type": fprint_type,
        "unique": False,
        "expr": expr,
        **filters,
    }
    url = "api/v1/fingerprint/guardian/query"
    try:
        for fingerprint in retrieve_data(
            api_url,
            api_key,
            org_uid,
            sources,
            None,
            None,
            time,
            pipeline=None,
            url=url,
            disable_pbar_on_first=disable_pbar_on_first,
            api_data=api_data,
            limit_mem=limit_mem,
        ):
            yield fingerprint
    except KeyboardInterrupt:
        __log_interrupt()


def get_machines(
    api_url,
    api_key,
    org_uid,
    muids,
    time,
    pipeline=None,
    limit_mem: bool = True,
    disable_pbar_on_first: bool = False,
) -> Generator[Dict, None, None]:
    try:
        datatype = lib.DATATYPE_SPYDERGRAPH
        schema = lib.MODEL_MACHINE_PREFIX
        for machine in retrieve_data(
            api_url,
            api_key,
            org_uid,
            muids,
            datatype,
            schema,
            time,
            pipeline=pipeline,
            limit_mem=limit_mem,
            disable_pbar_on_first=disable_pbar_on_first,
        ):
            yield machine
    except KeyboardInterrupt:
        __log_interrupt()


def get_namespaces(
    api_url,
    api_key,
    org_uid,
    clusters,
    time,
    pipeline=None,
    disable_pbar_on_first: bool = False,
) -> Generator[Dict, None, None]:
    try:
        datatype = lib.DATATYPE_K8S
        schema = lib.MODEL_CLUSTER_PREFIX
        namespaces = list(
            retrieve_data(
                api_url,
                api_key,
                org_uid,
                clusters,
                datatype,
                schema,
                time,
                raise_notfound=True,
                pipeline=pipeline,
                limit_mem=False,
                disable_pbar_on_first=disable_pbar_on_first,
            )
        )
        for namespace in namespaces:
            yield namespace
    except KeyboardInterrupt:
        __log_interrupt()


def get_nodes(
    api_url,
    api_key,
    org_uid,
    clusters,
    time,
    pipeline=None,
    limit_mem: bool = True,
    disable_pbar_on_first: bool = False,
) -> Generator[Dict, None, None]:
    try:
        datatype = lib.DATATYPE_K8S
        schema = lib.MODEL_NODE_PREFIX
        for node in retrieve_data(
            api_url,
            api_key,
            org_uid,
            clusters,
            datatype,
            schema,
            time,
            raise_notfound=True,
            pipeline=pipeline,
            limit_mem=limit_mem,
            disable_pbar_on_first=disable_pbar_on_first,
        ):
            yield node
    except KeyboardInterrupt:
        __log_interrupt()


def get_opsflags(
    api_url,
    api_key,
    org_uid,
    sources,
    time,
    pipeline=None,
    limit_mem: bool = True,
    disable_pbar_on_first: bool = False,
) -> Generator[Dict, None, None]:
    try:
        if sources and sources[0].startswith("clus:"):
            datatype = lib.DATATYPE_K8S
        else:
            datatype = lib.DATATYPE_REDFLAGS
        schema = lib.EVENT_OPSFLAG_PREFIX
        for opsflag in retrieve_data(
            api_url,
            api_key,
            org_uid,
            sources,
            datatype,
            schema,
            time,
            pipeline=pipeline,
            limit_mem=limit_mem,
            disable_pbar_on_first=disable_pbar_on_first,
        ):
            yield opsflag
    except KeyboardInterrupt:
        __log_interrupt()


def get_pods(
    api_url,
    api_key,
    org_uid,
    clusters,
    time,
    pipeline=None,
    limit_mem: bool = True,
    disable_pbar_on_first: bool = False,
) -> Generator[Dict, None, None]:
    try:
        datatype = lib.DATATYPE_K8S
        schema = lib.MODEL_POD_PREFIX
        for pod in retrieve_data(
            api_url,
            api_key,
            org_uid,
            clusters,
            datatype,
            schema,
            time,
            raise_notfound=True,
            pipeline=pipeline,
            limit_mem=limit_mem,
            disable_pbar_on_first=disable_pbar_on_first,
        ):
            yield pod
    except KeyboardInterrupt:
        __log_interrupt()


def get_cluster_full(
    api_url,
    api_key,
    org_uid,
    cluster_sources,
    time,
    pipeline=None,
    limit_mem: bool = True,
    disable_pbar_on_first: bool = False,
    disable_pbar: bool = False,
    last_model: bool = True,
    projection_func: Optional[Callable] = None,
) -> Generator[Dict, None, None]:
    try:
        datatype = lib.DATATYPE_K8S
        schema = None
        for resource in retrieve_data(
            api_url,
            api_key,
            org_uid,
            cluster_sources,
            datatype,
            schema,
            time,
            raise_notfound=True,
            pipeline=pipeline,
            limit_mem=limit_mem,
            disable_pbar_on_first=disable_pbar_on_first,
            disable_pbar=disable_pbar,
            last_model=last_model,
            projection_func=projection_func,
        ):
            yield resource
    except KeyboardInterrupt:
        __log_interrupt()


def get_processes(
    api_url,
    api_key,
    org_uid,
    muids,
    time,
    pipeline=None,
    limit_mem: bool = True,
    disable_pbar_on_first: bool = False,
) -> Generator[Dict, None, None]:
    try:
        datatype = lib.DATATYPE_SPYDERGRAPH
        schema = lib.MODEL_PROCESS_PREFIX
        for process in retrieve_data(
            api_url,
            api_key,
            org_uid,
            muids,
            datatype,
            schema,
            time,
            pipeline=pipeline,
            limit_mem=limit_mem,
            disable_pbar_on_first=disable_pbar_on_first,
        ):
            yield process
    except KeyboardInterrupt:
        __log_interrupt()


def get_replicaset(
    api_url,
    api_key,
    org_uid,
    clusters,
    time,
    pipeline=None,
    limit_mem: bool = True,
    disable_pbar_on_first: bool = False,
) -> Generator[Dict, None, None]:
    try:
        datatype = lib.DATATYPE_K8S
        schema = lib.MODEL_REPLICASET_PREFIX
        for replicaset in retrieve_data(
            api_url,
            api_key,
            org_uid,
            clusters,
            datatype,
            schema,
            time,
            raise_notfound=True,
            pipeline=pipeline,
            limit_mem=limit_mem,
            disable_pbar_on_first=disable_pbar_on_first,
        ):
            yield replicaset
    except KeyboardInterrupt:
        __log_interrupt()


def get_role(
    api_url,
    api_key,
    org_uid,
    clusters,
    time,
    pipeline=None,
    limit_mem: bool = True,
    disable_pbar_on_first: bool = False,
) -> Generator[Dict, None, None]:
    try:
        datatype = lib.DATATYPE_K8S
        schema = lib.MODEL_K8S_ROLE_PREFIX
        for roles in retrieve_data(
            api_url,
            api_key,
            org_uid,
            clusters,
            datatype,
            schema,
            time,
            raise_notfound=True,
            pipeline=pipeline,
            limit_mem=limit_mem,
            disable_pbar_on_first=disable_pbar_on_first,
        ):
            yield roles
    except KeyboardInterrupt:
        __log_interrupt()


def get_clusterrole(
    api_url,
    api_key,
    org_uid,
    clusters,
    time,
    pipeline=None,
    limit_mem: bool = True,
    disable_pbar_on_first: bool = False,
) -> Generator[Dict, None, None]:
    try:
        datatype = lib.DATATYPE_K8S
        schema = lib.MODEL_K8S_ROLE_PREFIX
        for clusterrole in retrieve_data(
            api_url,
            api_key,
            org_uid,
            clusters,
            datatype,
            schema,
            time,
            raise_notfound=True,
            pipeline=pipeline,
            limit_mem=limit_mem,
            disable_pbar_on_first=disable_pbar_on_first,
        ):
            yield clusterrole
    except KeyboardInterrupt:
        __log_interrupt()


def get_rolebinding(
    api_url,
    api_key,
    org_uid,
    clusters,
    time,
    pipeline=None,
    limit_mem: bool = True,
    disable_pbar_on_first: bool = False,
) -> Generator[Dict, None, None]:
    try:
        datatype = lib.DATATYPE_K8S
        schema = lib.MODEL_ROLEBINDING_PREFIX
        for rolebinding in retrieve_data(
            api_url,
            api_key,
            org_uid,
            clusters,
            datatype,
            schema,
            time,
            raise_notfound=True,
            pipeline=pipeline,
            limit_mem=limit_mem,
            disable_pbar_on_first=disable_pbar_on_first,
        ):
            yield rolebinding
    except KeyboardInterrupt:
        __log_interrupt()


def get_clusterrolebinding(
    api_url,
    api_key,
    org_uid,
    clusters,
    time,
    pipeline=None,
    limit_mem: bool = True,
    disable_pbar_on_first: bool = False,
) -> Generator[Dict, None, None]:
    try:
        datatype = lib.DATATYPE_K8S
        schema = lib.MODEL_CLUSTERROLE_BINDING_PREFIX
        for crb in retrieve_data(
            api_url,
            api_key,
            org_uid,
            clusters,
            datatype,
            schema,
            time,
            raise_notfound=True,
            pipeline=pipeline,
            limit_mem=limit_mem,
            disable_pbar_on_first=disable_pbar_on_first,
        ):
            yield crb
    except KeyboardInterrupt:
        __log_interrupt()


def get_redflags(
    api_url,
    api_key,
    org_uid,
    sources,
    time,
    pipeline=None,
    limit_mem: bool = True,
    disable_pbar_on_first: bool = False,
) -> Generator[Dict, None, None]:
    try:
        if sources and sources[0].startswith("clus:"):
            datatype = lib.DATATYPE_K8S
        else:
            datatype = lib.DATATYPE_REDFLAGS
        schema = lib.EVENT_REDFLAG_PREFIX
        for redflag in retrieve_data(
            api_url,
            api_key,
            org_uid,
            sources,
            datatype,
            schema,
            time,
            pipeline=pipeline,
            limit_mem=limit_mem,
            disable_pbar_on_first=disable_pbar_on_first,
        ):
            yield redflag
    except KeyboardInterrupt:
        __log_interrupt()


def get_spydertraces(
    api_url,
    api_key,
    org_uid,
    muids,
    time,
    pipeline=None,
    limit_mem: bool = True,
    disable_pbar_on_first: bool = False,
) -> Generator[Dict, None, None]:
    try:
        datatype = lib.DATATYPE_SPYDERGRAPH
        schema = lib.MODEL_SPYDERTRACE_PREFIX
        for spydertrace in retrieve_data(
            api_url,
            api_key,
            org_uid,
            muids,
            datatype,
            schema,
            time,
            pipeline=pipeline,
            limit_mem=limit_mem,
            disable_pbar_on_first=disable_pbar_on_first,
        ):
            yield spydertrace
    except KeyboardInterrupt:
        __log_interrupt()


def get_top_data(
    api_url,
    api_key,
    org_uid,
    muids,
    time,
    pipeline=None,
    limit_mem: bool = True,
    disable_pbar_on_first: bool = False,
):
    try:
        datatype = lib.DATATYPE_HTOP
        schema = lib.EVENT_TOP_DATA_PREFIX
        for top_data in retrieve_data(
            api_url,
            api_key,
            org_uid,
            muids,
            datatype,
            schema,
            time,
            pipeline=pipeline,
            limit_mem=limit_mem,
            disable_pbar_on_first=disable_pbar_on_first,
        ):
            yield top_data
    except KeyboardInterrupt:
        __log_interrupt()


# ----------------------------------------------------------------- #
#               Policy Workflow Source-Based Resources              #
# ----------------------------------------------------------------- #


def get_trace_summaries(
    api_url,
    api_key,
    org_uid,
    sources,
    time,
    pipeline=None,
    limit_mem: bool = True,
    disable_pbar_on_first: bool = False,
) -> Generator[Dict, None, None]:
    try:
        datatype = lib.DATATYPE_FINGERPRINTS
        schema = f"{lib.MODEL_FINGERPRINT_PREFIX}:{lib.POL_TYPE_TRACE}"
        for fingerprint in retrieve_data(
            api_url,
            api_key,
            org_uid,
            sources,
            datatype,
            schema,
            time,
            pipeline=pipeline,
            limit_mem=limit_mem,
            disable_pbar_on_first=disable_pbar_on_first,
        ):
            yield fingerprint
    except KeyboardInterrupt:
        __log_interrupt()


# ----------------------------------------------------------------- #
#                          Helper Functions                         #
# ----------------------------------------------------------------- #


def __log_interrupt():
    cli.try_log("\nRequest aborted, no partial results.. exiting.")
    sys.exit(0)
