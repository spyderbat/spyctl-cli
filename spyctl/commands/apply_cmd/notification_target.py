"""Handles apply notification_targets."""

from typing import Dict

import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.notification_targets import (
    create_email_notification_target,
    create_pagerduty_notification_target,
    create_slack_notification_target,
    create_webhook_notification_target,
    update_email_notification_target,
    update_pagerduty_notification_target,
    update_slack_notification_target,
    update_webhook_notification_target,
)


def handle_apply_notification_target(resrc_data: Dict, from_edit: bool = False):
    """
    Handles the application of a notification target.
    """
    tgt_type = resrc_data[lib.METADATA_FIELD].get("type")
    if tgt_type == lib.TGT_TYPE_PAGERDUTY:
        return handle_apply_pagerduty_notification_target(resrc_data, from_edit)
    if tgt_type == lib.TGT_TYPE_SLACK:
        return handle_apply_slack_notification_target(resrc_data, from_edit)
    if tgt_type == lib.TGT_TYPE_EMAIL:
        return handle_apply_email_notification_target(resrc_data, from_edit)
    if tgt_type == lib.TGT_TYPE_WEBHOOK:
        return handle_apply_webhook_notification_target(resrc_data, from_edit)
    raise ValueError(f"Unsupported notification target type: {tgt_type}")


def handle_apply_pagerduty_notification_target(
    resrc_data: Dict, from_edit: bool = False
):
    """
    Handles the application of a PagerDuty notification target.
    """
    ctx = cfg.get_current_context()
    metadata = resrc_data[lib.METADATA_FIELD]
    spec = resrc_data[lib.SPEC_FIELD]
    uid = metadata.get("uid")
    kwargs = {
        "routing_key": spec[lib.TGT_ROUTING_KEY_FIELD],
    }
    if lib.TGT_DESCRIPTION_FIELD in metadata:
        kwargs["description"] = metadata[lib.TGT_DESCRIPTION_FIELD]
    else:
        kwargs["clear_description"] = True
    if lib.METADATA_TAGS_FIELD in metadata:
        kwargs["tags"] = metadata[lib.METADATA_TAGS_FIELD]
    else:
        kwargs["clear_tags"] = True
    if uid is None:
        uid = create_pagerduty_notification_target(
            *ctx.get_api_data(),
            name=metadata[lib.METADATA_NAME_FIELD],
            **kwargs,
        )
        cli.try_log(f"Successfully created pagerduty notification target {uid}")
    else:
        update_pagerduty_notification_target(
            *ctx.get_api_data(),
            uid=uid,
            name=metadata[lib.METADATA_NAME_FIELD],
            **kwargs,
        )
        if from_edit:
            cli.try_log(f"Successfully edited pagerduty notification target {uid}")
        else:
            cli.try_log(f"Successfully created pagerduty notification target {uid}")
    return uid


def handle_apply_slack_notification_target(resrc_data: Dict, from_edit: bool = False):
    """
    Handles the application of a Slack notification target.
    """
    ctx = cfg.get_current_context()
    metadata = resrc_data[lib.METADATA_FIELD]
    spec = resrc_data[lib.SPEC_FIELD]
    uid = metadata.get("uid")
    kwargs = {
        "url": spec[lib.TGT_SLACK_URL],
    }
    if lib.TGT_DESCRIPTION_FIELD in metadata:
        kwargs["description"] = metadata[lib.TGT_DESCRIPTION_FIELD]
    else:
        kwargs["clear_description"] = True
    if lib.METADATA_TAGS_FIELD in metadata:
        kwargs["tags"] = metadata[lib.METADATA_TAGS_FIELD]
    else:
        kwargs["clear_tags"] = True
    if uid is None:
        uid = create_slack_notification_target(
            *ctx.get_api_data(),
            name=metadata[lib.METADATA_NAME_FIELD],
            **kwargs,
        )
        cli.try_log(f"Successfully created slack notification target {uid}")
    else:
        update_slack_notification_target(
            *ctx.get_api_data(),
            uid,
            name=metadata[lib.METADATA_NAME_FIELD],
            **kwargs,
        )
        if from_edit:
            cli.try_log(f"Successfully edited slack notification target {uid}")
        else:
            cli.try_log(f"Successfully created slack notification target {uid}")
    return uid


def handle_apply_email_notification_target(resrc_data: Dict, from_edit: bool = False):
    """
    Handles the application of an email notification target.
    """
    ctx = cfg.get_current_context()
    metadata = resrc_data[lib.METADATA_FIELD]
    spec = resrc_data[lib.SPEC_FIELD]
    uid = metadata.get("uid")
    kwargs = {
        "emails": spec[lib.TGT_EMAILS_FIELD],
    }
    if lib.TGT_DESCRIPTION_FIELD in metadata:
        kwargs["description"] = metadata[lib.TGT_DESCRIPTION_FIELD]
    else:
        kwargs["clear_description"] = True
    if lib.METADATA_TAGS_FIELD in metadata:
        kwargs["tags"] = metadata[lib.METADATA_TAGS_FIELD]
    else:
        kwargs["clear_tags"] = True
    if uid is None:
        uid = create_email_notification_target(
            *ctx.get_api_data(),
            name=metadata[lib.METADATA_NAME_FIELD],
            **kwargs,
        )
        cli.try_log(f"Successfully created email notification target {uid}")
    else:
        update_email_notification_target(
            *ctx.get_api_data(),
            uid,
            name=metadata[lib.METADATA_NAME_FIELD],
            **kwargs,
        )
        if from_edit:
            cli.try_log(f"Successfully edited email notification target {uid}")
        else:
            cli.try_log(f"Successfully created email notification target {uid}")
    return uid


def handle_apply_webhook_notification_target(resrc_data: Dict, from_edit: bool = False):
    """
    Handles the application of a webhook notification target.
    """
    ctx = cfg.get_current_context()
    metadata = resrc_data[lib.METADATA_FIELD]
    spec = resrc_data[lib.SPEC_FIELD]
    uid = metadata.get("uid")
    kwargs = {
        "url": spec[lib.TGT_WEBHOOK_URL],
    }
    if lib.TGT_DESCRIPTION_FIELD in metadata:
        kwargs["description"] = metadata[lib.TGT_DESCRIPTION_FIELD]
    else:
        kwargs["clear_description"] = True
    if lib.METADATA_TAGS_FIELD in metadata:
        kwargs["tags"] = metadata[lib.METADATA_TAGS_FIELD]
    else:
        kwargs["clear_tags"] = True
    if uid is None:
        uid = create_webhook_notification_target(
            *ctx.get_api_data(),
            name=metadata[lib.METADATA_NAME_FIELD],
            **kwargs,
        )
        cli.try_log(f"Successfully created webhook notification target {uid}")
    else:
        update_webhook_notification_target(
            *ctx.get_api_data(),
            uid,
            name=metadata[lib.METADATA_NAME_FIELD],
            **kwargs,
        )
        if from_edit:
            cli.try_log(f"Successfully edited webhook notification target {uid}")
        else:
            cli.try_log(f"Successfully created webhook notification target {uid}")
    return uid
