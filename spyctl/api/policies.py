"""Handles the API requests for analytics policies."""

import json
from typing import Dict

import spyctl.spyctl_lib as lib
from spyctl.api.primitives import delete, get, post, put


def delete_policy(api_url, api_key, org_uid, pol_uid):
    """
    Deletes a policy from the analytics API.

    Args:
        api_url (str): The URL of the analytics API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        pol_uid (str): The unique identifier of the policy to be deleted.

    Returns:
        resp (Response): The response object from the API call.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/analyticspolicy/{pol_uid}"
    resp = delete(url, api_key)
    return resp


def get_policies(api_url, api_key, org_uid, params=None, raw_data=False):
    """
    Retrieves the policies for a given organization from the specified AP
    endpoint.

    Args:
        api_url (str): The URL of the API endpoint.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        params (dict, optional): Additional parameters to include in the
            request. Defaults to None.
        raw_data (bool, optional): Flag indicating whether to return the raw
            data or just the policy names. Defaults to False.

    Returns:
        list: A list of policies retrieved from the API endpoint.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/analyticspolicy/"
    params = {} if params is None else params
    policies = []
    resp = get(url, api_key, params)
    for pol_json in resp.iter_lines():
        pol_list = json.loads(pol_json)
        if not raw_data:
            for pol in pol_list:
                policy = pol["policy"]
                policies.append(policy)
        else:
            policies.extend(pol_list)
    return policies


def get_policy(api_url, api_key, org_uid, pol_uid):
    """
    Retrieves a policy from the specified API endpoint.

    Args:
        api_url (str): The URL of the API endpoint.
        api_key (str): The API key for authentication.
        org_uid (str): The UID of the organization.
        pol_uid (str): The UID of the policy.

    Returns:
        list: A list of policies retrieved from the API endpoint.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/analyticspolicy/{pol_uid}"
    resp = get(url, api_key)
    policies = []
    for pol_json in resp.iter_lines():
        pol = json.loads(pol_json)
        uid = pol["uid"]
        policy = pol["policy"]
        policy[lib.METADATA_FIELD][lib.METADATA_UID_FIELD] = uid
        policies.append(policy)
    return policies


def post_new_policy(api_url, api_key, org_uid, policy: Dict):
    """
    Posts a new policy to the specified API endpoint.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        policy (Dict): The policy to be posted.

    Returns:
        Response: The response from the API.

    """
    data = {"policy": policy}
    url = f"{api_url}/api/v1/org/{org_uid}/analyticspolicy/"
    resp = post(url, data, api_key)
    return resp


def put_policy_update(api_url, api_key, org_uid, data: Dict):
    """
    Update a policy using the PUT method.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        data (Dict): The data containing the policy to be updated.

    Returns:
        Response: The response from the API.

    """
    data = {"policy": data}
    url = f"{api_url}/api/v1/org/{org_uid}/analyticspolicy/"
    resp = put(url, data, api_key)
    return resp
