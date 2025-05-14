"""Contains functions specific to the custom_flag resource."""

from typing import Dict, List

from tabulate import tabulate

import spyctl.schemas_v2 as schemas
import spyctl.spyctl_lib as lib


def data_to_yaml(data: Dict) -> Dict:
    """
    Convert data to a YAML representation of a CustomFlagModel.

    Args:
        data (Dict): The data to be converted.

    Returns:
        Dict: The YAML representation of a CustomFlagModel.
    """
    metadata = schemas.CustomFlagMetadataModel(
        name=data["name"],
        creationTimestamp=data.get("valid_from"),
        createdBy=data.get("created_by"),
        lastUpdatedBy=data.get("last_updated_by"),
        lastUpdatedTimestamp=data.get("last_updated"),
        uid=data.get("uid"),
    )
    metadata.query_schema = data["schema"]
    if "saved_query_uid" in data:
        metadata.saved_query_uid = data["saved_query_uid"]
    # Revision is used when gathering historical data
    v = data.get("revision") or data.get("version")
    if v:
        metadata.version = v
    if data.get("tags"):
        metadata.tags = data["tags"]
    if data.get("action_taken"):
        metadata.action_taken = data["action_taken"]
    flag_settings = schemas.FlagSettingsField(
        type=data["type"],
        severity=data["severity"],
        description=data["description"],
    )
    if data.get("impact"):
        flag_settings.impact = data["impact"]
    if data.get("content"):
        flag_settings.content = data["content"]
    spec = schemas.CustomFlagSpecModel(
        flagSettings=flag_settings,
        query=data["query"],
        notification_settings=data.get("notification_settings"),
    )
    if "is_enabled" in data:
        spec.enabled = data["is_enabled"]
    elif "is_disabled" in data:
        spec.enabled = not data["is_disabled"]
    else:
        spec.enabled = True
    model = schemas.CustomFlagModel(
        apiVersion=lib.API_VERSION,
        kind=lib.CUSTOM_FLAG_KIND,
        metadata=metadata,
        spec=spec,
    )
    return model.model_dump(exclude_unset=True, exclude_none=True, by_alias=True)


SUMMARY_HEADERS = [
    "NAME",
    "UID",
    "DESCRIPTION",
    "SEVERITY",
    "SCHEMA",
    "STATUS",
    "AGE",
]

HISTORY_SUMMARY = [
    "NAME",
    "UID",
    "DESCRIPTION",
    "SEVERITY",
    "SCHEMA",
    "VERSION",
    "AUDIT ACTION",
    "TIMESTAMP",
]


def summary_output(custom_flags: List[Dict], total_pages: int, current_page: int = 0):
    """
    Generate a summary output for the given custom flags.

    Args:
        custom_flags (List[Dict]): A list of dictionaries representing custom
            flags.
        total_pages (int): The total number of pages.
        current_page (int, optional): The current page number. Defaults to 0.

    Returns:
        str: The summary output.

    """
    data = []
    is_history = False
    if len(custom_flags) > 0:
        is_history = "action_taken" in custom_flags[0]
        if is_history:
            for cf in custom_flags:
                description = lib.limit_line_length(cf.get("description", ""))
                data.append(
                    [
                        cf["name"],
                        cf["uid"],
                        description,
                        cf["severity"],
                        cf["schema"],
                        cf["revision"],
                        cf["action_taken"],
                        lib.epoch_to_zulu(cf["action_time"]),
                    ]
                )
        else:
            for cf in custom_flags:
                description = lib.limit_line_length(cf.get("description", ""))
                data.append(
                    [
                        cf["name"],
                        cf["uid"],
                        description,
                        cf["severity"],
                        cf["schema"],
                        "ENABLED" if cf["is_enabled"] else "DISABLED",
                        lib.calc_age(cf["valid_from"]),
                    ]
                )
    if len(custom_flags) == 0:
        current_page = 0
        total_pages = 0
    else:
        current_page = min(current_page, total_pages)
    rv = [f"Page {current_page}/{total_pages}"]
    headers = HISTORY_SUMMARY if is_history else SUMMARY_HEADERS
    rv.append(tabulate(data, headers=headers, tablefmt="plain"))
    return "\n".join(rv)


WIDE_HEADERS = [
    "NAME",
    "UID",
    "DESCRIPTION",
    "SEVERITY",
    "QUERY_UID",
    "SCHEMA",
    "QUERY",
    "STATUS",
    "CREATE TIME",
    "CREATED BY",
    "LAST UPDATED",
    "LAST UPDATED BY",
]

HISTORY_WIDE_HEADERS = [
    "NAME",
    "UID",
    "DESCRIPTION",
    "SEVERITY",
    "QUERY_UID",
    "SCHEMA",
    "QUERY",
    "VERSION",
    "AUDIT ACTION",
    "TIMESTAMP",
    "ACTIONED_BY",
    "CREATED BY",
]


def wide_output(custom_flags: List[Dict], total_pages: int, current_page: int = 0):
    """
    Generate a wide output for the given custom flags.

    Args:
        custom_flags (List[Dict]): A list of dictionaries representing custom
            flags.
        total_pages (int): The total number of pages.
        current_page (int, optional): The current page number. Defaults to 0.

    Returns:
        str: The wide output.

    """
    data = []
    is_history = False
    if len(custom_flags) > 0:
        is_history = "action_taken" in custom_flags[0]
        if is_history:
            for cf in custom_flags:
                description = lib.limit_line_length(cf.get("description", ""))
                data.append(
                    [
                        cf["name"],
                        cf["uid"],
                        description,
                        cf["severity"],
                        cf["saved_query_uid"],
                        cf["schema"],
                        cf["query"],
                        cf["revision"],
                        cf["action_taken"],
                        lib.epoch_to_zulu(cf["action_time"]),
                        cf["action_user"],
                        cf["created_by"],
                    ]
                )
        else:
            for cf in custom_flags:
                description = lib.limit_line_length(cf.get("description", ""))
                data.append(
                    [
                        cf["name"],
                        cf["uid"],
                        description,
                        cf["severity"],
                        cf["saved_query_uid"],
                        cf["schema"],
                        cf["query"],
                        "ENABLED" if cf["is_enabled"] else "DISABLED",
                        lib.calc_age(cf["valid_from"]),
                        cf["created_by"],
                        lib.epoch_to_zulu(cf["last_updated"]),
                        cf["last_updated_by"],
                    ]
                )
    if len(custom_flags) == 0:
        current_page = 0
        total_pages = 0
    else:
        current_page = min(current_page, total_pages)
    rv = [f"Page {current_page}/{total_pages}"]
    headers = HISTORY_WIDE_HEADERS if is_history else WIDE_HEADERS
    rv.append(tabulate(data, headers=headers, tablefmt="plain"))
    return "\n".join(rv)
