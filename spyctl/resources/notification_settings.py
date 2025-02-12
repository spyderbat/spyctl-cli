"""Contains functions specific to notification_settings."""

from typing import Dict, List

from tabulate import tabulate

import spyctl.spyctl_lib as lib

SUMMARY_HEADERS = [
    "UID",
    "REF_UID",
    "FEATURE",
    "TRIGGER",
    "IS_ENABLED",
    "TARGETS",
    "CREATION_TIME",
]


def summary_output(notifications: List[Dict], total_pages: int, current_page: int = 0):
    """
    Print a summary of notification settings.

    Args:
        notifications (List[Dict]): The notification settings to be summarized.
    """
    data = []
    for notification in notifications:
        data.append(
            [
                notification["uid"],
                notification["ref_uid"],
                notification["feature"],
                notification["trigger"],
                notification["is_enabled"],
                (len(notification["target_map"]) if notification["target_map"] else 0),
                lib.epoch_to_zulu(notification["valid_from"]),
            ]
        )
    if len(notifications) == 0:
        current_page = 0
        total_pages = 0
    else:
        current_page = min(current_page, total_pages)
    rv = [f"Page {current_page}/{total_pages}"]
    rv.append(tabulate(data, headers=SUMMARY_HEADERS, tablefmt="plain"))
    return "\n".join(rv)
