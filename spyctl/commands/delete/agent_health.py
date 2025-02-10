"""Handle the deletion of agent health notification settings."""

import click

import spyctl.commands.delete.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.agent_health import (
    delete_agent_health_notification_settings,
    get_agent_health_notification_settings_list,
)
from spyctl.commands.delete import saved_query


@click.command(
    "agent-health-notification-settings",
    cls=lib.CustomCommand,
    epilog=lib.SUB_EPILOG,
)
@_so.delete_options
def delete_agent_health_notification_settings_cmd(name_or_id, yes=False):
    """Delete agent health notification settings by name or ID."""
    if yes:
        cli.set_yes_option()
    handle_delete_agent_health_notification_settings(name_or_id)


def handle_delete_agent_health_notification_settings(name_or_id):
    """Handle the deletion of agent health notification settings."""
    ctx = cfg.get_current_context()
    params = {"name_or_uid_contains": name_or_id}
    agent_health_notification_settings, _ = (
        get_agent_health_notification_settings_list(
            *ctx.get_api_data(), **params
        )
    )
    if len(agent_health_notification_settings) == 0:
        cli.err_exit(
            f"No agent health notification settings matching name_or_id '{name_or_id}'"
        )
    for (
        agent_health_notification_setting
    ) in agent_health_notification_settings:
        name = agent_health_notification_setting["name"]
        uid = agent_health_notification_setting["uid"]
        perform_delete = cli.query_yes_no(
            f"Are you sure you want to delete agent health notification settings '{name} - {uid}'?"
        )
        if perform_delete:
            delete_agent_health_notification_settings(*ctx.get_api_data(), uid)
            cli.try_log(
                f"Successfully deleted agent health notification settings '{name} - {uid}'"
            )
        else:
            cli.try_log(f"Skipping delete of '{name} - {uid}'")
