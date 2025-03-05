"""Handles the create container-ruleset command"""

import time

import click

import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.schemas_v2 as schemas
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.athena_search import search_full_json

# from typing import List


@click.command(
    "container-ruleset",
    cls=lib.CustomCommand,
    epilog=lib.SUB_EPILOG,
    hidden=True,
)
@click.help_option("-h", "--help", hidden=True)
@click.option(
    "-o",
    "--output",
    default=lib.OUTPUT_DEFAULT,
    type=click.Choice(lib.OUTPUT_CHOICES, case_sensitive=False),
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
@click.option(
    "--include-selectors",
    "include_selectors",
    help="Include all query selectors in generated rules",
    metavar="",
    is_flag=True,
)
def create_container_ruleset(output: str, st: float, et: float, **kwargs):
    """Create a container ruleset."""
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    handle_create_container_ruleset(output, st, et, **kwargs)


def handle_create_container_ruleset(output: str, st: float, et: float, **kwargs):
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
    include_selectors = kwargs.pop("include_selectors", False)
    if output == lib.OUTPUT_DEFAULT:
        output = lib.OUTPUT_YAML
    if not kwargs:
        # No query params, emit empty ruleset
        rs = schemas.RulesetModel(
            **{
                lib.API_FIELD: lib.API_VERSION,
                lib.KIND_FIELD: lib.RULESET_KIND,
                lib.METADATA_FIELD: {
                    lib.METADATA_NAME_FIELD: "",
                    lib.METADATA_TYPE_FIELD: lib.RULESET_TYPE_CONT,
                },
                lib.SPEC_FIELD: {
                    lib.RULES_FIELD: [],
                },
            }
        ).model_dump(by_alias=True, exclude_none=True)
        cli.show(rs, output)
        return
    procs = search_full_json(
        *ctx.get_api_data(),
        schema="model_process",
        query=__proc_conn_query(**kwargs),
        start_time=st,
        end_time=et,
        desc="Retrieving Policy Processes",
    )
    conns = []
    # conns = api.search_athena(
    #     *ctx.get_api_data(),
    #     schema="model_connection",
    #     query=__proc_conn_query(**kwargs),
    #     start_time=st,
    #     end_time=et,
    #     desc="Retrieving Policy Connections",
    # )
    conts = search_full_json(
        *ctx.get_api_data(),
        schema="model_container",
        query=__cont_query(**kwargs),
        start_time=st,
        end_time=et,
        desc="Retrieving Policy Containers",
    )
    rulesets = _r.container_rulesets.create_container_rulesets(
        procs, conns, conts, {"include_selectors": include_selectors}, **kwargs
    )
    if len(rulesets) == 1:
        cli.show(rulesets[0], output=output)
    else:
        policies = {
            lib.API_FIELD: lib.API_VERSION,
            lib.ITEMS_FIELD: rulesets,
        }
        cli.show(policies, output=output)


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
