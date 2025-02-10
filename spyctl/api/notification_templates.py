"""Handles the API calls for notification templates."""

from spyctl.api.primitives import get, post, put, delete


def get_notification_template(api_url, api_key, org_uid, template_uid):
    """
    Load a specific notification template.

    Args:
        org_uid (str): The organization UID.
        template_uid (str): The notification template UID.

    Returns:
        dict: The API response containing the notification template details.
    """
    endpoint = (
        f"{api_url}/api/v1/org/{org_uid}/notification_template/{template_uid}"
    )
    return get(endpoint, api_key).json()["notification_template"]


def get_notification_templates(api_url, api_key, org_uid, **params):
    """
    List notification templates for an organization.

    Args:
        org_uid (str): The organization UID.
        **params: Optional query parameters.

    Returns:
        dict: The API response containing the list of notification templates.
    """
    endpoint = f"{api_url}/api/v1/org/{org_uid}/notification_template/"
    resp = get(endpoint, api_key, params=params)
    jo = resp.json()
    nts = jo["notification_templates"]
    total_pages = jo["total_pages"]
    return nts, total_pages


def create_email_notification_template(api_url, api_key, org_uid, **kwargs):
    """
    Create an email notification template.

    This will create a new email notification template for an organization.
    Requires the action 'org:CreateNotificationTemplate' on the organization.

    Args:
        api_url (str): The API URL.
        api_key (str): The API key.
        org_uid (str): The organization UID.
        **kwargs: The keyword arguments.

    Keyword Args:
        name (str): Name of the notification template.
        subject (str): Subject of the email.
        body_html (str): HTML body of the email.
        body_text (str): Simple text body of the email.
        description (str, optional): A brief description explaining what the template is for. Max 500 characters.
        tags (List[str], optional): List of tags for the notification template.

    Returns:
        str: The UID of the created template.
    """
    endpoint = f"{api_url}/api/v1/org/{org_uid}/notification_template/email/"
    template_data = {
        "name": kwargs["name"],
        "subject": kwargs["subject"],
        "body_html": kwargs["body_html"],
        "body_text": kwargs["body_text"],
        "description": kwargs.get("description"),
        "tags": kwargs.get("tags", []),
    }
    response = post(endpoint, template_data, api_key)
    return response.json()["uid"]


def update_email_notification_template(
    api_url: str, api_key: str, org_uid: str, template_uid: str, **kwargs
):
    """
    Update an email notification template.

    This will update a specific email notification template for an organization.
    Requires the action 'org:UpdateNotificationTemplate' on the organization.

    Args:
        api_url (str): The API URL.
        api_key (str): The API key.
        org_uid (str): The organization UID.
        template_uid (str): The notification template UID.
        **kwargs: The keyword arguments for updating the template.

    Keyword Args:
        name (str): Name of the notification template.
        subject (str): Subject of the email.
        body_html (str): HTML body of the email.
        body_text (str): Simple text body of the email.
        description (str, optional): A brief description explaining what the template is for. Max 500 characters.
        tags (List[str], optional): List of tags for the notification template.
        clear_description (bool, optional): Clear the description of the notification template.
        clear_tags (bool, optional): Clear the tags of the notification template.

    Returns:
        dict: The API response containing the updated notification template.
    """
    endpoint = f"{api_url}/api/v1/org/{org_uid}/notification_template/email/{template_uid}"

    template_data = {
        "name": kwargs.get("name"),
        "subject": kwargs.get("subject"),
        "body_html": kwargs.get("body_html"),
        "body_text": kwargs.get("body_text"),
        "description": kwargs.get("description"),
        "tags": kwargs.get("tags"),
    }

    # Remove None values from the dictionary
    template_data = {k: v for k, v in template_data.items() if v is not None}

    params = {
        "clear_description": kwargs.get("clear_description", False),
        "clear_tags": kwargs.get("clear_tags", False),
    }

    response = put(endpoint, template_data, api_key, params=params)
    return response.json()["notification_template"]


def create_pagerduty_notification_template(
    api_url: str, api_key: str, org_uid: str, **kwargs
) -> str:
    """
    Create a PagerDuty notification template.

    This function creates a new PagerDuty notification template for an organization.
    It requires the action 'org:CreateNotificationTemplate' on the organization.

    Args:
        api_url (str): The base URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.

    Keyword Args:
        name (str): Name of the notification template.
        severity (str): The perceived severity of the notification. Can be one of info, warning, error, or critical.
        summary (str): A brief text summary of the event, used to generate the summaries/titles of any associated alerts.
        class_ (str, optional): The class/type of the event.
        source (str, optional): Specific human-readable unique identifier, such as a hostname, for the system having the problem.
        component (str, optional): Component of the source machine that is responsible for the event.
        custom_details (dict, optional): Custom details to include in the event.
        description (str, optional): A brief description explaining what the template is for. Max 500 characters.
        group (str, optional): Logical grouping of components of a service, useful for filtering alerts.
        tags (List[str], optional): List of tags for the notification template.

    Returns:
        str: The UID of the created notification template.
    """
    endpoint = (
        f"{api_url}/api/v1/org/{org_uid}/notification_template/pagerduty/"
    )

    template_data = {
        "name": kwargs["name"],
        "severity": kwargs["severity"],
        "summary": kwargs["summary"],
        "class": kwargs.get("class_"),
        "source": kwargs.get("source"),
        "component": kwargs.get("component"),
        "custom_details": kwargs.get("custom_details"),
        "description": kwargs.get("description"),
        "group": kwargs.get("group"),
        "tags": kwargs.get("tags"),
    }

    # Remove None values from the dictionary
    template_data = {k: v for k, v in template_data.items() if v is not None}

    response = post(endpoint, template_data, api_key)
    return response.json()["uid"]


def update_pagerduty_notification_template(
    api_url: str, api_key: str, org_uid: str, template_uid: str, **kwargs
) -> dict:
    """
    Update a PagerDuty notification template.

    Args:
        api_url (str): The base URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        template_uid (str): The unique identifier of the notification template.

    Keyword Args:
        name (str): Name of the notification template.
        severity (str): The perceived severity of the notification. Can be one of info, warning, error, or critical.
        summary (str): A brief text summary of the event, used to generate the summaries/titles of any associated alerts.
        class_ (str, optional): The class/type of the event.
        client (str, optional): The unique identifier of the event source. Defaults to 'Spyderbat Notifications Service'.
        client_url (str, optional): The URL of the event source. Defaults to an org's notifications page in the Spyderbat Console.
        component (str, optional): Component of the source machine that is responsible for the event.
        custom_details (dict, optional): Custom details to include in the event.
        description (str, optional): A brief description explaining what the template is for. Max 500 characters.
        group (str, optional): Logical grouping of components of a service, useful for filtering alerts.
        tags (List[str], optional): List of tags for the notification template.
        clear_description (bool, optional): Clear the description of the notification template.
        clear_tags (bool, optional): Clear the tags of the notification template.

    Returns:
        dict: The API response for the updated template.
    """
    endpoint = f"{api_url}/api/v1/org/{org_uid}/notification_template/pagerduty/{template_uid}"

    template_data = {
        "name": kwargs.get("name"),
        "severity": kwargs.get("severity"),
        "summary": kwargs.get("summary"),
        "class": kwargs.get("class_"),
        "client": kwargs.get("client"),
        "client_url": kwargs.get("client_url"),
        "component": kwargs.get("component"),
        "custom_details": kwargs.get("custom_details"),
        "description": kwargs.get("description"),
        "group": kwargs.get("group"),
        "tags": kwargs.get("tags"),
    }

    # Remove None values from the dictionary
    template_data = {k: v for k, v in template_data.items() if v is not None}

    query_params = {
        "clear_description": kwargs.get("clear_description", False),
        "clear_tags": kwargs.get("clear_tags", False),
    }

    response = put(endpoint, template_data, api_key, params=query_params)
    return response.json()["notification_template"]


def create_slack_notification_template(
    api_url: str, api_key: str, org_uid: str, **kwargs
) -> str:
    """
    Create a Slack notification template.

    This function creates a new Slack notification template for an organization
    and returns the unique identifier of the created template.
    It requires the action 'org:CreateNotificationTemplate' on the organization.

    Args:
        api_url (str): The base URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.

    Keyword Args:
        name (str): Name of the notification template.
        message (str): Message to send to Slack.
        blocks (List[dict], optional): Array of Slack block objects.
        channel (str, optional): Slack channel to send the message to.
        description (str, optional): A brief description explaining what the template is for. Max 500 characters.
        tags (List[str], optional): List of tags for the notification template.

    Returns:
        str: The UID of the created notification template.

    Raises:
        HTTPError: If the request fails.
    """
    endpoint = f"{api_url}/api/v1/org/{org_uid}/notification_template/slack/"

    template_data = {
        "name": kwargs["name"],
        "text": kwargs["text"],
        "blocks": kwargs.get("blocks"),
        "channel": kwargs.get("channel"),
        "description": kwargs.get("description"),
        "tags": kwargs.get("tags"),
    }

    # Remove None values from the dictionary
    template_data = {k: v for k, v in template_data.items() if v is not None}

    response = post(endpoint, template_data, api_key)
    return response.json()["uid"]


def update_slack_notification_template(
    api_url: str,
    api_key: str,
    org_uid: str,
    notification_template_uid: str,
    **kwargs,
) -> dict:
    """
    Update a Slack notification template.

    This function updates a specific Slack notification template for an organization.
    It requires the action 'org:UpdateNotificationTemplate' on the organization.

    Args:
        api_url (str): The base URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        notification_template_uid (str): The unique identifier of the notification template.

    Keyword Args:
        name (str): Name of the notification template.
        message (str): Message to send to Slack.
        blocks (List[dict], optional): Array of Slack block objects.
        channel (str, optional): Slack channel to send the message to.
        description (str, optional): A brief description explaining what the template is for. Max 500 characters.
        tags (List[str], optional): List of tags for the notification template.

    Returns:
        dict: The API response for the updated template.
    """
    endpoint = f"{api_url}/api/v1/org/{org_uid}/notification_template/slack/{notification_template_uid}"

    template_data = {
        "name": kwargs.get("name"),
        "text": kwargs.get("text"),
        "blocks": kwargs.get("blocks"),
        "channel": kwargs.get("channel"),
        "description": kwargs.get("description"),
        "tags": kwargs.get("tags"),
    }

    # Remove None values from the dictionary
    template_data = {k: v for k, v in template_data.items() if v is not None}

    query_params = {
        "clear_description": kwargs.get("clear_description", False),
        "clear_tags": kwargs.get("clear_tags", False),
    }

    response = put(endpoint, template_data, api_key, params=query_params)
    return response.json()["notification_template"]


def create_webhook_notification_template(api_url, api_key, org_uid, **kwargs):
    """
    Create a webhook notification template.

    This function creates a new webhook notification template for an organization.
    It requires the action 'org:CreateNotificationTemplate' on the organization.

    Args:
        api_url (str): The base URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.

    Keyword Args:
        name (str): Name of the notification template.
        payload (dict): Custom payload to send to the webhook.
        description (str, optional): A brief description explaining what the template is for. Max 500 characters.
        entire_object (bool, optional): Send the entire object as the payload. Overrides the payload field.
        tags (List[str], optional): List of tags for the notification template.

    Returns:
        dict: The API response for the created template, containing the 'uid' of the new template.
    """
    endpoint = f"{api_url}/api/v1/org/{org_uid}/notification_template/webhook/"

    template_data = {
        "name": kwargs.get("name"),
        "payload": kwargs.get("payload"),
        "description": kwargs.get("description"),
        "entire_object": kwargs.get("entire_object"),
        "tags": kwargs.get("tags"),
    }

    # Remove None values from the dictionary
    template_data = {k: v for k, v in template_data.items() if v is not None}

    response = post(endpoint, template_data, api_key)
    return response.json()["uid"]


def update_webhook_notification_template(
    api_url, api_key, org_uid, template_uid, **kwargs
):
    """
    Update a webhook notification template.

    This function updates a specific webhook notification template for an organization.
    It requires the action 'org:UpdateNotificationTemplate' on the organization.

    Args:
        api_url (str): The base URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        template_uid (str): The unique identifier of the notification template.

    Keyword Args:
        name (str, optional): Name of the notification template.
        description (str, optional): A brief description explaining what the template is for. Max 500 characters.
        entire_object (bool, optional): Send the entire object as the payload. Overrides the payload field.
        payload (dict, optional): Custom payload to send to the webhook.
        tags (List[str], optional): List of tags for the notification template.
        clear_description (bool, optional): Clear the description of the notification template.
        clear_tags (bool, optional): Clear the tags of the notification template.

    Returns:
        dict: The API response for the updated template, containing the updated notification_template details.
    """
    endpoint = f"{api_url}/api/v1/org/{org_uid}/notification_template/webhook/{template_uid}"

    query_params = {
        "clear_description": kwargs.get("clear_description"),
        "clear_tags": kwargs.get("clear_tags"),
    }
    # Remove None values from the query_params dictionary
    query_params = {k: v for k, v in query_params.items() if v is not None}

    template_data = {
        "name": kwargs.get("name"),
        "description": kwargs.get("description"),
        "entire_object": kwargs.get("entire_object"),
        "payload": kwargs.get("payload"),
        "tags": kwargs.get("tags"),
    }

    # Remove None values from the template_data dictionary
    template_data = {k: v for k, v in template_data.items() if v is not None}

    response = put(endpoint, template_data, api_key, params=query_params)
    return response.json()["notification_template"]


def delete_notification_template(api_url, api_key, org_uid, template_uid):
    """
    Delete a specific notification template.

    Args:
        org_uid (str): The organization UID.
        template_uid (str): The notification template UID.

    Returns:
        dict: The API response for the deleted template.
    """
    endpoint = (
        f"{api_url}/api/v1/org/{org_uid}/notification_template/{template_uid}"
    )
    return delete(endpoint, api_key)
