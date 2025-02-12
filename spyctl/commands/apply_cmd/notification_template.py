"""Handles apply notification_templates."""

from typing import Dict

import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.notification_templates import (
    create_email_notification_template,
    create_pagerduty_notification_template,
    create_slack_notification_template,
    create_webhook_notification_template,
    update_email_notification_template,
    update_pagerduty_notification_template,
    update_slack_notification_template,
    update_webhook_notification_template,
)


def handle_apply_notification_template(resrc_data: Dict, from_edit: bool = False):
    """
    Handles the application of a notification template.
    """
    tmpl_type = resrc_data[lib.METADATA_FIELD].get("type")
    if tmpl_type == lib.TMPL_TYPE_EMAIL:
        return handle_apply_email_notification_template(resrc_data, from_edit)
    if tmpl_type == lib.TMPL_TYPE_SLACK:
        return handle_apply_slack_notification_template(resrc_data, from_edit)
    if tmpl_type == lib.TMPL_TYPE_PD:
        return handle_apply_pagerduty_notification_template(resrc_data, from_edit)
    if tmpl_type == lib.TMPL_TYPE_WEBHOOK:
        return handle_apply_webhook_notification_template(resrc_data, from_edit)
    raise ValueError(f"Unsupported template type: {tmpl_type}")


def handle_apply_email_notification_template(resrc_data: Dict, from_edit: bool = False):
    """
    Handles the application of an email notification template.
    """
    ctx = cfg.get_current_context()
    metadata = resrc_data[lib.METADATA_FIELD]
    spec = resrc_data[lib.SPEC_FIELD]
    uid = metadata.get("uid")
    kwargs = {
        "name": metadata[lib.METADATA_NAME_FIELD],
        "subject": spec[lib.TMPL_EMAIL_SUBJECT_FIELD],
        "body_text": spec.get(lib.TMPL_EMAIL_BODY_TEXT_FIELD),
        "body_html": spec.get(lib.TMPL_EMAIL_BODY_HTML_FIELD),
    }
    if lib.TMPL_DESCRIPTION_FIELD in metadata:
        kwargs["description"] = metadata[lib.TMPL_DESCRIPTION_FIELD]
    else:
        kwargs["clear_description"] = True
    if lib.METADATA_TAGS_FIELD in metadata:
        kwargs["tags"] = metadata[lib.METADATA_TAGS_FIELD]
    else:
        kwargs["clear_tags"] = True
    if uid is None:
        uid = create_email_notification_template(
            *ctx.get_api_data(),
            **kwargs,
        )
        cli.try_log(f"Successfully created email notification template {uid}")
    else:
        update_email_notification_template(
            *ctx.get_api_data(),
            template_uid=uid,
            **kwargs,
        )
        if from_edit:
            cli.try_log(f"Successfully edited email notification template {uid}")
        else:
            cli.try_log(f"Successfully created email notification template {uid}")
    return uid


def handle_apply_slack_notification_template(resrc_data: Dict, from_edit: bool = False):
    """
    Handles the application of a Slack notification template.
    """
    ctx = cfg.get_current_context()
    metadata = resrc_data[lib.METADATA_FIELD]
    spec = resrc_data[lib.SPEC_FIELD]
    uid = metadata.get("uid")
    kwargs = {
        "name": metadata[lib.METADATA_NAME_FIELD],
        "text": spec.get(lib.TMPL_SLACK_TEXT_FIELD),
        "blocks": spec.get(lib.TMPL_SLACK_BLOCKS_FIELD),
    }
    if lib.TMPL_DESCRIPTION_FIELD in metadata:
        kwargs["description"] = metadata[lib.TMPL_DESCRIPTION_FIELD]
    else:
        kwargs["clear_description"] = True
    if lib.METADATA_TAGS_FIELD in metadata:
        kwargs["tags"] = metadata[lib.METADATA_TAGS_FIELD]
    else:
        kwargs["clear_tags"] = True
    if uid is None:
        uid = create_slack_notification_template(
            *ctx.get_api_data(),
            **kwargs,
        )
        cli.try_log(f"Successfully created Slack notification template {uid}")
    else:
        update_slack_notification_template(
            *ctx.get_api_data(),
            notification_template_uid=uid,
            **kwargs,
        )
        if from_edit:
            cli.try_log(f"Successfully edited Slack notification template {uid}")
        else:
            cli.try_log(f"Successfully created Slack notification template {uid}")
    return uid


def handle_apply_pagerduty_notification_template(
    resrc_data: Dict, from_edit: bool = False
):
    """
    Handles the application of a PagerDuty notification template.
    """
    ctx = cfg.get_current_context()
    metadata = resrc_data[lib.METADATA_FIELD]
    spec = resrc_data[lib.SPEC_FIELD]
    uid = metadata.get("uid")
    kwargs = {
        "name": metadata[lib.METADATA_NAME_FIELD],
        "summary": spec[lib.TMPL_PD_SUMMARY_FIELD],
        "severity": spec[lib.TMPL_PD_SEVERITY_FIELD],
        "source": spec[lib.TMPL_PD_SOURCE_FIELD],
    }
    if lib.TMPL_PD_COMPONENT_FIELD in spec:
        kwargs["component"] = spec[lib.TMPL_PD_COMPONENT_FIELD]
    if lib.TMPL_PD_GROUP_FIELD in spec:
        kwargs["group"] = spec[lib.TMPL_PD_GROUP_FIELD]
    if lib.TMPL_PD_CLASS_FIELD in spec:
        kwargs["class_field"] = spec[lib.TMPL_PD_CLASS_FIELD]
    if lib.TMPL_PD_CUSTOM_DETAILS_FIELD in spec:
        kwargs["custom_details"] = spec[lib.TMPL_PD_CUSTOM_DETAILS_FIELD]
    if lib.TMPL_PD_DEDUP_KEY_FIELD in spec:
        kwargs["dedup_key"] = spec[lib.TMPL_PD_DEDUP_KEY_FIELD]
    if lib.TMPL_DESCRIPTION_FIELD in metadata:
        kwargs["description"] = metadata[lib.TMPL_DESCRIPTION_FIELD]
    else:
        kwargs["clear_description"] = True
    if lib.METADATA_TAGS_FIELD in metadata:
        kwargs["tags"] = metadata[lib.METADATA_TAGS_FIELD]
    else:
        kwargs["clear_tags"] = True
    if uid is None:
        uid = create_pagerduty_notification_template(
            *ctx.get_api_data(),
            **kwargs,
        )
        cli.try_log(f"Successfully created PagerDuty notification template {uid}")
    else:
        update_pagerduty_notification_template(
            *ctx.get_api_data(),
            template_uid=uid,
            **kwargs,
        )
        if from_edit:
            cli.try_log(f"Successfully edited PagerDuty notification template {uid}")
        else:
            cli.try_log(f"Successfully created PagerDuty notification template {uid}")
    return uid


def handle_apply_webhook_notification_template(
    resrc_data: Dict, from_edit: bool = False
):
    """
    Handles the application of a webhook notification template.
    """
    ctx = cfg.get_current_context()
    metadata = resrc_data[lib.METADATA_FIELD]
    spec = resrc_data[lib.SPEC_FIELD]
    uid = metadata.get("uid")
    kwargs = {
        "name": metadata[lib.METADATA_NAME_FIELD],
        "payload": spec.get(lib.TMPL_WEBHOOK_PAYLOAD_FIELD),
        "entire_object": spec.get(lib.TMPL_WEBHOOK_ENTIRE_OBJECT_FIELD),
    }
    if lib.TMPL_DESCRIPTION_FIELD in metadata:
        kwargs["description"] = metadata[lib.TMPL_DESCRIPTION_FIELD]
    else:
        kwargs["clear_description"] = True
    if lib.METADATA_TAGS_FIELD in metadata:
        kwargs["tags"] = metadata[lib.METADATA_TAGS_FIELD]
    else:
        kwargs["clear_tags"] = True
    if uid is None:
        uid = create_webhook_notification_template(
            *ctx.get_api_data(),
            **kwargs,
        )
        cli.try_log(f"Successfully created webhook notification template {uid}")
    else:
        update_webhook_notification_template(
            *ctx.get_api_data(),
            template_uid=uid,
            **kwargs,
        )
        if from_edit:
            cli.try_log(f"Successfully edited webhook notification template {uid}")
        else:
            cli.try_log(f"Successfully created webhook notification template {uid}")
    return uid
