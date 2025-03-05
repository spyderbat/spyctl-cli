"""Handles the create container-policy command"""

import time

import click

import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.athena_search import search_full_json


@click.command(
    "container-policy",
    cls=lib.CustomCommand,
    epilog=lib.SUB_EPILOG,
)
@click.help_option("-h", "--help", hidden=True)
@click.option(
    "-o",
    "--output",
    default=lib.OUTPUT_DEFAULT,
    type=click.Choice(lib.OUTPUT_CHOICES, case_sensitive=False),
)
@click.option(
    "-m",
    "--mode",
    type=click.Choice(lib.POL_MODES),
    default=lib.POL_MODE_AUDIT,
    metavar="",
    help="This determines what the policy should do when applied and enabled."
    " Default is audit mode. Audit mode will generate log messages when a"
    " violation occurs and when it would have taken an action, but it will not"
    " actually take an action or generate a violation flag. Enforce mode"
    " will take actions, generate flags, and also generate audit events.",
    hidden=False,
)
@click.option(
    "-t",
    "--start-time",
    "st",
    help="Time to start generating statements from. Default is 1.5 hours ago.",
    default="1.5h",
    metavar="",
    type=lib.time_inp,
)
@click.option(
    "-e",
    "--end-time",
    "et",
    help="Time to stop generating statements from. Default is now.",
    default=time.time(),
    metavar="",
    type=lib.time_inp,
)
@click.option(
    "-P",
    "--pod-name",
    "pod_name",
    help="Name of kubernetes pod.",
    metavar="",
)
@click.option(
    "-D",
    "--deployment-name",
    "deployment",
    help="Name of kubernetes deployment.",
    metavar="",
)
@click.option(
    "-C",
    "--cluster-name",
    "clustername",
    help="Name of kubernetes cluster.",
    metavar="",
)
@click.option(
    "-N",
    "--namespace",
    "pod_namespace",
    help="Name of kubernetes namespace.",
    metavar="",
)
@click.option(
    "-I",
    "--image",
    help="Name of container image.",
    metavar="",
)
@click.option(
    "--hostname",
    help="Hostname of container's machine.",
    metavar="",
)
@click.option(
    "--machine-uid",
    "muid",
    help="Unique id of container's machine.",
    metavar="",
)
@click.option(
    "--image-id",
    "image_id",
    help="Id of container image.",
    metavar="",
)
@click.option(
    "--container-id",
    "container_id",
    help="Id of container.",
    metavar="",
)
@click.option(
    "--container-name",
    help="Name of container.",
    metavar="",
)
@click.option(
    "--pod-labels",
    help="Labels of kubernetes pod.",
    metavar="",
    type=lib.DictParam(),
)
@click.option(
    "--namespace-labels",
    "pod_namespace_labels",
    help="Labels of kubernetes namespace.",
    metavar="",
    type=lib.DictParam(),
)
def create_container_policy(output: str, st: float, et: float, **kwargs):
    """Create container policies.

    This command retrieves container processes and connections
    to build a policy that can enforce container workload
    behavior. The options of this command help build the query
    that retrieves the processes and connections.
    A policy will be created for each unique container image within
    the scope of the query.

    Query results are limited to 10,000 objects so be sure to use
    the options to narrow the query as much as possible. Viable
    policies may be created with limited results, but will likely
    take longer to settle during the audit period.
    """
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    handle_create_container_policy(output, st, et, **kwargs)


CONTAINER_FIELDS = {
    "image",
    "image_id",
    "container_id",
    "container_name",
    "pod_name",
    "pod_labels",
    "pod_namespace",
    "clustername",
    "pod_namespace_labels",
}

MACHINE_FIELDS = {"hostname"}


def handle_create_container_policy(output: str, st: float, et: float, **kwargs):
    """
    Handle the creation of a container policy.

    Args:
        output (str): The output format.
        st (float): The start time.
        et (float): The end time.
        **kwargs: Additional keyword arguments.

    Returns:
        None
    """
    ctx = cfg.get_current_context()
    mode = kwargs.pop("mode")
    procs = search_full_json(
        *ctx.get_api_data(),
        schema="model_process",
        query=__proc_conn_query(**kwargs),
        start_time=st,
        end_time=et,
        desc="Retrieving Policy Processes",
    )
    conns = []
    conns = search_full_json(
        *ctx.get_api_data(),
        schema="model_connection",
        query=__proc_conn_query(**kwargs),
        start_time=st,
        end_time=et,
        desc="Retrieving Policy Connections",
    )
    conts = search_full_json(
        *ctx.get_api_data(),
        schema="model_container",
        query=__cont_query(**kwargs),
        start_time=st,
        end_time=et,
        desc="Retrieving Policy Containers",
    )
    policies = _r.container_policies.create_container_policies(
        procs, conns, conts, mode, **kwargs
    )
    if output == lib.OUTPUT_DEFAULT:
        output = lib.OUTPUT_YAML
    if len(policies) == 1:
        cli.show(policies[0], output=output)
    else:
        policies = {
            lib.API_FIELD: lib.API_VERSION,
            lib.ITEMS_FIELD: policies,
        }
        cli.show(policies, output=output)


def __proc_conn_query(**kwargs):
    def make_query_key(key):
        if key == "deployment":
            return "container.pod_name"
        if key in CONTAINER_FIELDS:
            return f"container.{key}"
        if key in MACHINE_FIELDS:
            return f"machine.{key}"
        return key

    def make_query_value(key: str, value: str):
        if key == "deployment":
            return value if value.endswith("*") else f"{value}*"
        return value

    query = 'id ~= "*"'
    for key, value in kwargs.items():
        query_key = make_query_key(key)
        query_value = make_query_value(key, value)
        if isinstance(query_value, dict):
            for qk, qv in query_value.items():
                if "*" in qv:
                    op = "~="
                else:
                    op = "="
                query += f' and {query_key}["{qk}"] {op} "{qv}"'
        else:
            if "*" in query_value:
                op = "~="
            else:
                op = "="
            query += f' and {query_key} {op} "{query_value}"'
    return query


def __cont_query(**kwargs):
    def make_query_key(key):
        if key == "deployment":
            return "pod_name"
        if key in MACHINE_FIELDS:
            return f"machine.{key}"
        return key

    def make_query_value(key: str, value: str):
        if key == "deployment":
            return value if value.endswith("*") else f"{value}*"
        return value

    query = 'id ~= "*"'
    for key, value in kwargs.items():
        query_key = make_query_key(key)
        query_value = make_query_value(key, value)
        if isinstance(query_value, dict):
            for qk, qv in query_value.items():
                if "*" in qv:
                    op = "~="
                else:
                    op = "="
                query += f' and {query_key}["{qk}"] {op} "{qv}"'
        else:
            if "*" in query_value:
                op = "~="
            else:
                op = "="
            query += f' and {query_key} {op} "{query_value}"'
    return query
