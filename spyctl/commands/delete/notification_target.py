"""Handles the delete notification target command"""

import click

import spyctl.commands.delete.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.notification_targets import (
    delete_notification_target,
    get_notification_targets,
)


@click.command("notification-target", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.delete_options
def delete_notif_tgt_cmd(name_or_id, yes=False):
    """Delete a notification target by name or uid"""
    if yes:
        cli.set_yes_option()
    handle_delete_notif_tgt(name_or_id)


def handle_delete_notif_tgt(name_or_id):
    """
    Handles the deletion of a notification target.
    """
    ctx = cfg.get_current_context()
    params = {"name_or_uid_contains": name_or_id}
    targets, _ = get_notification_targets(*ctx.get_api_data(), **params)
    if len(targets) == 0:
        cli.err_exit(f"No notification targets matching '{name_or_id}'.")
    for target in targets:
        name = target["name"]
        uid = target["uid"]
        perform_delete = cli.query_yes_no(
            f"Are you sure you want to delete notification target '{name} - {uid}'?"
        )
        if perform_delete:
            delete_notification_target(*ctx.get_api_data(), uid)
            cli.try_log(f"Successfully deleted notification target '{name} - {uid}'")
        else:
            cli.try_log(f"Skipping delete of '{name} - {uid}'")
