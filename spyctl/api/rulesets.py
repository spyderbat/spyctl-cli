"""Handles the API calls for the rulesets endpoint."""

import json
from typing import Dict, Optional

from spyctl.api.primitives import delete, get, post, put


def delete_ruleset(api_url, api_key, org_uid, ruleset_uid):
    """
    Deletes a ruleset from the specified organization.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        ruleset_uid (str): The unique identifier of the ruleset to be deleted.

    Returns:
        Response: The response from the API indicating the success or failure
            of the deletion.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/analyticsruleset/{ruleset_uid}"
    resp = delete(url, api_key)
    return resp


def post_new_ruleset(api_url, api_key, org_uid, ruleset: Dict):
    """
    Posts a new ruleset to the specified API endpoint.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        ruleset (Dict): The ruleset to be posted.

    Returns:
        Response: The response from the API.

    """
    data = {"ruleset": ruleset}
    url = f"{api_url}/api/v1/org/{org_uid}/analyticsruleset/"
    resp = post(url, data, api_key)
    return resp


def put_ruleset_update(api_url, api_key, org_uid, ruleset: Dict):
    """
    Updates a ruleset using the provided API URL, API key, organization UID
    and ruleset data.

    Parameters:
    - api_url (str): The URL of the API.
    - api_key (str): The API key for authentication.
    - org_uid (str): The UID of the organization.
    - ruleset (Dict): The ruleset data to be updated.

    Returns:
    - resp: The response from the API call.
    """
    data = {"ruleset": ruleset}
    url = f"{api_url}/api/v1/org/{org_uid}/analyticsruleset/"
    resp = put(url, data, api_key)
    return resp


def get_rulesets(api_url, api_key, org_uid, params=None, raw_data=False):
    """
    Retrieves the rulesets for a given organization from the specified API
    endpoint.

    Args:
        api_url (str): The URL of the API endpoint.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        params (dict, optional): Additional parameters to include in th
            request. Defaults to None.
        raw_data (bool, optional): Flag indicating whether to return the ra
            data or just the ruleset names. Defaults to False.

    Returns:
        list: A list of rulesets. Each ruleset is represented as a dictionary.

    """
    url = f"{api_url}/api/v1/org/{org_uid}/analyticsruleset/"
    params = {} if params is None else params
    resp = get(url, api_key, params)
    rulesets = []
    for ruleset_json in resp.iter_lines():
        ruleset_list = json.loads(ruleset_json)
        for ruleset in ruleset_list:
            if not raw_data:
                rulesets.append(ruleset["ruleset"])
            else:
                rulesets.append(ruleset)
    return rulesets


def get_ruleset(api_url, api_key, org_uid, ruleset_uid) -> Optional[Dict]:
    """
    Retrieves a specific ruleset from the API.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        ruleset_uid (str): The unique identifier of the ruleset.

    Returns:
        Optional[Dict]: The ruleset as a dictionary, or None if not found.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/analyticsruleset/{ruleset_uid}"
    resp = get(url, api_key, raise_notfound=True)
    for ruleset_json in resp.iter_lines():
        ruleset = json.loads(ruleset_json)
        if ruleset:
            return ruleset["ruleset"]
    return None
