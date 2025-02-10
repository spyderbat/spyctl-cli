"""Enable notifications for a custom flag."""

import click

from spyctl import spyctl_lib as lib
from spyctl.api.custom_flags import get_custom_flags
from spyctl.api.notifications import put_enable_notification_settings
from spyctl.config import configs as cfg


@click.command("custom-flag")
@click.help_option("-h", "--help", hidden=True)
@click.argument(
    "name_or_uid",
    type=str,
)
def enable_custom_flag(name_or_uid):
    """Enable notifications for a custom flag."""
    ctx = cfg.get_current_context()
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
    put_enable_notification_settings(*ctx.get_api_data(), custom_flag["uid"])
    lib.try_log(f"Notifications for custom flag '{name_or_uid}' enabled")
