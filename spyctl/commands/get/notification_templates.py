"""Handles retrieval of notification_templates."""

import click

import spyctl.api.notification_templates as nt_api
import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl.commands.get import get_lib


@click.command(
    "notification-templates", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG
)
@_so.help_option
@_so.name_or_id_arg
@_so.output_option
@_so.page_option
@_so.page_size_option
@_so.exact_match_option
@_so.reversed_option
@_so.tags_contain_option
@_so.action_taken_option
@_so.latest_version_option
@_so.raw_data_option
@click.option(
    "--type-equals",
    help="Filter by notification target type.",
    type=click.Choice(lib.TGT_TYPES),
    metavar="",
)
@click.option(
    "--from-history",
    is_flag=True,
    help="Include historical archive data in the output.",
)
@click.option(
    "--sort-by",
    help="Sort the results by a field.",
    type=click.Choice(
        [
            "name",
            "description",
            "create_time",
            "last_updated",
            "type",
        ],
        case_sensitive=False,
    ),
    metavar="",
)
@click.option(
    "--version",
    help="Filter by the specified version of the notification target.",
    type=click.INT,
)
def get_notification_templates(name_or_id, output, **kwargs):
    """Get notification_templates by name or id."""
    get_lib.output_time_log(
        lib.NOTIFICATION_TEMPLATES_RESOURCE.name_plural, None, None
    )
    kwargs = {key: value for key, value in kwargs.items() if value is not None}
    handle_get_notification_templates(name_or_id, output, **kwargs)


def handle_get_notification_templates(name_or_id, output, **kwargs):
    """Output notification_templates by name or id."""
    kwargs["page"] = kwargs.get("page", 0)
    kwargs["page_size"] = kwargs.get("page_size", 10)
    ctx = cfg.get_current_context()
    if name_or_id:
        kwargs["name_or_uid_contains"] = name_or_id
    notification_templates, total_pages = nt_api.get_notification_templates(
        *ctx.get_api_data(), **kwargs
    )
    if kwargs.get("raw_data"):
        data_parser = None
    else:
        data_parser = _r.notification_templates.data_to_yaml
    get_lib.show_get_data(
        notification_templates,
        output,
        lambda data: _r.notification_templates.summary_output(
            data, total_pages, kwargs["page"]
        ),
        lambda data: _r.notification_templates.wide_output(
            data, total_pages, kwargs["page"]
        ),
        data_parser,
    )
