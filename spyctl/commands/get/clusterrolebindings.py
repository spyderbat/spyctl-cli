"""Handles retrieval of clusterrolebindings."""

import click

import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl.api.athena_search import search_athena
from spyctl.commands.get import get_lib


@click.command("clusterrolebindings", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.athena_query_options
@_so.schema_options("model_k8s_clusterrolebinding")


def get_clusterrolebindings_cmd(name_or_id, output, st, et, **filters):
    """Get clusterrolebindings by name or id."""
    exact = filters.pop("exact")
    get_lib.output_time_log(lib.CLUSTERROLE_BINDING_RESOURCE.name_plural, st, et)
    name_or_id = get_lib.wildcard_name_or_id(name_or_id, exact)
    filters = {key: value for key, value in filters.items() if value is not None}
    handle_get_clusterrolebindings(name_or_id, output, st, et, **filters)


def handle_get_clusterrolebindings(name_or_id, output, st, et, **filters):
    """Output clusterrolebindings by name or id."""
    ctx = cfg.get_current_context()
    query = lib.query_builder("model_k8s_clusterrolebinding", name_or_id, **filters)

    crbs = search_athena(
        *ctx.get_api_data(),
        "model_k8s_clusterrolebinding",
        query,
        start_time=st,
        end_time=et,
        desc="Retrieving ClusterRoleBindings",
    )
    get_lib.show_get_data(
        crbs,
        output,
        _r.clusterrolebindings.clusterrolebinding_output_summary,
    )
