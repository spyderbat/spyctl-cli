"""Handles listing notifications on Spyderbat resources"""

import click

import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
import spyctl.commands.get.shared_options as _so
from spyctl.commands.get import get_lib
from spyctl.api import notifications as notif_api
import spyctl.resources as _r


@click.command("list", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
@_so.help_option
@_so.name_or_id_arg
@_so.output_option
@_so.page_option
@_so.page_size_option
@_so.reversed_option
@click.option(
    "--refUID-equals",
    help="Filter by refUID matching the specified string.",
    metavar="",
)
def list_notifications(name_or_id, output, **kwargs):
    """List notifications on a Spyderbat resource."""
    get_lib.output_time_log("configured notifications", None, None)
    kwargs = {key: value for key, value in kwargs.items() if value is not None}
    handle_list_notifications(name_or_id, output, **kwargs)


def handle_list_notifications(name_or_id, output, **kwargs):
    """Handle listing notifications on a Spyderbat resource."""
    ctx = cfg.get_current_context()
    kwargs["page"] = kwargs.get("page", 0)
    kwargs["page_size"] = kwargs.get("page_size", 10)
    if name_or_id:
        kwargs["name_or_uid_contains"] = name_or_id
    notifications, total_pages = notif_api.get_notification_settings_list(
        *ctx.get_api_data(), kwargs
    )
    get_lib.show_get_data(
        notifications,
        output,
        lambda data: _r.notification_settings.summary_output(
            data, total_pages, kwargs["page"]
        ),
    )
