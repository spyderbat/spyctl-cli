"""Handles retrieval of spydertraces."""

import click

import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl.api.athena_search import search_full_json
from spyctl.commands.get import get_lib


@click.command("spydertraces", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.athena_query_options
@_so.schema_options("model_spydertrace")
@click.option(
    "--include-linkback",
    is_flag=True,
    help="Include linkback to the console to view the trace.",
)
def get_spydertraces_cmd(name_or_id, output, st, et, **filters):
    """Get spydertraces by name or id."""
    exact = filters.pop("exact")
    get_lib.output_time_log(lib.SPYDERTRACE_RESOURCE.name_plural, st, et)
    name_or_id = get_lib.wildcard_name_or_id(name_or_id, exact)
    filters = {
        key: value for key, value in filters.items() if value is not None
    }
    handle_get_spydertraces(name_or_id, output, st, et, **filters)


def handle_get_spydertraces(name_or_id, output, st, et, **filters):
    """Output spydertraces by name or id."""
    ctx = cfg.get_current_context()
    query = lib.query_builder("model_spydertrace", name_or_id, **filters)
    include_linkback = filters.pop("include_linkback", False)
    spydertraces = search_full_json(
        *ctx.get_api_data(),
        "model_spydertrace",
        query,
        start_time=st,
        end_time=et,
        desc="Retrieving Spydertraces",
    )
    get_lib.show_get_data(
        spydertraces,
        output,
        lambda data: _r.spydertraces.spydertraces_stream_summary_output(
            data,
            wide=output == lib.OUTPUT_WIDE,
            include_linkback=include_linkback,
        ),
    )
