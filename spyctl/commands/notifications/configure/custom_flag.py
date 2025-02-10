"""Configure notifications for a custom flag."""

import click

from spyctl import spyctl_lib as lib
from spyctl.api.custom_flags import get_custom_flags
from spyctl.api.notifications import put_set_notification_settings
from spyctl.commands.notifications.configure.shared_options import (
    notification_settings_options,
    get_target_map,
)
from spyctl.config import configs as cfg


@click.command("custom-flag")
@click.help_option("-h", "--help", hidden=True)
@notification_settings_options
@click.argument("name_or_uid", type=str)
def configure_custom_flag(name_or_uid, **kwargs):
    """Configure notifications for a custom flag."""
    ctx = cfg.get_current_context()
    is_enabled = not kwargs.pop("is_disabled", False)
    target_map = get_target_map(**kwargs)
    notification_settings = {**kwargs}
    notification_settings["is_enabled"] = is_enabled
    notification_settings["target_map"] = target_map if target_map else None

    cf_params = {
        "name_or_uid_contains": name_or_uid,
    }
    custom_flags, _ = get_custom_flags(*ctx.get_api_data(), **cf_params)
    if not custom_flags:
        lib.err_exit(f"Custom flag '{name_or_uid}' not found")
    if len(custom_flags) > 1:
        lib.err_exit(
            f"Custom flag '{name_or_uid}' is ambiguous, use full name or UID"
        )
    custom_flag = custom_flags[0]
    put_set_notification_settings(
        *ctx.get_api_data(), custom_flag["uid"], notification_settings
    )
    if not target_map:
        lib.try_log(
            f"No notification targets configured for custom flag '{name_or_uid}'"
        )
        lib.try_log(
            f"Use 'spyctl edit custom-flag \"{name_or_uid}\"' to configure"
        )
        lib.try_log(
            "Or re-run this command with --targets and/or --target-map options"
        )
    lib.try_log(
        f"Notification settings for custom flag '{name_or_uid}' updated"
    )
