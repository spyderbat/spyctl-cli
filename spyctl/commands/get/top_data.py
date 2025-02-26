"""Handles retrieval of top data."""

import click

import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.athena_search import search_athena
from spyctl.commands.get import get_lib


@click.command("top-data", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.athena_query_options
@_so.schema_options("event_top_data")
def get_top_data_cmd(name_or_id, output, st, et, **filters):
    """Get top-data by name or id."""
    exact = filters.pop("exact")
    get_lib.output_time_log(lib.TOP_DATA_RESOURCE.name_plural, st, et)
    name_or_id = get_lib.wildcard_name_or_id(name_or_id, exact)
    filters = {key: value for key, value in filters.items() if value is not None}
    handle_get_top_data(name_or_id, output, st, et, **filters)


def handle_get_top_data(name_or_id, output, st, et, **filters):
    """Output top-data by name or id."""
    ctx = cfg.get_current_context()
    query = lib.query_builder("event_top_data", name_or_id, **filters)
    if "muid" not in query:
        cli.err_exit(
            "Provide an option with the machine uid of the machine you want top data for.\n"  # noqa
            "'spyctl get machines' will provide a list."
        )
    top_data = search_athena(
        *ctx.get_api_data(),
        "event_top_data",
        query,
        start_time=st,
        end_time=et,
    )
    get_lib.show_get_data(
        top_data,
        output,
        None,
    )
