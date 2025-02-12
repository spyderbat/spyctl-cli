"""Handles saved queries API requests."""

# spellchecker: ignore savedquery updatelastused

from typing import Dict, List, Tuple

from requests import Response

from spyctl.api.primitives import delete, get, post, put


def get_saved_query(api_url, api_key, org_uid, saved_query_uid) -> Dict:
    """
    Gets a saved query from the specified organization.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        saved_query_uid (str): The unique identifier of the saved query to be
            retrieved.

    Returns:
        Dict: The saved query data.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/savedquery/{saved_query_uid}"
    resp = get(url, api_key)
    sq = resp.json()["saved_query"]
    return sq


def get_saved_queries(
    api_url, api_key, org_uid, **query_params
) -> Tuple[List[Dict], int]:
    """
    Gets all saved queries from the specified organization that match
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
        Tuple[List[Dict], int]: A list of saved queries and the total number
        of pages.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/savedquery/"
    resp = get(url, api_key, params=query_params)
    jo = resp.json()
    sqs = jo["saved_queries"]
    total_pages = jo["total_pages"]
    return sqs, total_pages


def get_saved_query_dependents(
    api_url, api_key, org_uid, saved_query_uid
) -> List[Dict]:
    """
    Gets all dependents of a saved query from the specified organization.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        saved_query_uid (str): The unique identifier of the saved query.

    Returns:
        List[Dict]: A list of dependents of the saved query.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/savedquery/{saved_query_uid}/dependents"  # noqa
    resp = get(url, api_key)
    return resp.json()


def post_new_saved_query(api_url, api_key, org_uid, **req_body) -> str:
    """
    Sends a POST request to create a new saved query.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        **req_body: The request body.

    Request Body:
        name (str)
        schema (str)
        query (str)
        description (str)

    Returns:
        str: The uid of the new saved query.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/savedquery/"
    resp = post(url, req_body, api_key)
    uid = resp.json()["uid"]
    return uid


def put_saved_query_update(
    api_url, api_key, org_uid, saved_query_uid, **req_body
) -> Dict:
    """
    Sends a PUT request to update an existing saved query.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        saved_query_uid (str): The unique identifier of the saved query to be
            updated.
        **req_body: The request body.

    Request Body:
        name (str): The name of the saved query.
        description (str): The description of the saved query.
        query (str): The query of the saved query.

    Returns:
        Dict: The updated saved query.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/savedquery/{saved_query_uid}"
    resp = put(url, req_body, api_key)
    sq = resp.json()["saved_query"]
    return sq


def put_update_last_used(api_url, api_key, org_uid, saved_query_uid) -> Response:
    """
    Sends a PUT request to update the last used time of a saved query.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        saved_query_uid (str): The unique identifier of the saved query to be
            updated.

    Returns:
        Dict: The updated saved query.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/savedquery/{saved_query_uid}/updatelastused"  # noqa
    return put(url, None, api_key)


def delete_saved_query(api_url, api_key, org_uid, saved_query_uid) -> Response:
    """
    Sends a DELETE request to delete a saved query from the specified.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        saved_query_uid (str): The unique identifier of the saved query to be
            deleted.

    Returns:
        Response: The response object.
    """

    url = f"{api_url}/api/v1/org/{org_uid}/savedquery/{saved_query_uid}"
    return delete(url, api_key)
