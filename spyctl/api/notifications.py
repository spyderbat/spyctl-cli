"""Handles the API calls for the notification policy."""

from typing import Dict

from spyctl.api.primitives import get, post, put


def post_test_notification(
    api_url, api_key, org_uid, target_uid, template_uid, record: Dict
):
    """
    Sends a test notification to a target.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        target_name (str): The name of the target to send the notification to.

    Returns:
        dict: The response from the API.

    """
    url = f"{api_url}/api/v1/org/{org_uid}/test_notification"
    data = {
        "target_uid": target_uid,
        "template_uid": template_uid,
        "record": record,
    }
    resp = post(url, data=data, key=api_key)
    return resp


def get_notification_settings(api_url, api_key, org_uid, ns_uid) -> Dict:
    """
    Load a specific notification settings object.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        ns_uid (str): The unique identifier of the notification settings to be loaded.

    Returns:
        Dict: The notification settings data.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/notification_settings/{ns_uid}"
    resp = get(url, api_key)
    jo = resp.json()
    settings = jo["notification_settings"]
    return settings


def get_notification_settings_list(api_url, api_key, org_uid, params: Dict) -> Dict:
    """
    List notification settings.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        params (Dict): Query parameters to filter the notification settings.

    Query Parameters:
        feature_equals (str): Filter by the feature.
        has_target_uid (str): Filter by whether the notification settings have a target UID.
        has_template_uid (str): Filter by whether the notification settings have a template UID.
        is_enabled (bool): Filter by whether the notification settings are enabled.
        name_or_uid_contains (str): Filter by the name or UID.
        name_or_uid_equals (str): Filter by the name or UID.
        page (int): Page number to return.
        page_size (int): Number of notification settings to return per page.
        refUID_equals (str): Filter by the reference UID.
        reversed (bool): Whether to return the results in reverse order.
        sort_by (str): Sort the results by a field.
        trigger_equals (str): Filter by the trigger.
        uid_equals (str): Filter by the notification settings UID.

    Returns:
        Dict: The notification settings data.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/notification_settings/"
    resp = get(url, api_key, params=params)
    jo = resp.json()
    settings = jo["notification_settings"]
    total_pages = jo["total_pages"]
    return settings, total_pages


def put_set_notification_settings(
    api_url, api_key, org_uid, ref_uid, notification_settings: Dict
) -> Dict:
    """
    Set notification settings for an object.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        ref_uid (str): The UID of the saved query or custom flag to set notification settings for.
        notification_settings (Dict): The notification settings data.

    Returns:
        Dict: The updated notification settings data.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/notification_settings/ref/{ref_uid}/set"
    resp = put(
        url,
        data={"notification_settings": notification_settings},
        key=api_key,
    )
    return resp.json()


def put_enable_notification_settings(api_url, api_key, org_uid, ref_uid) -> Dict:
    """
    Enable notification settings for an object.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        ref_uid (str): The UID of the saved query or custom flag to enable notifications for.

    Returns:
        Dict: The updated notification settings data.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/notification_settings/ref/{ref_uid}/enable"
    return put(url, data={}, key=api_key)


def put_disable_notification_settings(api_url, api_key, org_uid, ref_uid) -> Dict:
    """
    Disable notification settings for an object.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        ref_uid (str): The UID of the saved query or custom flag to disable notifications for.

    Returns:
        Dict: The updated notification settings data.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/notification_settings/ref/{ref_uid}/disable"
    return put(url, data={}, key=api_key)
