"""Handles custom flags API requests."""

from typing import Dict, List, Tuple
from requests import Response

from spyctl.api.primitives import delete, get, post, put


def get_custom_flag(api_url, api_key, org_uid, custom_flag_uid) -> Dict:
    """
    Gets a custom flag from the specified organization.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        custom_flag_uid (str): The unique identifier of the custom flag to be
            retrieved.

    Returns:
        Dict: The custom flag data.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/customflag/{custom_flag_uid}"
    resp = get(url, api_key)
    cf = resp.json()["custom_flag"]
    return cf


def get_custom_flags(
    api_url, api_key, org_uid, **query_params
) -> Tuple[List[Dict], int]:
    """
    Gets all custom flags from the specified organization that match
    the query parameters.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        **query_params: Keyword query parameters.

    Query Parameters:
        created_by_equals (str)
        name_contains (str)
        name_equals (str)
        name_or_uid_contains (str)
        page (int)
        page_size (int)
        query_contains (str)
        query_equals (str)
        reversed (bool)
        schema_contains (str)
        schema_equals (str)
        sort_by (str)
        uid_equals (str)

    Returns:
        Tuple[List[Dict], int]: A list of custom flags and the total number
        of pages.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/customflag/"
    resp = get(url, api_key, query_params)
    custom_flags = resp.json()["custom_flags"]
    total_pages = resp.json()["total_pages"]
    return custom_flags, total_pages


def post_new_custom_flag(api_url, api_key, org_uid, **req_body) -> str:
    """
    Creates a new custom flag in the specified organization.
    See https://api.spyderbat.com/openapi.pdf for details
    on the request body.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        custom_flag (dict): The custom flag data.

    Request Body:
        name (str): The name of the custom flag.
        description (str): The description of the custom flag.
        saved_query_uid (str): The unique identifier of the saved query.
        severity (str): The severity of the custom flag.
        type (str): The type of the custom flag.
        is_disabled(bool): Whether the custom flag is disabled on creation.
        tags (List[str]): The tags associated with the custom flag.
        impact (str): The impact of the custom flag on the organization.
        content (str): Markdown content describing extra details about the
            custom flag.

    Returns:
        str: The unique identifier of the new custom flag.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/customflag/"
    resp = post(url, req_body, api_key)
    return resp.json()["uid"]


def put_custom_flag_update(
    api_url, api_key, org_uid, custom_flag_uid, **req_body
) -> Dict:
    """
    Updates a custom flag in the specified organization.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        custom_flag_uid (str): The unique identifier of the custom flag to be
            updated.
        **req_body: The updated custom flag data.

    Returns:
        Dict: The updated custom flag data.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/customflag/{custom_flag_uid}"
    resp = put(url, req_body, api_key)
    return resp.json()


def put_enable_custom_flag(
    api_url, api_key, org_uid, custom_flag_uid
) -> Response:
    """
    Enables a custom flag in the specified organization.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        custom_flag_uid (str): The unique identifier of the custom flag to be
            enabled.

    Returns:
        Dict: The response from the API.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/customflag/{custom_flag_uid}/enable"
    return put(url, {}, api_key)


def put_disable_custom_flag(
    api_url, api_key, org_uid, custom_flag_uid
) -> Response:
    """
    Disables a custom flag in the specified organization.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        custom_flag_uid (str): The unique identifier of the custom flag to be
            disabled.

    Returns:
        Dict: The response from the API.
    """
    url = (
        f"{api_url}/api/v1/org/{org_uid}/customflag/{custom_flag_uid}/disable"
    )
    return put(url, {}, api_key)


def delete_custom_flag(api_url, api_key, org_uid, custom_flag_uid) -> Response:
    """
    Deletes a custom flag from the specified organization.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        custom_flag_uid (str): The unique identifier of the custom flag to be
            deleted.

    Returns:
        Response: The response object.
    """

    url = f"{api_url}/api/v1/org/{org_uid}/customflag/{custom_flag_uid}"
    return delete(url, api_key)
