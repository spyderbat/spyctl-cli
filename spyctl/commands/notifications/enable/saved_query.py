"""Enable notifications for a saved query."""

import click

from spyctl import spyctl_lib as lib
from spyctl.api.notifications import put_enable_notification_settings
from spyctl.api.saved_queries import get_saved_queries
from spyctl.config import configs as cfg


@click.command("saved-query")
@click.help_option("-h", "--help", hidden=True)
@click.argument("name_or_uid", type=str)
def enable_saved_query(name_or_uid):
    """Enable notifications for a saved query."""
    ctx = cfg.get_current_context()
    sq_params = {
        "name_or_uid_contains": name_or_uid,
    }
    saved_queries, _ = get_saved_queries(*ctx.get_api_data(), **sq_params)
    if not saved_queries:
        lib.err_exit(f"Saved query '{name_or_uid}' not found")
        return
    if len(saved_queries) > 1:
        lib.err_exit(f"Saved query '{name_or_uid}' is ambiguous, use full name or UID")
    saved_query = saved_queries[0]
    put_enable_notification_settings(*ctx.get_api_data(), saved_query["uid"])
    lib.try_log(f"Notifications for saved query '{name_or_uid}' enabled")
