"""Handles search set API requests."""

# spellchecker: ignore searchset updatelastused

from typing import Dict, List

from requests import Response

from spyctl.api.primitives import delete, get, post, put


def get_search_set(api_url, api_key, org_uid, search_set_uid) -> Dict:
    """
    Gets a search set from the specified organization.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        search_set_uid (str): The unique identifier of the search set to be
            retrieved.

    Returns:
        Dict: The search set data.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/searchset/{search_set_uid}"
    resp = get(url, api_key)
    return resp.json()


def get_search_sets(api_url, api_key, org_uid, **query_params) -> List[Dict]:
    """
    Gets all search sets from the specified organization that match
    the query parameters.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        **query_params: Keyword query parameters.

    Query Parameters:
        from_archive (bool)
        name_contains (str)
        name_equals (str)
        name_or_uid_contains (str)
        type (str)
        uid_equals (str)

    Returns:
        List[Dict]: A list of search sets.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/searchset/"
    resp = get(url, api_key, params=query_params)
    return resp.json()


def post_new_search_set(api_url, api_key, org_uid, **req_body) -> str:
    """
    Sends a POST request to create a new search set.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.

    Returns:
        str: The uid of the new search set.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/searchset/"
    resp = post(url, req_body, api_key)
    uid = resp.json()["uid"]
    return uid


def put_search_set_update(api_url, api_key, org_uid, **req_body) -> Dict:
    """
    Sends a PUT request to update an existing search set.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.

    Returns:
        Dict: The updated search set.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/searchset/"
    resp = put(url, req_body, api_key)
    jo = resp.json()
    return jo


def delete_search_set(api_url, api_key, org_uid, search_set_uid) -> Response:
    """
    Sends a DELETE request to delete a search set.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        search_set_uid (str): The unique identifier of the search set to be
            deleted.

    Returns:
        Response: The response object.
    """

    url = f"{api_url}/api/v1/org/{org_uid}/searchset/{search_set_uid}"
    return delete(url, api_key)
