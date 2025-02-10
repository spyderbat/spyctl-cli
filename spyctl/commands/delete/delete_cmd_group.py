"""Contains the delete command group."""

import click

import spyctl.spyctl_lib as lib
from spyctl.commands.delete import (
    agent_health,
    custom_flag,
    notification_target,
    notification_template,
    policy,
    ruleset,
    saved_query,
)


@click.group("delete", cls=lib.CustomSubGroup, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
def delete():
    """Get Spyderbat Resources."""


delete.add_command(notification_target.delete_notif_tgt_cmd)
delete.add_command(policy.delete_policy_cmd)
delete.add_command(ruleset.delete_ruleset_cmd)
delete.add_command(saved_query.delete_saved_query_cmd)
delete.add_command(custom_flag.delete_custom_flag_cmd)
delete.add_command(notification_template.delete_notif_tmpl_cmd)
delete.add_command(agent_health.delete_agent_health_notification_settings_cmd)
