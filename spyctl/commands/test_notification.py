"""Handles the test-notification subcommand for spyctl."""

import json
from typing import IO

import click

import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
from spyctl.api.notification_targets import get_notification_targets
from spyctl.api.notification_templates import get_notification_templates
from spyctl.api.notifications import post_test_notification

# ----------------------------------------------------------------- #
#                   Test Notification Subcommand                    #
# ----------------------------------------------------------------- #


@click.command("test-notification", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
@click.option(
    "-T",
    "--target",
    metavar="",
    help="Target name or UID to send a test notification to. Supply only this value to test that a target is reachable.",
)
@click.option(
    "-P",
    "--template",
    metavar="",
    help="Template name or UID of the same type as the target. This must be provided along with the target of the same type to send a test notification.",
)
@click.option(
    "-S",
    "--notification-settings-uid",
    metavar="",
    help="Notification settings UID to use for the test notification."
    " This is used to test a specific feature/trigger notification settings."
    " Such as testing the configuration for (Agent Health Notifications/Agent Offline) Notifications.",
)
@click.option(
    "-f",
    "--record-file",
    metavar="",
    type=click.File(),
    help="File containing a JSON record used to build the notification.",
)
def test_notification(target, template, record_file, notification_settings_uid):
    """Send test notifications to Targets or Notification Routes.

    Targets are named destinations like email, slack hooks, webhooks, or sns
    topics.
    Notification Routes define which notifications are send to which targets.
    Testing a notification route will send a test notification to one or many
    targets it is configured with.
    """
    handle_test_notification(target, template, record_file, notification_settings_uid)


# ----------------------------------------------------------------- #
#                    Test Notification Handlers                     #
# ----------------------------------------------------------------- #


def handle_test_notification(
    target_name_or_uid,
    template_name_or_uid,
    record_file: IO,
    notification_settings_uid: str,
):
    """
    Sends a test notification to the specified targets.

    Args:
        test_targets (list): A list of target names or IDs to send the test
            notification to.

    Raises:
        SystemExit: If no targets are provided, or if there are no targets to
            test.

    Returns:
        None
    """
    ctx = cfg.get_current_context()
    record = None
    if record_file:
        try:
            record = json.load(record_file)
        except json.JSONDecodeError:
            lib.err_exit("Invalid JSON record file")
    target = {"uid": ""}
    template = {"uid": ""}
    if target_name_or_uid:
        tgt_params = {
            "name_or_uid_contains": target_name_or_uid,
        }
        targets, _ = get_notification_targets(*ctx.get_api_data(), **tgt_params)
        if not targets:
            lib.err_exit(f"No targets found for {target_name_or_uid}")
        if len(targets) > 1:
            lib.err_exit(f"Ambiguous targets found for {target_name_or_uid}")
        target = targets[0]
        if template_name_or_uid:
            tmpl_params = {
                "name_or_uid_contains": template_name_or_uid,
            }
            templates, _ = get_notification_templates(
                *ctx.get_api_data(), **tmpl_params
            )
            if not templates:
                lib.err_exit(f"No templates found for {template_name_or_uid}")
            if len(templates) > 1:
                lib.err_exit(f"Ambiguous templates found for {template_name_or_uid}")
            template = templates[0]

    post_test_notification(
        *ctx.get_api_data(),
        target_uid=target["uid"],
        template_uid=template["uid"],
        notification_settings_uid=notification_settings_uid,
        record=record,
    )
