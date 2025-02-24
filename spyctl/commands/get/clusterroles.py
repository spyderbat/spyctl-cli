"""Handles retrieval of clusterroles."""

import click

import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl.api.athena_search import search_athena
from spyctl.commands.get import get_lib


@click.command("clusterroles", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.athena_query_options
@_so.schema_options("model_k8s_clusterrole")


def get_clusterroles_cmd(name_or_id, output, st, et, **filters):
    """Get clusterroles by name or id."""
    exact = filters.pop("exact")
    get_lib.output_time_log(lib.CLUSTERROLES_RESOURCE.name_plural, st, et)
    name_or_id = get_lib.wildcard_name_or_id(name_or_id, exact)
    filters = {key: value for key, value in filters.items() if value is not None}
    handle_get_clusterroles(name_or_id, output, st, et, **filters)


def handle_get_clusterroles(name_or_id, output, st, et, **filters):
    """Output clusterroles by name or id."""
    ctx = cfg.get_current_context()
    query = lib.query_builder("model_k8s_clusterrole", name_or_id, **filters)

    cluster_roles = search_athena(
        *ctx.get_api_data(),
        "model_k8s_clusterrole",
        query,
        start_time=st,
        end_time=et,
        desc="Retrieving ClusterRole",
    )
    get_lib.show_get_data(
        cluster_roles,
        output,
        _r.clusterroles.clusterrole_output_summary,
    )
