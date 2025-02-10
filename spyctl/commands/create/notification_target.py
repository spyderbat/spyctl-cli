"""Handles the creation of notification targets."""

import click

import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.resources import notification_targets as _nts
from spyctl.commands.apply_cmd.notification_target import (
    handle_apply_notification_target,
)
from spyctl.api.notification_targets import get_notification_target


@click.group(
    name="notification-target", cls=lib.CustomSubGroup, epilog=lib.SUB_EPILOG
)
@click.help_option("-h", "--help", hidden=True)
def notification_target():
    """Create a notification target."""


@notification_target.command(name="pagerduty", cls=lib.CustomCommand)
@click.help_option("-h", "--help", hidden=True)
@click.option(
    "-o",
    "--output",
    default=lib.OUTPUT_DEFAULT,
    type=click.Choice(lib.OUTPUT_CHOICES, case_sensitive=False),
)
@click.option(
    "-n",
    "--name",
    required=True,
    help="Name of the notification target.",
    metavar="",
)
@click.option(
    "-d",
    "--description",
    help="Description of the notification target.",
    metavar="",
)
@click.option(
    "-r",
    "--routing-key",
    required=True,
    help="PagerDuty routing key of the notification target.",
)
@click.option(
    "-T",
    "--tags",
    help="The tags associated with the custom flag. Comma delimited.",
    type=lib.ListParam(),
    metavar="",
)
@click.option(
    "-a",
    "--apply",
    is_flag=True,
    help="Apply the notification target during creation.",
)
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    help="Automatically answer yes to all prompts.",
)
def pagerduty(output, name, routing_key, **kwargs):
    """Create a PagerDuty notification target."""
    yes_option = kwargs.pop("yes")
    if yes_option:
        cli.set_yes_option()
    data = {
        "name": name,
        "target_type": lib.TGT_TYPE_PAGERDUTY,
        "target_data": {
            "routing_key": routing_key,
        },
        "description": kwargs.pop("description", None),
        "tags": kwargs.pop("tags", None),
    }
    notification_target_resrc = _nts.data_to_yaml(data)
    should_apply = kwargs.pop("apply")
    if should_apply:
        ctx = cfg.get_current_context()
        uid = handle_apply_notification_target(notification_target_resrc)
        nt = get_notification_target(*ctx.get_api_data(), uid)
        model = _nts.data_to_yaml(nt)
    else:
        model = notification_target_resrc
    output = kwargs.pop("output", lib.OUTPUT_YAML)
    if output == lib.OUTPUT_DEFAULT:
        output = lib.OUTPUT_YAML
    cli.show(model, output)


@notification_target.command(name="slack", cls=lib.CustomCommand)
@click.help_option("-h", "--help", hidden=True)
@click.option(
    "-o",
    "--output",
    default=lib.OUTPUT_DEFAULT,
    type=click.Choice(lib.OUTPUT_CHOICES, case_sensitive=False),
)
@click.option(
    "-n",
    "--name",
    required=True,
    help="Name of the notification target.",
    metavar="",
)
@click.option(
    "-d",
    "--description",
    help="Description of the notification target.",
    metavar="",
)
@click.option(
    "-T",
    "--tags",
    help="The tags associated with the notification target. Comma delimited.",
    type=lib.ListParam(),
    metavar="",
)
@click.option(
    "-u",
    "--url",
    required=True,
    help="URL of the Slack notification target.",
)
@click.option(
    "-a",
    "--apply",
    is_flag=True,
    help="Apply the notification target during creation.",
)
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    help="Automatically answer yes to all prompts.",
)
def slack(output, name, url, **kwargs):
    """Create a Slack notification target."""
    yes_option = kwargs.pop("yes")
    if yes_option:
        cli.set_yes_option()
    data = {
        "name": name,
        "target_type": lib.TGT_TYPE_SLACK,
        "target_data": {
            "url": url,
        },
        "description": kwargs.pop("description", None),
        "tags": kwargs.pop("tags", None),
    }
    notification_target_resrc = _nts.data_to_yaml(data)
    should_apply = kwargs.pop("apply")
    if should_apply:
        ctx = cfg.get_current_context()
        uid = handle_apply_notification_target(notification_target_resrc)
        nt = get_notification_target(*ctx.get_api_data(), uid)
        model = _nts.data_to_yaml(nt)
    else:
        model = notification_target_resrc
    output = kwargs.pop("output", lib.OUTPUT_YAML)
    if output == lib.OUTPUT_DEFAULT:
        output = lib.OUTPUT_YAML
    cli.show(model, output)


@notification_target.command(name="email", cls=lib.CustomCommand)
@click.help_option("-h", "--help", hidden=True)
@click.option(
    "-o",
    "--output",
    default=lib.OUTPUT_DEFAULT,
    type=click.Choice(lib.OUTPUT_CHOICES, case_sensitive=False),
)
@click.option(
    "-n",
    "--name",
    required=True,
    help="Name of the notification target.",
    metavar="",
)
@click.option(
    "-d",
    "--description",
    help="Description of the notification target.",
    metavar="",
)
@click.option(
    "-e",
    "--emails",
    required=True,
    help="Email of the notification target.",
    type=lib.ListParam(),
    metavar="",
)
@click.option(
    "-T",
    "--tags",
    help="The tags associated with the notification target. Comma delimited.",
    type=lib.ListParam(),
    metavar="",
)
@click.option(
    "-a",
    "--apply",
    is_flag=True,
    help="Apply the notification target during creation.",
)
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    help="Automatically answer yes to all prompts.",
)
def email(output, name, emails, **kwargs):
    """Create an email notification target."""
    yes_option = kwargs.pop("yes")
    if yes_option:
        cli.set_yes_option()
    data = {
        "name": name,
        "target_type": lib.TGT_TYPE_EMAIL,
        "target_data": {
            "emails": emails,
        },
        "description": kwargs.pop("description", None),
        "tags": kwargs.pop("tags", None),
    }
    notification_target_resrc = _nts.data_to_yaml(data)
    should_apply = kwargs.pop("apply")
    if should_apply:
        ctx = cfg.get_current_context()
        uid = handle_apply_notification_target(notification_target_resrc)
        nt = get_notification_target(*ctx.get_api_data(), uid)
        model = _nts.data_to_yaml(nt)
    else:
        model = notification_target_resrc
    output = kwargs.pop("output", lib.OUTPUT_YAML)
    if output == lib.OUTPUT_DEFAULT:
        output = lib.OUTPUT_YAML
    cli.show(model, output)


@notification_target.command(name="webhook", cls=lib.CustomCommand)
@click.help_option("-h", "--help", hidden=True)
@click.option(
    "-o",
    "--output",
    default=lib.OUTPUT_DEFAULT,
    type=click.Choice(lib.OUTPUT_CHOICES, case_sensitive=False),
)
@click.option(
    "-n",
    "--name",
    required=True,
    help="Name of the notification target.",
    metavar="",
)
@click.option(
    "-d",
    "--description",
    help="Description of the notification target.",
    metavar="",
)
@click.option(
    "-T",
    "--tags",
    help="The tags associated with the notification target. Comma delimited.",
    type=lib.ListParam(),
    metavar="",
)
@click.option(
    "-u",
    "--url",
    required=True,
    help="URL of the webhook notification target.",
    metavar="",
)
@click.option(
    "-a",
    "--apply",
    is_flag=True,
    help="Apply the notification target during creation.",
)
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    help="Automatically answer yes to all prompts.",
)
def webhook(output, name, url, **kwargs):
    """Create a webhook notification target."""
    yes_option = kwargs.pop("yes")
    if yes_option:
        cli.set_yes_option()
    data = {
        "name": name,
        "target_type": lib.TGT_TYPE_WEBHOOK,
        "target_data": {
            "url": url,
        },
        "description": kwargs.pop("description", None),
        "tags": kwargs.pop("tags", None),
    }
    notification_target_resrc = _nts.data_to_yaml(data)
    should_apply = kwargs.pop("apply")
    if should_apply:
        ctx = cfg.get_current_context()
        uid = handle_apply_notification_target(notification_target_resrc)
        nt = get_notification_target(*ctx.get_api_data(), uid)
        model = _nts.data_to_yaml(nt)
    else:
        model = notification_target_resrc
    output = kwargs.pop("output", lib.OUTPUT_YAML)
    if output == lib.OUTPUT_DEFAULT:
        output = lib.OUTPUT_YAML
    cli.show(model, output)
