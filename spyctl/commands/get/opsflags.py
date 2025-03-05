"""Handles retrieval of opsflags."""

import click

import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl.api.athena_search import search_full_json
from spyctl.commands.get import get_lib


@click.command("opsflags", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.athena_query_options
@_so.schema_options("event_opsflag")
def get_opsflags_cmd(name_or_id, output, st, et, **filters):
    """Get opsflags by name or id."""
    exact = filters.pop("exact")
    get_lib.output_time_log(lib.OPSFLAGS_RESOURCE.name_plural, st, et)
    name_or_id = get_lib.wildcard_name_or_id(name_or_id, exact)
    filters = {
        key: value for key, value in filters.items() if value is not None
    }
    handle_get_opsflags(name_or_id, output, st, et, **filters)


def handle_get_opsflags(name_or_id, output, st, et, **filters):
    """Output opsflags by name or id."""
    ctx = cfg.get_current_context()
    query = lib.query_builder("event_opsflag", name_or_id, **filters)
    opsflags = search_full_json(
        *ctx.get_api_data(),
        "event_opsflag",
        query,
        start_time=st,
        end_time=et,
    )
    get_lib.show_get_data(
        opsflags,
        output,
        _r.flags.flags_output_summary,
    )
