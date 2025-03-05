"""Handles retrieval of deployments."""

import click

import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl.api.athena_search import search_full_json
from spyctl.commands.get import get_lib


@click.command("deployments", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.athena_query_options
@_so.schema_options("model_k8s_deployment")
def get_deployments_cmd(name_or_id, output, st, et, **filters):
    """Get deployments by name or id."""
    exact = filters.pop("exact")
    get_lib.output_time_log(lib.DEPLOYMENTS_RESOURCE.name_plural, st, et)
    name_or_id = get_lib.wildcard_name_or_id(name_or_id, exact)
    filters = {key: value for key, value in filters.items() if value is not None}
    handle_get_deployments(name_or_id, output, st, et, **filters)


def handle_get_deployments(name_or_id, output, st, et, **filters):
    """Output deployments by name or id."""
    ctx = cfg.get_current_context()
    query = lib.query_builder("model_k8s_deployment", name_or_id, **filters)
    deployments = search_full_json(
        *ctx.get_api_data(),
        "model_k8s_deployment",
        query,
        start_time=st,
        end_time=et,
    )
    get_lib.show_get_data(
        deployments,
        output,
        _r.deployments.deployments_stream_summary_output,
    )
