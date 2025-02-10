"""Create a new agent health notification settings."""

import click

import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl import schemas_v2 as schemas
from spyctl.resources.agent_health import data_to_yaml
from spyctl.commands.apply_cmd.agent_health import (
    handle_apply_agent_health_notification,
)
from spyctl.api.agent_health import get_agent_health_notification_settings
from spyctl.commands.notifications.configure.shared_options import (
    get_target_map,
)


@click.command(
    "agent-health-notification-settings",
    cls=lib.CustomCommand,
    epilog=lib.SUB_EPILOG,
)
@click.help_option("-h", "--help", hidden=True)
@click.option(
    "-a",
    "--apply",
    help="Apply the agent health notification settings during creation.",
    is_flag=True,
    default=False,
)
@click.option(
    "-n",
    "--name",
    help="Name for the agent health notification settings.",
    metavar="",
    required=True,
)
@click.option(
    "-d",
    "--description",
    help="Description for the agent health notification settings.",
    metavar="",
)
@click.option(
    "-q",
    "--scope-query",
    help="SpyQL query on model_agents table to determine which agents this setting applies to.",
)
@click.option(
    "-T",
    "--targets",
    help="Comma separated list of targets to send notifications to.",
    type=lib.ListParam(),
    metavar="",
)
@click.option(
    "--is-disabled",
    help="Disable the agent health notification settings on creation.",
    is_flag=True,
    default=False,
)
@click.option(
    "-o",
    "--output",
    help="Output format for the agent health notification settings.",
    type=click.Choice(lib.OUTPUT_CHOICES, case_sensitive=False),
    default=lib.OUTPUT_DEFAULT,
)
@click.option(
    "-y",
    "--yes",
    help="Automatically answer yes to all prompts.",
    is_flag=True,
    default=False,
)
def create_agent_health_notification_settings(output, **kwargs):
    """Create a new agent health notification settings."""
    yes_option = kwargs.pop("yes")
    if yes_option:
        cli.set_yes_option()
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    handle_create_agent_health_notification_settings(output, **kwargs)


def handle_create_agent_health_notification_settings(output, **kwargs):
    """Handle creating a new agent health notification settings."""
    ctx = cfg.get_current_context()
    should_apply = kwargs.pop("apply", False)
    data = {
        "name": kwargs["name"],
        "description": kwargs.get("description"),
        "scope_query": kwargs.get("scope_query"),
        "is_disabled": kwargs.get("is_disabled"),
    }
    if kwargs.get("targets"):
        target_map = get_target_map(**kwargs)
        settings = schemas.NotificationSettingsModel(
            **{
                "is_enabled": True,
                "target_map": target_map,
            }
        )
        notification_settings = schemas.AgentHealthNotificationsSettingsModel(
            agent_healthy=settings,
            agent_unhealthy=settings,
            agent_offline=settings,
            agent_online=settings,
        )
        notification_settings = notification_settings.model_dump(
            exclude_unset=True, exclude_none=True, by_alias=True
        )
        data["notification_settings"] = notification_settings
    agent_health_notification_settings_rec = data_to_yaml(data)
    if should_apply:
        uid = handle_apply_agent_health_notification(
            agent_health_notification_settings_rec
        )
        agent_health_notification_settings = (
            get_agent_health_notification_settings(*ctx.get_api_data(), uid)
        )
        model = data_to_yaml(agent_health_notification_settings)
    else:
        model = agent_health_notification_settings_rec
    if output == lib.OUTPUT_DEFAULT:
        output = lib.OUTPUT_YAML
    cli.show(model, output)
