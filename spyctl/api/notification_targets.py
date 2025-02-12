"""Handles the API calls for notification targets."""

from spyctl.api.primitives import delete, get, post, put


def get_notification_target(
    api_url,
    api_key,
    org_uid,
    notification_target_uid,
    exclude_target_data=False,
):
    """Gets a notification target from the specified organization."""
    url = f"{api_url}/api/v1/org/{org_uid}/notificationtarget/{notification_target_uid}"
    resp = get(url, api_key, params={"include_target_data": not exclude_target_data})
    return resp.json()["notification_target"]


def get_notification_targets(api_url, api_key, org_uid, **query_params):
    """
    Gets all notification targets from the specified organization.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        **query_params: Keyword query parameters.

    Query Parameters:
        action_taken_equals (str): Filter by the action taken on the notification target(s). Pulls from the
            history database table. One of [insert|update|delete]
        from_history (bool): Retrieve from history.
        include_target_data (bool): Include the potentially sensitive target data in the response. This could
            be emails, webhooks, keys, etc. Increased permissions are required to view this data.
        latest_version (bool): Retrieve the latest version.
        name_contains (str): Filter by name containing this string.
        name_equals (str): Filter by exact name match.
        name_or_uid_contains (str): Filter by name or UID containing this string.
        name_or_uid_equals (str): Filter by exact name or UID match.
        page (int): Page number for pagination.
        page_size (int): Number of items per page.
        reversed (bool): Reverse the order of results.
        sort_by (str): Sort the results by a field. One of [name|description|create_time|last_updated|type]
        tags_contain (List[str]): Filter by tags containing these values.
        type_equals (str): Filter by exact type match.
        type_not_equals (str): Filter by type not matching this value.
        uid_equals (str): Filter by exact UID match.
        uid_in_list (List[str]): Filter by UIDs in this list.
        version (int): Retrieve a specific version.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/notificationtarget/"
    resp = get(url, api_key, params=query_params)
    jo = resp.json()
    nts = jo["notification_targets"]
    total_pages = jo["total_pages"]
    return nts, total_pages


def create_email_notification_target(
    api_url: str, api_key: str, org_uid: str, name: str, **kwargs
) -> str:
    """
    Creates an email notification target and returns its UID.

    This function creates a new email notification target for an organization
    and returns the unique identifier of the created target.
    It requires the action 'org:CreateNotificationTarget' on the organization.

    Args:
        api_url (str): The base URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        name (str): Name of the notification target.

    Keyword Args:
        emails (List[str], optional): List of email addresses for the notification target. Defaults to None.
        description (str, optional): Description of the notification target. Max 500 characters. Defaults to "".
        tags (List[str], optional): List of tags for the notification target. Defaults to None.

    Returns:
        str: The UID of the created notification target.

    Raises:
        HTTPError: If the request fails.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/notificationtarget/email/"
    payload = {
        "name": name,
        "emails": kwargs.get("emails", []),
        "description": kwargs.get("description", ""),
        "tags": kwargs.get("tags", []),
    }
    response = post(url, payload, api_key)
    return response.json()["uid"]


def create_slack_notification_target(
    api_url: str, api_key: str, org_uid: str, name: str, **kwargs
) -> str:
    """
    Creates a Slack notification target and returns its UID.

    This function creates a new Slack notification target for an organization
    and returns the unique identifier of the created target.
    It requires the action 'org:CreateNotificationTarget' on the organization.

    Args:
        api_url (str): The base URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        name (str): Name of the notification target.

    Keyword Args:
        url (str): URL to send the notification to.
        description (str, optional): Description of the notification target. Max 500 characters. Defaults to "".
        tags (List[str], optional): List of tags for the notification target. Defaults to None.

    Returns:
        str: The UID of the created notification target.
    """
    endpoint = f"{api_url}/api/v1/org/{org_uid}/notificationtarget/slack/"
    payload = {
        "name": name,
        "url": kwargs.get("url"),
        "description": kwargs.get("description", ""),
        "tags": kwargs.get("tags", []),
    }
    response = post(endpoint, payload, api_key)
    return response.json()["uid"]


def create_webhook_notification_target(
    api_url: str, api_key: str, org_uid: str, name: str, **kwargs
) -> str:
    """
    Creates a webhook notification target and returns its UID.

    This function creates a new webhook notification target for an organization
    and returns the unique identifier of the created target.
    It requires the action 'org:CreateNotificationTarget' on the organization.

    Args:
        api_url (str): The base URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        name (str): Name of the notification target.

    Keyword Args:
        url (str): URL to send the webhook to.
        description (str, optional): Description of the notification target. Max 500 characters. Defaults to "".
        tags (List[str], optional): List of tags for the notification target. Defaults to None.
        user_name (str, optional): Optional username for basic auth.
        password (str, optional): Optional password for basic auth.

    Returns:
        str: The UID of the created notification target.
    """
    endpoint = f"{api_url}/api/v1/org/{org_uid}/notificationtarget/webhook/"
    payload = {
        "name": name,
        "url": kwargs.get("url"),
        "description": kwargs.get("description", ""),
        "tags": kwargs.get("tags", []),
        "user_name": kwargs.get("user_name"),
        "password": kwargs.get("password"),
    }
    response = post(endpoint, payload, api_key)
    return response.json()["uid"]


def create_pagerduty_notification_target(
    api_url: str, api_key: str, org_uid: str, name: str, **kwargs
) -> str:
    """
    Creates a PagerDuty notification target and returns its UID.

    This function creates a new PagerDuty notification target for an organization
    and returns the unique identifier of the created target.
    It requires the action 'org:CreateNotificationTarget' on the organization.

    Args:
        api_url (str): The base URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        name (str): Name of the notification target.

    Keyword Args:
        routing_key (str): Routing key for the PagerDuty service.
        description (str, optional): Description of the notification target. Max 500 characters. Defaults to "".
        tags (List[str], optional): List of tags for the notification target. Defaults to None.

    Returns:
        str: The UID of the created notification target.
    """
    endpoint = f"{api_url}/api/v1/org/{org_uid}/notificationtarget/pagerduty/"
    payload = {
        "name": name,
        "routing_key": kwargs.get("routing_key"),
        "description": kwargs.get("description", ""),
        "tags": kwargs.get("tags", []),
    }
    response = post(endpoint, payload, api_key)
    return response.json()["uid"]


def delete_notification_target(
    api_url: str, api_key: str, org_uid: str, notification_target_uid: str
) -> None:
    """
    Deletes a notification target from the specified organization.

    This function deletes a specific notification target for an organization.
    It requires the action 'org:DeleteNotificationTarget' on the organization.

    Args:
        api_url (str): The base URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        notification_target_uid (str): The unique identifier of the notification target to be deleted.

    Returns:
        None
    """
    endpoint = (
        f"{api_url}/api/v1/org/{org_uid}/notificationtarget/{notification_target_uid}"
    )
    delete(endpoint, api_key)


def update_email_notification_target(
    api_url, api_key, org_uid, notification_target_uid, **kwargs
):
    """
    Updates an email notification target.

    This function updates the specified email notification target for an organization.
    It requires the action 'org:UpdateNotificationTarget' on the organization.

    Args:
        api_url (str): The base URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        notification_target_uid (str): The unique identifier of the notification target to be updated.

    Keyword Args:
        name (str, optional): New name for the notification target.
        emails (List[str], optional): List of email addresses for the notification target.
        description (str, optional): New description for the notification target. Max 500 characters.
        tags (List[str], optional): New list of tags for the notification target.
        clear_description (bool, optional): If True, clears the existing description. Defaults to False.
        clear_tags (bool, optional): If True, clears the existing tags. Defaults to False.

    Returns:
        dict: The updated notification target information.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/notificationtarget/email/{notification_target_uid}"
    payload = {
        "name": kwargs.get("name"),
        "emails": kwargs.get("emails"),
        "description": kwargs.get("description"),
        "tags": kwargs.get("tags"),
    }
    query_params = {
        "clear_description": kwargs.get("clear_description", False),
        "clear_tags": kwargs.get("clear_tags", False),
    }
    resp = put(url, payload, api_key, query_params)
    return resp.json()["notification_target"]


def update_slack_notification_target(
    api_url, api_key, org_uid, notification_target_uid, **kwargs
):
    """
    Updates a Slack notification target.

    This function updates the specified Slack notification target for an organization.
    It requires the action 'org:UpdateNotificationTarget' on the organization.

    Args:
        api_url (str): The base URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        notification_target_uid (str): The unique identifier of the notification target to be updated.

    Keyword Args:
        name (str, optional): New name for the notification target.
        url (str, optional): New URL for the notification target.
        description (str, optional): New description for the notification target. Max 500 characters.
        tags (List[str], optional): New list of tags for the notification target.
        clear_description (bool, optional): If True, clears the existing description. Defaults to False.
        clear_tags (bool, optional): If True, clears the existing tags. Defaults to False.

    Returns:
        dict: The updated notification target information.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/notificationtarget/slack/{notification_target_uid}"
    payload = {
        "name": kwargs.get("name"),
        "url": kwargs.get("url"),
        "description": kwargs.get("description"),
        "tags": kwargs.get("tags"),
    }
    query_params = {
        "clear_description": kwargs.get("clear_description", False),
        "clear_tags": kwargs.get("clear_tags", False),
    }
    resp = put(url, payload, api_key, query_params)
    return resp.json()["notification_target"]


def update_webhook_notification_target(
    api_url, api_key, org_uid, notification_target_uid, **kwargs
):
    """
    Updates a webhook notification target.

    This function updates the specified webhook notification target for an organization.
    It requires the action 'org:UpdateNotificationTarget' on the organization.

    Args:
        api_url (str): The base URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        notification_target_uid (str): The unique identifier of the notification target to be updated.

    Keyword Args:
        name (str, optional): New name for the notification target.
        url (str, optional): New URL for the webhook.
        description (str, optional): New description for the notification target. Max 500 characters.
        tags (List[str], optional): New list of tags for the notification target.
        clear_description (bool, optional): If True, clears the existing description. Defaults to False.
        clear_tags (bool, optional): If True, clears the existing tags. Defaults to False.

    Returns:
        dict: The updated notification target information.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/notificationtarget/webhook/{notification_target_uid}"
    payload = {
        "name": kwargs.get("name"),
        "url": kwargs.get("url"),
        "description": kwargs.get("description"),
        "tags": kwargs.get("tags"),
    }
    query_params = {
        "clear_description": kwargs.get("clear_description", False),
        "clear_tags": kwargs.get("clear_tags", False),
    }
    resp = put(url, payload, api_key, query_params)
    return resp.json()["notification_target"]


def update_pagerduty_notification_target(
    api_url, api_key, org_uid, notification_target_uid, **kwargs
):
    """
    Updates a PagerDuty notification target.

    This function updates the specified PagerDuty notification target for an organization.
    It requires the action 'org:UpdateNotificationTarget' on the organization.

    Args:
        api_url (str): The base URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        notification_target_uid (str): The unique identifier of the notification target to be updated.

    Keyword Args:
        name (str, optional): New name for the notification target.
        routing_key (str, optional): New routing key for the PagerDuty integration.
        description (str, optional): New description for the notification target. Max 500 characters.
        tags (List[str], optional): New list of tags for the notification target.
        clear_description (bool, optional): If True, clears the existing description. Defaults to False.
        clear_tags (bool, optional): If True, clears the existing tags. Defaults to False.

    Returns:
        dict: The updated notification target information.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/notificationtarget/pagerduty/{notification_target_uid}"
    payload = {
        "name": kwargs.get("name"),
        "routing_key": kwargs.get("routing_key"),
        "description": kwargs.get("description"),
        "tags": kwargs.get("tags"),
    }
    query_params = {
        "clear_description": kwargs.get("clear_description", False),
        "clear_tags": kwargs.get("clear_tags", False),
    }
    resp = put(url, payload, api_key, query_params)
    return resp.json()["notification_target"]
