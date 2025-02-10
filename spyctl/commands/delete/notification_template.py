"""Handles the delete notification template command"""

import click

import spyctl.commands.delete.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.notification_templates import (
    get_notification_templates,
    delete_notification_template,
)


@click.command(
    "notification-template", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG
)
@_so.delete_options
def delete_notif_tmpl_cmd(name_or_id, yes=False):
    """Delete a notification template by name or uid"""
    if yes:
        cli.set_yes_option()
    handle_delete_notif_tmpl(name_or_id)


def handle_delete_notif_tmpl(name_or_id):
    """
    Handles the deletion of a notification template.
    """
    ctx = cfg.get_current_context()
    params = {"name_or_uid_contains": name_or_id}
    templates, _ = get_notification_templates(*ctx.get_api_data(), **params)
    if len(templates) == 0:
        cli.err_exit(f"No notification templates matching '{name_or_id}'.")
    for template in templates:
        name = template["name"]
        uid = template["uid"]
        perform_delete = cli.query_yes_no(
            f"Are you sure you want to delete notification template '{name} - {uid}'?"
        )
        if perform_delete:
            delete_notification_template(*ctx.get_api_data(), uid)
            cli.try_log(
                f"Successfully deleted notification template '{name} - {uid}'"
            )
        else:
            cli.try_log(f"Skipping delete of '{name} - {uid}'")
