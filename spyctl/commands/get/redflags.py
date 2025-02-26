"""Handles retrieval of redflags."""

import click

import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl.api.athena_search import search_athena
from spyctl.commands.get import get_lib


@click.command("redflags", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.athena_query_options
@_so.schema_options("event_redflag")
@click.option(
    "--include-exceptions",
    "exceptions",
    is_flag=True,
    help="Include redflags marked as exceptions in output. Off by default.",
)
def get_redflags_cmd(name_or_id, output, st, et, **filters):
    """Get redflags by name or id."""
    exact = filters.pop("exact")
    get_lib.output_time_log(lib.REDFLAGS_RESOURCE.name_plural, st, et)
    name_or_id = get_lib.wildcard_name_or_id(name_or_id, exact)
    filters = {
        key: value for key, value in filters.items() if value is not None
    }
    handle_get_redflags(name_or_id, output, st, et, **filters)


def handle_get_redflags(name_or_id, output, st, et, **filters):
    """Output redflags by name or id."""
    ctx = cfg.get_current_context()
    query = lib.query_builder("event_redflag", name_or_id, **filters)
    redflags = search_athena(
        *ctx.get_api_data(),
        "event_redflag",
        query,
        start_time=st,
        end_time=et,
    )
    get_lib.show_get_data(
        redflags,
        output,
        _r.flags.flags_output_summary,
    )
