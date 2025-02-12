"""Contains functions specific to the agent health notification resource."""

from typing import Dict

import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.agent_health import (
    post_new_agent_health_notification_settings,
    put_update_agent_health_notification_settings,
)


def handle_apply_agent_health_notification(data: Dict, from_edit: bool = False):
    """
    Handles the application of an agent health notification.
    """
    ctx = cfg.get_current_context()
    metadata = data[lib.METADATA_FIELD]
    spec = data[lib.SPEC_FIELD]
    uid = metadata.get("uid")
    kwargs = {
        "name": metadata.get("name"),
        "description": metadata.get("description"),
        "scope_query": spec.get("scope_query"),
        "notification_settings": spec.get("notification_settings"),
    }
    if uid is None:
        uid = post_new_agent_health_notification_settings(
            *ctx.get_api_data(),
            **kwargs,
        )
        cli.try_log(f"Successfully created agent health notification {uid}")
    else:
        put_update_agent_health_notification_settings(
            *ctx.get_api_data(),
            ahn_uid=uid,
            **kwargs,
        )
        if from_edit:
            cli.try_log(f"Successfully edited agent health notification {uid}")
        else:
            cli.try_log(f"Successfully created agent health notification {uid}")
    return uid
