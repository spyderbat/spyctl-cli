"""Handles retrieval of replicasets."""

import click

import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl.commands.get import get_lib
from spyctl.api.athena_search import search_athena


@click.command("replicasets", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.athena_query_options
@_so.schema_options("model_k8s_replicaset")
def get_replicasets_cmd(name_or_id, output, st, et, **filters):
    """Get replicasets by name or id."""
    exact = filters.pop("exact")
    get_lib.output_time_log(lib.REPLICASET_RESOURCE.name_plural, st, et)
    name_or_id = get_lib.wildcard_name_or_id(name_or_id, exact)
    filters = {
        key: value for key, value in filters.items() if value is not None
    }
    handle_get_replicasets(name_or_id, output, st, et, **filters)


def handle_get_replicasets(name_or_id, output, st, et, **filters):
    """Output replicasets by name or id."""
    ctx = cfg.get_current_context()
    query = lib.query_builder("model_k8s_replicaset", name_or_id, **filters)
    replicasets = search_athena(
        *ctx.get_api_data(),
        "model_k8s_replicaset",
        query,
        start_time=st,
        end_time=et,
    )
    get_lib.show_get_data(
        replicasets,
        output,
        _r.replicasets.replicaset_output_summary,
    )
