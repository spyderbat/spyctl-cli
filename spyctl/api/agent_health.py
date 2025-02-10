"""Handles agent health API requests."""

from typing import Dict, List, Tuple

from requests import Response

from spyctl.api.primitives import delete, get, post, put


def get_agent_health_notification_settings(
    api_url, api_key, org_uid, ahn_uid
) -> Dict:
    """
    Gets the agent health for the specified organization.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/agent_health_notification_settings/{ahn_uid}"
    resp = get(url, api_key)
    ahn = resp.json()["agent_health_notification_settings"]
    return ahn


def get_agent_health_notification_settings_list(
    api_url, api_key, org_uid, **query_params
) -> Tuple[List[Dict], int]:
    """
    Gets the list of agent health notification settings for the specified organization.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        **query_params: Keyword query parameters.

    Query Parameters:
        action_taken_equals (str): Filter by the action taken on the flag(s). One of [insert|update|delete|enable|disable].
        from_history (bool): Retrieves historical custom flags data.
        latest_version (bool): Filter by the latest version of the flag.
        name_contains (str): Filter by the name.
        name_equals (str): Filter by the name.
        name_or_uid_contains (str): Filter by the name or UID.
        name_or_uid_equals (str): Filter by the name or UID.
        page (int): Page number to return.
        page_size (int): Number of notification settings to return per page.
        reversed (bool): Whether to return the results in reverse order.
        scope_query_contains (str): Filter by the scope query.
        scope_query_equals (str): Filter by the scope query.
        sort_by (str): Sort the results by a field.
        uid_equals (str): Filter by the notification settings UID.
        version (int): Filter by the flag version.

    Returns:
        Tuple[List[Dict], int]: A list of agent health notification settings and the total number of pages.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/agent_health_notification_settings/"
    resp = get(url, api_key, query_params)
    ahn_list = resp.json()["agent_health_notifications_settings_list"]
    total_pages = resp.json()["total_pages"]
    return ahn_list, total_pages


def post_new_agent_health_notification_settings(
    api_url, api_key, org_uid, **req_body
) -> str:
    """
    Creates an agent health notification for the specified organization.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        **req_body: The request body containing the notification settings.

    Request Body:
        description (str): Description of the notification settings (max: 500 chars).
        name (str): Name of the notification settings (1 to 128 chars).
        notification_settings (dict): The notification settings for different agent states.
            agent_healthy (dict): Settings for agent healthy notifications.
                aggregate (bool): Aggregate notifications.
                aggregate_by (list): Fields to aggregate by.
                aggregate_seconds (int): Aggregation window in seconds.
                cooldown (int): Cooldown period in seconds.
                cooldown_by (list): Fields to cooldown by.
                is_enabled (bool): Whether the notification is enabled.
                target_map (dict): Map of notification targets to optional templates.
                uid (str): Auto-generated UID.
            agent_offline (dict): Settings for agent offline notifications.
                aggregate (bool): Aggregate notifications.
                aggregate_by (list): Fields to aggregate by.
                aggregate_seconds (int): Aggregation window in seconds.
                cooldown (int): Cooldown period in seconds.
                cooldown_by (list): Fields to cooldown by.
                is_enabled (bool): Whether the notification is enabled.
                target_map (dict): Map of notification targets to optional templates.
                uid (str): Auto-generated UID.
            agent_online (dict): Settings for agent online notifications.
                aggregate (bool): Aggregate notifications.
                aggregate_by (list): Fields to aggregate by.
                aggregate_seconds (int): Aggregation window in seconds.
                cooldown (int): Cooldown period in seconds.
                cooldown_by (list): Fields to cooldown by.
                is_enabled (bool): Whether the notification is enabled.
                target_map (dict): Map of notification targets to optional templates.
                uid (str): Auto-generated UID.
            agent_unhealthy (dict): Settings for agent unhealthy notifications.
                aggregate (bool): Aggregate notifications.
                aggregate_by (list): Fields to aggregate by.
                aggregate_seconds (int): Aggregation window in seconds.
                cooldown (int): Cooldown period in seconds.
                cooldown_by (list): Fields to cooldown by.
                is_enabled (bool): Whether the notification is enabled.
                target_map (dict): Map of notification targets to optional templates.
                uid (str): Auto-generated UID.
        scope_query (str): Scope query (max: 65535 chars).

    Returns:
        str: The UID of the created agent health notification settings.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/agent_health_notification_settings/"
    resp = post(url, req_body, api_key)
    ahn_uid = resp.json()["uid"]
    return ahn_uid


def put_update_agent_health_notification_settings(
    api_url, api_key, org_uid, ahn_uid, **req_body
) -> Dict:
    """
    Updates the agent health notification settings for the specified organization.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        ahn_uid (str): The unique identifier of the agent health notification settings to be updated.
        **req_body: The updated agent health notification settings data.

    Request Body:
        description (str): Description of the notification settings (max: 500 chars).
        name (str): Name of the notification settings (1 to 128 chars).
        notification_settings (dict): Notification settings for different agent states.
            agent_healthy (dict): Settings for agent healthy notifications.
                aggregate (bool): Aggregate notifications.
                aggregate_by (list): Fields to aggregate by.
                aggregate_seconds (int): Aggregation window in seconds.
                cooldown (int): Cooldown period in seconds.
                cooldown_by (list): Fields to cooldown by.
                is_enabled (bool): Whether the notification is enabled.
                target_map (dict): Map of notification targets to optional templates.
                uid (str): Auto-generated UID.
            agent_offline (dict): Settings for agent offline notifications.
                aggregate (bool): Aggregate notifications.
                aggregate_by (list): Fields to aggregate by.
                aggregate_seconds (int): Aggregation window in seconds.
                cooldown (int): Cooldown period in seconds.
                cooldown_by (list): Fields to cooldown by.
                is_enabled (bool): Whether the notification is enabled.
                target_map (dict): Map of notification targets to optional templates.
                uid (str): Auto-generated UID.
            agent_online (dict): Settings for agent online notifications.
                aggregate (bool): Aggregate notifications.
                aggregate_by (list): Fields to aggregate by.
                aggregate_seconds (int): Aggregation window in seconds.
                cooldown (int): Cooldown period in seconds.
                cooldown_by (list): Fields to cooldown by.
                is_enabled (bool): Whether the notification is enabled.
                target_map (dict): Map of notification targets to optional templates.
                uid (str): Auto-generated UID.
            agent_unhealthy (dict): Settings for agent unhealthy notifications.
                aggregate (bool): Aggregate notifications.
                aggregate_by (list): Fields to aggregate by.
                aggregate_seconds (int): Aggregation window in seconds.
                cooldown (int): Cooldown period in seconds.
                cooldown_by (list): Fields to cooldown by.
                is_enabled (bool): Whether the notification is enabled.
                target_map (dict): Map of notification targets to optional templates.
                uid (str): Auto-generated UID.
        scope_query (str): Scope query (1 to 65535 chars).

    Returns:
        Dict: The updated agent health notification settings data.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/agent_health_notification_settings/{ahn_uid}"
    resp = put(url, req_body, api_key)
    return resp.json()


def delete_agent_health_notification_settings(
    api_url, api_key, org_uid, ahn_uid
) -> Response:
    """
    Deletes the agent health notification settings for the specified organization.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/agent_health_notification_settings/{ahn_uid}"
    return delete(url, api_key)
