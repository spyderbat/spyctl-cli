"""Configure notifications for a saved query."""

import click

from spyctl import spyctl_lib as lib
from spyctl.api.saved_queries import get_saved_queries
from spyctl.api.notifications import put_set_notification_settings
from spyctl.commands.notifications.configure.shared_options import (
    notification_settings_options,
    get_target_map,
)
from spyctl.config import configs as cfg


@click.command("saved-query")
@click.help_option("-h", "--help", hidden=True)
@notification_settings_options
@click.argument("name_or_uid", type=str)
def configure_saved_query(name_or_uid, **kwargs):
    """Configure notifications for a saved query."""
    ctx = cfg.get_current_context()
    is_enabled = not kwargs.pop("is_disabled", False)
    target_map = get_target_map(**kwargs)
    notification_settings = {**kwargs}
    notification_settings["is_enabled"] = is_enabled
    notification_settings["target_map"] = target_map if target_map else None

    sq_params = {
        "name_or_uid_contains": name_or_uid,
    }
    saved_queries, _ = get_saved_queries(*ctx.get_api_data(), **sq_params)
    if not saved_queries:
        lib.err_exit(f"Saved query '{name_or_uid}' not found")
    if len(saved_queries) > 1:
        lib.err_exit(
            f"Saved query '{name_or_uid}' is ambiguous, use full name or UID"
        )
    saved_query = saved_queries[0]
    put_set_notification_settings(
        *ctx.get_api_data(), saved_query["uid"], notification_settings
    )
    if not target_map:
        lib.try_log(
            f"No notification targets configured for saved query '{name_or_uid}'"
        )
        lib.try_log(
            f"Use 'spyctl edit saved-query \"{name_or_uid}\"' to configure"
        )
        lib.try_log(
            "Or re-run this command with --targets and/or --target-map options"
        )
    lib.try_log(
        f"Notification settings for saved query '{name_or_uid}' updated"
    )
