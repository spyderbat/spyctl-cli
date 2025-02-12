"""Handles retrieval of custom flags."""

import click

import spyctl.api.custom_flags as cf_api
import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl.commands import search
from spyctl.commands.get import get_lib


@click.command("custom-flags", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.help_option
@_so.name_or_id_arg
@_so.output_option
@_so.page_option
@_so.page_size_option
@_so.exact_match_option
@_so.is_enabled_option
@_so.is_not_enabled_option
@_so.reversed_option
@_so.tags_contain_option
@_so.action_taken_option
@_so.latest_version_option
@_so.raw_data_option
@click.option(
    "--content-contains",
    help="Filter by custom flag content containing the specified string.",
)
@click.option(
    "--impact-contains",
    help="Filter by custom flag impact containing the specified string.",
)
@click.option(
    "--query-contains",
    help="Filter by custom flag query containing the specified string.",
)
@click.option(
    "--query-equals",
    help="Filter by custom flag query matching the specified string.",
)
@click.option(
    "--schema-equals",
    help="Filter by custom flag schema matching the specified string.",
)
@click.option(
    "--query-uid-equals",
    help="Filter for custom flags with a saved query UID matching the"
    " specified string.",
)
@click.option(
    "--severity-equals",
    help="Filter by custom flag severity matching the specified string.",
)
@click.option(
    "--from-history",
    is_flag=True,
    help="Include historical archive data in the output.",
)
@click.option(
    "--flag-type-equals",
    help="Filter by custom flag type matching the specified string.",
    type=click.Choice(lib.FLAG_TYPES),
)
@click.option(
    "--sort-by",
    help="Sort by the specified field.",
    type=click.Choice(
        [
            "name",
            "description",
            "create_time",
            "query",
            "schema",
            "severity",
            "impact",
            "last_updated",
            "is_enabled",
        ],
        case_sensitive=False,
    ),
)
@click.option(
    "--version",
    help="Filter by the specified version of the custom flag.",
    type=click.INT,
)
def get_custom_flags(name_or_id, output, **kwargs):
    """Get custom flags by name or id."""
    get_lib.output_time_log(lib.CUSTOM_FLAG_RESOURCE.name_plural, None, None)
    kwargs = {key: value for key, value in kwargs.items() if value is not None}
    search.load_schemas()
    if "schema_equals" in kwargs:
        kwargs["schema_equals"] = search.TITLE_TO_SCHEMA_MAP.get(
            kwargs["schema_equals"], kwargs["schema_equals"]
        )
    handle_get_custom_flags(name_or_id, output, **kwargs)


def handle_get_custom_flags(name_or_id, output, **kwargs):
    """Output custom flags by name or id."""
    kwargs["page"] = kwargs.get("page", 0)
    kwargs["page_size"] = kwargs.get("page_size", 10)
    ctx = cfg.get_current_context()
    if name_or_id:
        kwargs["name_or_uid_contains"] = name_or_id
    custom_flags, total_pages = cf_api.get_custom_flags(*ctx.get_api_data(), **kwargs)
    if kwargs.get("raw_data"):
        data_parser = None
    else:
        data_parser = _r.custom_flags.data_to_yaml
    get_lib.show_get_data(
        custom_flags,
        output,
        lambda data: _r.custom_flags.summary_output(data, total_pages, kwargs["page"]),
        lambda data: _r.custom_flags.wide_output(data, total_pages, kwargs["page"]),
        data_parser=data_parser,
    )
