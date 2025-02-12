"""Contains functions specific to the notification_template resource."""

from typing import Dict, List

from tabulate import tabulate

import spyctl.spyctl_lib as lib
from spyctl import schemas_v2 as schemas


def data_to_yaml(data: Dict) -> Dict:
    """
    Convert data to a YAML representation of a NotificationTemplateModel.

    Args:
        data (Dict): The data to be converted.

    Returns:
        Dict: The YAML representation of a NotificationTemplateModel.
    """
    metadata = schemas.NotificationTemplateMetadataModel(
        name=data["name"],
        type=data["template_type"],
        creationTimestamp=data.get("valid_from"),
        createdBy=data.get("created_by"),
        lastUsedTimestamp=data.get("last_used"),
        uid=data.get("uid"),
        tags=data.get("tags"),
        description=data.get("description"),
    )
    spec = data.get("template_data")
    model = schemas.NotificationTemplateModel(
        apiVersion=lib.API_VERSION,
        kind=lib.TEMPLATE_KIND,
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


def summary_output(templates: List[Dict], total_pages: int, current_page: int = 0):
    """
    Print a summary of notification templates.

    Args:
        templates (List[Dict]): The notification templates to be summarized.
    """
    data = []
    for template in templates:
        description = lib.limit_line_length(template.get("description", ""))
        data.append(
            [
                template["name"],
                template["uid"],
                template["template_type"],
                lib.epoch_to_zulu(template["valid_from"]),
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


def wide_output(templates: List[Dict], total_pages: int, current_page: int = 0):
    """
    Print a wide summary of notification templates.
    """
    data = []
    for template in templates:
        description = lib.limit_line_length(template.get("description", ""))
        data.append(
            [
                template["name"],
                template["uid"],
                template["template_type"],
                lib.epoch_to_zulu(template["valid_from"]),
                description,
                template["created_by"],
            ]
        )
    rv = [f"Page {min(current_page, total_pages)}/{total_pages}"]
    rv.append(tabulate(data, headers=WIDE_HEADERS, tablefmt="plain"))
    return "\n".join(rv)
