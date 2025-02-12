"""Contains functions specific to the notification_target resource."""

from typing import Dict, List

from tabulate import tabulate

import spyctl.spyctl_lib as lib
from spyctl import schemas_v2 as schemas


def data_to_yaml(data: Dict) -> Dict:
    """
    Convert data to a YAML representation of a NotificationTargetModel.

    Args:
        data (Dict): The data to be converted.

    Returns:
        Dict: The YAML representation of a NotificationTargetModel.
    """
    metadata = schemas.NotifTgtMetadataModel(
        name=data["name"],
        type=data["target_type"],
        creationTimestamp=data.get("valid_from"),
        createdBy=data.get("created_by"),
        lastUsedTimestamp=data.get("last_used"),
        uid=data.get("uid"),
        tags=data.get("tags"),
        description=data.get("description"),
    )
    spec = data.get("target_data")  # Target data may be sensitive and not returned
    if not spec:
        spec = None
    model = schemas.NotificationTgtResourceModel(
        apiVersion=lib.API_VERSION,
        kind=lib.TARGET_KIND,
        metadata=metadata,
        spec=spec,
    )
    return model.model_dump(by_alias=True, exclude_unset=True, exclude_none=True)


SUMMARY_HEADERS = [
    "NAME",
    "UID",
    "TYPE",
    "CREATED",
    "DESCRIPTION",
]


def summary_output(targets: List[Dict], total_pages: int, current_page: int = 0):
    """
    Print a summary of notification targets.

    Args:
        targets (List[Dict]): The notification targets to be summarized.
    """
    data = []
    for target in targets:
        description = lib.limit_line_length(target.get("description", ""))
        data.append(
            [
                target["name"],
                target["uid"],
                target["target_type"],
                lib.epoch_to_zulu(target["valid_from"]),
                description,
            ]
        )
    rv = [f"Page {min(current_page, total_pages)}/{total_pages}"]
    rv.append(tabulate(data, headers=SUMMARY_HEADERS, tablefmt="plain"))
    return "\n".join(rv)


WIDE_HEADERS = [
    "NAME",
    "UID",
    "TYPE",
    "CREATED",
    "DESCRIPTION",
    "CREATED BY",
]


def wide_output(targets: List[Dict], total_pages: int, current_page: int = 0):
    """
    Print a wide summary of notification targets.

    Args:
        targets (List[Dict]): The notification targets to be summarized.
    """
    data = []
    for target in targets:
        description = lib.limit_line_length(target.get("description", ""))
        data.append(
            [
                target["name"],
                target["uid"],
                target["target_type"],
                lib.epoch_to_zulu(target["valid_from"]),
                description,
                target["created_by"],
            ]
        )
    rv = [f"Page {min(current_page, total_pages)}/{total_pages}"]
    rv.append(tabulate(data, headers=WIDE_HEADERS, tablefmt="plain"))
    return "\n".join(rv)
