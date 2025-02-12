"""Contains functions specific to the agent health notification settings resource."""

from typing import Dict, List

from tabulate import tabulate

import spyctl.schemas_v2 as schemas
import spyctl.spyctl_lib as lib


def data_to_yaml(data: Dict) -> Dict:
    """Convert data to a YAML representation of an AgentHealthNotificationSettingsModel."""
    metadata = schemas.AgentHealthNotificationMetadataModel(
        name=data["name"],
        uid=data.get("uid"),
        description=data.get("description"),
        create_time=data.get("valid_from"),
        last_updated=data.get("last_updated"),
        created_by=data.get("created_by"),
        last_updated_by=data.get("last_updated_by"),
        version=data.get("version"),
        action_taken=data.get("action_taken"),
    )
    spec = schemas.AgentHealthNotificationSpecModel(
        scope_query=data.get("scope_query"),
        notification_settings=data.get("notification_settings"),
    )
    model = schemas.AgentHealthNotificationModel(
        apiVersion=lib.API_VERSION,
        kind=lib.AGENT_HEALTH_NOTIFICATION_KIND,
        metadata=metadata,
        spec=spec,
    )
    return model.model_dump(exclude_unset=True, exclude_none=True, by_alias=True)


SUMMARY_HEADERS = [
    "NAME",
    "UID",
    "SCOPE",
    "DESCRIPTION",
    "VERSION",
    "AGE",
]

HISTORY_SUMMARY = [
    "NAME",
    "UID",
    "SCOPE",
    "DESCRIPTION",
    "VERSION",
    "AUDIT ACTION",
    "TIMESTAMP",
]


def summary_output(
    agent_health_notification_settings: List[Dict],
    total_pages: int,
    current_page: int = 0,
):
    """Generate a summary output for the given agent health notification settings."""
    data = []
    is_history = False
    if len(agent_health_notification_settings) > 0:
        is_history = (
            "action_taken" in agent_health_notification_settings[0]
            and agent_health_notification_settings[0]["action_taken"]
        )
        if is_history:
            for ahn in agent_health_notification_settings:
                description = lib.limit_line_length(ahn.get("description", ""))
                data.append(
                    [
                        ahn["name"],
                        ahn["uid"],
                        ahn["scope_query"],
                        description,
                        ahn["version"],
                        ahn["action_taken"],
                        lib.epoch_to_zulu(ahn["action_time"]),
                    ]
                )
        else:
            for ahn in agent_health_notification_settings:
                description = lib.limit_line_length(ahn.get("description", ""))
                data.append(
                    [
                        ahn["name"],
                        ahn["uid"],
                        ahn["scope_query"],
                        description,
                        ahn["version"],
                        lib.calc_age(ahn["valid_from"]),
                    ]
                )
    if len(agent_health_notification_settings) == 0:
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
    "SCOPE",
    "VERSION",
    "CREATE TIME",
    "CREATED BY",
    "LAST UPDATED",
    "LAST UPDATED BY",
]

WIDE_HISTORY_HEADERS = [
    "NAME",
    "UID",
    "DESCRIPTION",
    "SCOPE",
    "VERSION",
    "AUDIT ACTION",
    "TIMESTAMP",
    "ACTIONED BY",
    "CREATED BY",
]


def wide_output(
    agent_health_notification_settings: List[Dict],
    total_pages: int,
    current_page: int = 0,
):
    """Generate a wide output for the given agent health notification settings."""
    data = []
    is_history = False
    if len(agent_health_notification_settings) > 0:
        is_history = (
            "action_taken" in agent_health_notification_settings[0]
            and agent_health_notification_settings[0]["action_taken"]
        )
        if is_history:
            for ahn in agent_health_notification_settings:
                description = lib.limit_line_length(ahn.get("description", ""))
                data.append(
                    [
                        ahn["name"],
                        ahn["uid"],
                        description,
                        ahn["scope_query"],
                        ahn["version"],
                        ahn["action_taken"],
                        lib.epoch_to_zulu(ahn["action_time"]),
                        ahn["action_user"],
                        ahn["created_by"],
                    ]
                )
        else:
            for ahn in agent_health_notification_settings:
                description = lib.limit_line_length(ahn.get("description", ""))
                data.append(
                    [
                        ahn["name"],
                        ahn["uid"],
                        description,
                        ahn["scope_query"],
                        ahn["version"],
                        lib.epoch_to_zulu(ahn["valid_from"]),
                        ahn["created_by"],
                        lib.epoch_to_zulu(ahn["last_updated"]),
                        ahn["last_updated_by"],
                    ]
                )
    if len(agent_health_notification_settings) == 0:
        current_page = 0
        total_pages = 0
    else:
        current_page = min(current_page, total_pages)
    rv = [f"Page {current_page}/{total_pages}"]
    headers = WIDE_HISTORY_HEADERS if is_history else WIDE_HEADERS
    rv.append(tabulate(data, headers=headers, tablefmt="plain"))
    return "\n".join(rv)
