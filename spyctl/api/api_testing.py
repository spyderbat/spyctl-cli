"""Handles API calls that test spyctl service functionality."""

from typing import Dict

from spyctl.api.primitives import post


def api_diff(api_url, api_key, org_uid, obj, d_objs):
    d_objs = d_objs if isinstance(d_objs, list) else [d_objs]
    url = f"{api_url}/api/v1/org/{org_uid}/spyctl/diff/"
    data = {
        "diff_objects": d_objs,
        "object": obj,
        "include_irrelevant": True,
        "content_type": "text",
    }
    resp = post(url, data, api_key)
    diff_data = resp.json()["diff_data"]
    return diff_data


def api_create_guardian_policy(
    api_url, api_key, org_uid, name, mode, data: Dict
) -> str:
    data = data if isinstance(data, list) else [data]
    url = f"{api_url}/api/v1/org/{org_uid}/spyctl/guardianpolicy/build/"
    data = {"input_objects": data, "mode": mode}
    if name:
        data["name"] = name
    resp = post(url, data, api_key)
    policy = resp.json()["policy"]
    return policy


def api_create_suppression_policy(
    api_url,
    api_key,
    org_uid,
    name,
    pol_type,
    scope_to_users,
    object_uid,
    **selectors,
) -> str:
    url = f"{api_url}/api/v1/org/{org_uid}/spyctl/suppressionpolicy/build/"
    data = {"type": pol_type}

    def dash(key: str) -> str:
        return key.replace("_", "-")

    processed_selectors = {dash(k): v for k, v in selectors.items()}
    if name:
        data["name"] = name
    if scope_to_users:
        data["scope_to_users"] = scope_to_users
    if object_uid:
        data["object_uid"] = object_uid
    if processed_selectors:
        data["selectors"] = processed_selectors
    print(data)
    resp = post(url, data, api_key)
    policy = resp.json()["policy"]
    return policy


def api_merge(api_url, api_key, org_uid, obj, m_objs):
    m_objs = m_objs if isinstance(m_objs, list) else [m_objs]
    url = f"{api_url}/api/v1/org/{org_uid}/spyctl/merge/"
    data = {"merge_objects": m_objs, "object": obj}
    resp = post(url, data, api_key)
    merged_object = resp.json()["merged_object"]
    return merged_object


def api_validate(api_url, api_key, org_uid, data: Dict) -> str:
    url = f"{api_url}/api/v1/org/{org_uid}/spyctl/validate/"
    resp = post(url, data, api_key)
    invalid_msg = resp.json()["invalid_message"]
    return invalid_msg
