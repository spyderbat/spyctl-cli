"""Handles the creation of notification templates."""

import click

import spyctl.spyctl_lib as lib
import spyctl.config.configs as cfg
from spyctl import cli
from spyctl.resources import notification_templates as _nts
from spyctl.commands.apply_cmd.notification_template import (
    handle_apply_notification_template,
)
from spyctl.api.notification_templates import get_notification_template


def template_settings_options(f):
    """Add template settings options to a click command."""
    f = click.option(
        "--exclude-mute",
        is_flag=True,
        help="Exclude the mute button from the sent notification.",
    )(f)
    f = click.option(
        "--include_attribution",
        is_flag=True,
        help="Include auto-generated details about the source of the sent notification.",
    )(f)
    f = click.option(
        "--include-linkback",
        is_flag=True,
        help="Include a linkback to the source of the sent notification.",
    )(f)
    return f


@click.group(
    name="notification-template", cls=lib.CustomSubGroup, epilog=lib.SUB_EPILOG
)
@click.help_option("-h", "--help", hidden=True)
def notification_template():
    """Create a notification template."""


@notification_template.command(name="email", cls=lib.CustomCommand)
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
    help="Name of the notification template.",
    metavar="",
)
@click.option(
    "-d",
    "--description",
    help="Description of the email notification template.",
    metavar="",
)
@click.option(
    "-s",
    "--subject",
    default="",
    help="Subject of the email notification template.",
    metavar="",
)
@click.option(
    "-b",
    "--body-html",
    default="",
    help="HTML body of the email notification template.",
    metavar="",
)
@click.option(
    "-B",
    "--body-text",
    default="",
    help="Text body of the email notification template.",
    metavar="",
)
@click.option(
    "-a",
    "--apply",
    is_flag=True,
    help="Apply the notification template during creation.",
)
@click.option(
    "-T",
    "--tags",
    help="The tags associated with the notification template. Comma delimited.",
    type=lib.ListParam(),
    metavar="",
)
@template_settings_options
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    help="Automatically answer yes to all prompts.",
)
def email(output, name, **kwargs):
    """Create an email notification template."""
    yes_option = kwargs.pop("yes")
    if yes_option:
        cli.set_yes_option()
    data = {
        "name": name,
        "template_type": lib.TMPL_TYPE_EMAIL,
        "template_data": {
            lib.TMPL_EMAIL_SUBJECT_FIELD: kwargs.pop("subject", None),
            lib.TMPL_EMAIL_BODY_HTML_FIELD: kwargs.pop("body_html", None),
            lib.TMPL_EMAIL_BODY_TEXT_FIELD: kwargs.pop("body_text", None),
        },
        "description": kwargs.pop("description", None),
        "tags": kwargs.pop("tags", None),
    }
    notification_template_resrc = _nts.data_to_yaml(data)
    should_apply = kwargs.pop("apply")
    if should_apply:
        ctx = cfg.get_current_context()
        uid = handle_apply_notification_template(notification_template_resrc)
        nt = get_notification_template(*ctx.get_api_data(), uid)
        model = _nts.data_to_yaml(nt)
    else:
        model = notification_template_resrc
    if output == lib.OUTPUT_DEFAULT:
        output = lib.OUTPUT_YAML
    cli.show(model, output)


@notification_template.command(name="slack", cls=lib.CustomCommand)
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
    help="Name of the notification template.",
    metavar="",
)
@click.option(
    "-d",
    "--description",
    help="Description of the Slack notification template.",
    metavar="",
)
@click.option(
    "-t",
    "--text",
    default="",
    help="Text of the Slack notification template. Used as a fallback if blocks are not provided.",
    metavar="",
)
@click.option(
    "-b",
    "--blocks",
    help='JSON list of blocks to be sent to Slack. Usually easier to edit as yaml. Default is "[]"',
    type=lib.JSONParam(),
    default="[]",
    metavar="",
)
@click.option(
    "-a",
    "--apply",
    is_flag=True,
    help="Apply the notification template during creation.",
)
@click.option(
    "-T",
    "--tags",
    help="The tags associated with the notification template. Comma delimited.",
    type=lib.ListParam(),
    metavar="",
)
@template_settings_options
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    help="Automatically answer yes to all prompts.",
)
def slack(output, name, **kwargs):
    """Create a Slack notification template."""
    yes_option = kwargs.pop("yes")
    if yes_option:
        cli.set_yes_option()
    data = {
        "name": name,
        "template_type": lib.TMPL_TYPE_SLACK,
        "template_data": {
            lib.TMPL_SLACK_TEXT_FIELD: kwargs.pop("text", None),
            lib.TMPL_SLACK_BLOCKS_FIELD: kwargs.pop("blocks", None),
        },
        "description": kwargs.pop("description", None),
        "tags": kwargs.pop("tags", None),
    }
    notification_template_resrc = _nts.data_to_yaml(data)
    should_apply = kwargs.pop("apply")
    if should_apply:
        ctx = cfg.get_current_context()
        uid = handle_apply_notification_template(notification_template_resrc)
        nt = get_notification_template(*ctx.get_api_data(), uid)
        model = _nts.data_to_yaml(nt)
    else:
        model = notification_template_resrc
    if output == lib.OUTPUT_DEFAULT:
        output = lib.OUTPUT_YAML
    cli.show(model, output)


@notification_template.command(name="pagerduty", cls=lib.CustomCommand)
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
    help="Name of the notification template.",
    metavar="",
)
@click.option(
    "-d",
    "--description",
    help="Description of the PagerDuty notification template.",
    metavar="",
)
@click.option(
    "-c",
    "--class",
    help="The class/type of the event.",
    metavar="",
)
@click.option(
    "-C",
    "--component",
    help="Component of the source machine that is responsible for the event.",
    metavar="",
)
@click.option(
    "-r",
    "--source",
    default="",
    help="Specific human-readable unique identifier, such as a hostname, for the system having the problem",
    metavar="",
)
@click.option(
    "-s",
    "--summary",
    help="A brief text summary of the event, used to generate the summaries/titles of any associated alerts.",
    default="",
    metavar="",
)
@click.option(
    "-S",
    "--severity",
    default="",
    help="The perceived severity of the notification. Can be one of info, warning, error, or critical.",
    metavar="",
)
@click.option(
    "-D",
    "--dedup-key",
    help="A string that uniquely identifies this event across the PagerDuty service."
    " If two events have the same dedup key, only one will be allowed through. Default is the summary of the event.",
    metavar="",
)
@click.option(
    "--custom-details",
    help="Additional details to be sent to PagerDuty as a JSON object. Usually easier to edit as yaml.",
    type=lib.JSONParam(),
    default="{}",
    metavar="",
)
@click.option(
    "-g",
    "--group",
    help='A cluster or grouping of sources. For example, sources "prod-datapipe-02" and "prod-datapipe-03" might both be part of "prod-datapipe".',
    metavar="",
)
@click.option(
    "-T",
    "--tags",
    help="The tags associated with the notification template. Comma delimited.",
    type=lib.ListParam(),
    metavar="",
)
@template_settings_options
@click.option(
    "-a",
    "--apply",
    is_flag=True,
    help="Apply the notification template during creation.",
)
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    help="Automatically answer yes to all prompts.",
)
def pagerduty(output, name, **kwargs):
    """Create a PagerDuty notification template."""
    yes_option = kwargs.pop("yes")
    if yes_option:
        cli.set_yes_option()
    data = {
        "name": name,
        "template_type": lib.TMPL_TYPE_PD,
        "template_data": {
            lib.TMPL_PD_CLASS_FIELD: kwargs.pop("class", None),
            lib.TMPL_PD_COMPONENT_FIELD: kwargs.pop("component", None),
            lib.TMPL_PD_SOURCE_FIELD: kwargs.pop("source", None),
            lib.TMPL_PD_SUMMARY_FIELD: kwargs.pop("summary", None),
            lib.TMPL_PD_SEVERITY_FIELD: kwargs.pop("severity", None),
            lib.TMPL_PD_DEDUP_KEY_FIELD: kwargs.pop("dedup_key", None),
            lib.TMPL_PD_CUSTOM_DETAILS_FIELD: kwargs.pop(
                "custom_details", None
            ),
            lib.TMPL_PD_GROUP_FIELD: kwargs.pop("group", None),
        },
        "description": kwargs.pop("description", None),
        "tags": kwargs.pop("tags", None),
    }
    notification_template_resrc = _nts.data_to_yaml(data)
    should_apply = kwargs.pop("apply")
    if should_apply:
        ctx = cfg.get_current_context()
        uid = handle_apply_notification_template(notification_template_resrc)
        nt = get_notification_template(*ctx.get_api_data(), uid)
        model = _nts.data_to_yaml(nt)
    else:
        model = notification_template_resrc
    if output == lib.OUTPUT_DEFAULT:
        output = lib.OUTPUT_YAML
    cli.show(model, output)


@notification_template.command(name="webhook", cls=lib.CustomCommand)
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
    help="Name of the notification template.",
    metavar="",
)
@click.option(
    "-d",
    "--description",
    help="Description of the webhook notification template.",
    metavar="",
)
@click.option(
    "-p",
    "--payload",
    help="The payload of the webhook notification template.",
    type=lib.JSONParam(),
    default="{}",
    metavar="",
)
@click.option(
    "--entire_object",
    is_flag=True,
    help="Send the entire object as the payload.",
)
@click.option(
    "-a",
    "--apply",
    is_flag=True,
    help="Apply the notification template during creation.",
)
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    help="Automatically answer yes to all prompts.",
)
def webhook(output, name, **kwargs):
    """Create a webhook notification template."""
    yes_option = kwargs.pop("yes")
    if yes_option:
        cli.set_yes_option()
    data = {
        "name": name,
        "template_type": lib.TMPL_TYPE_WEBHOOK,
        "template_data": {
            lib.TMPL_WEBHOOK_PAYLOAD_FIELD: kwargs.pop("payload", None),
            lib.TMPL_WEBHOOK_ENTIRE_OBJECT_FIELD: kwargs.pop(
                "entire_object", None
            ),
        },
        "description": kwargs.pop("description", None),
        "tags": kwargs.pop("tags", None),
    }
    notification_template_resrc = _nts.data_to_yaml(data)
    should_apply = kwargs.pop("apply")
    if should_apply:
        ctx = cfg.get_current_context()
        uid = handle_apply_notification_template(notification_template_resrc)
        nt = get_notification_template(*ctx.get_api_data(), uid)
        model = _nts.data_to_yaml(nt)
    else:
        model = notification_template_resrc
    if output == lib.OUTPUT_DEFAULT:
        output = lib.OUTPUT_YAML
    cli.show(model, output)
