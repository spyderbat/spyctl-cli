"""Handles retrieval of saved_queries."""

import click

import spyctl.api.search_sets as ss_api
import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl.commands.get import get_lib


@click.command("search-sets", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.help_option
@_so.name_or_id_arg
@click.option(
    "--from-archive",
    is_flag=True,
    help="Retrieve archived search set versions.",
)
@_so.output_option
def get_search_sets(name_or_id, output, **kwargs):
    """Get search sets by name or id."""
    get_lib.output_time_log(lib.SEARCH_SET_RESOURCE.name_plural, None, None)
    kwargs = {key: value for key, value in kwargs.items() if value is not None}
    handle_get_search_sets(name_or_id, output, **kwargs)


def handle_get_search_sets(name_or_id, output, **kwargs):
    """Output search sets by name or id."""
    ctx = cfg.get_current_context()
    if name_or_id:
        kwargs["name_or_uid_contains"] = name_or_id
    search_sets = ss_api.get_search_sets(*ctx.get_api_data(), **kwargs)
    get_lib.show_get_data(
        search_sets,
        output,
        lambda data: _r.search_sets.summary_output(data),
        lambda data: _r.search_sets.wide_output(data),
        data_parser=_r.search_sets.data_to_yaml,
    )
