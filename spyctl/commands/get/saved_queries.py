"""Handles retrieval of saved_queries."""

import click

import spyctl.api.saved_queries as sq_api
import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl.commands import search
from spyctl.commands.get import get_lib


@click.command("saved-queries", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.help_option
@_so.name_or_id_arg
@_so.output_option
@_so.page_option
@_so.page_size_option
@_so.exact_match_option
@_so.reversed_option
@click.option(
    "--query-contains",
    help="Filter by saved query query containing the specified string.",
    metavar="",
)
@click.option(
    "--query-equals",
    help="Filter by saved query query matching the specified string.",
    metavar="",
)
@click.option(
    "--schema-equals",
    help="Filter by saved query schema matching the specified string.",
    metavar="",
)
@click.option(
    "--sort-by",
    help="Sort by the specified field.",
    type=click.Choice(
        [
            "name",
            "description",
            "query",
            "schema",
            "create_time",
            "last_used",
        ],
        case_sensitive=False,
    ),
    metavar="",
)
def get_saved_queries(name_or_id, output, **kwargs):
    """Get saved_queries by name or id."""
    get_lib.output_time_log(lib.SAVED_QUERY_RESOURCE.name_plural, None, None)
    kwargs = {key: value for key, value in kwargs.items() if value is not None}
    search.load_schemas()
    if "schema_equals" in kwargs:
        kwargs["schema_equals"] = search.TITLE_TO_SCHEMA_MAP.get(
            kwargs["schema_equals"], kwargs["schema_equals"]
        )
    handle_get_saved_queries(name_or_id, output, **kwargs)


def handle_get_saved_queries(name_or_id, output, **kwargs):
    """Output saved_queries by name or id."""
    kwargs["page"] = kwargs.get("page", 0)
    kwargs["page_size"] = kwargs.get("page_size", 10)
    ctx = cfg.get_current_context()
    if name_or_id:
        kwargs["name_or_uid_contains"] = name_or_id
    saved_queries, total_pages = sq_api.get_saved_queries(*ctx.get_api_data(), **kwargs)
    get_lib.show_get_data(
        saved_queries,
        output,
        lambda data: _r.saved_queries.summary_output(data, total_pages, kwargs["page"]),
        lambda data: _r.saved_queries.wide_output(data, total_pages, kwargs["page"]),
        data_parser=_r.saved_queries.data_to_yaml,
    )
