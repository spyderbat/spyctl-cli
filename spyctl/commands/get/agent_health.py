"""Handles retrieval of agent health notification settings."""

import click

import spyctl.api.agent_health as ahn_api
import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl.commands.get import get_lib


@click.command(
    "agent-health-notification-settings",
    cls=lib.CustomCommand,
    epilog=lib.SUB_EPILOG,
)
@_so.help_option
@_so.name_or_id_arg
@_so.output_option
@_so.page_option
@_so.page_size_option
@_so.exact_match_option
@_so.reversed_option
@_so.action_taken_option
@_so.latest_version_option
@_so.raw_data_option
@click.option(
    "--scope-query-equals",
    help="Filter by scope query matching the specified string.",
)
@click.option(
    "--scope-query-contains",
    help="Filter by scope query containing the specified string.",
)
@click.option(
    "--from-history",
    is_flag=True,
    help="Include historical archive data in the output.",
)
def get_agent_health_notification_settings(name_or_id, output, **kwargs):
    """Get agent health notification settings."""
    get_lib.output_time_log(
        lib.AGENT_HEALTH_NOTIFICATION_RESOURCE.name_plural, None, None
    )
    kwargs = {key: value for key, value in kwargs.items() if value is not None}
    handle_get_agent_health_notification_settings(name_or_id, output, **kwargs)


def handle_get_agent_health_notification_settings(name_or_id, output, **kwargs):
    """Handle the retrieval of agent health notification settings."""
    kwargs["page"] = kwargs.get("page", 0)
    kwargs["page_size"] = kwargs.get("page_size", 10)
    ctx = cfg.get_current_context()
    if name_or_id:
        kwargs["name_or_uid_contains"] = name_or_id
    (
        agent_health_notification_settings,
        total_pages,
    ) = ahn_api.get_agent_health_notification_settings_list(
        *ctx.get_api_data(), **kwargs
    )
    if kwargs.get("raw_data"):
        data_parser = None
    else:
        data_parser = _r.agent_health.data_to_yaml
    get_lib.show_get_data(
        agent_health_notification_settings,
        output,
        lambda data: _r.agent_health.summary_output(data, total_pages, kwargs["page"]),
        lambda data: _r.agent_health.wide_output(data, total_pages, kwargs["page"]),
        data_parser=data_parser,
    )
