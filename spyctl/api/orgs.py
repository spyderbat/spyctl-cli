"""Handles the API calls for the organizations endpoint."""

from typing import List, Tuple

from spyctl.api.primitives import get


def get_orgs(api_url, api_key) -> List[Tuple]:
    org_uids = []
    org_names = []
    url = f"{api_url}/api/v1/org/"
    orgs_json = get(url, api_key).json()
    for org in orgs_json:
        org_uids.append(org["uid"])
        org_names.append(org["name"])
    return (org_uids, org_names)
