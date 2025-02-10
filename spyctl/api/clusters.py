"""Handles the Cluster-Related API Calls."""

from typing import Dict, List

from spyctl.api.primitives import get


def get_clusters(api_url, api_key, org_uid) -> List[Dict]:
    """
    Retrieves a list of clusters from the specified API URL for the given
    organization UID.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The UID of the organization.

    Returns:
        List[Dict]: A list of dictionaries representing the clusters.

    """
    clusters = []
    url = f"{api_url}/api/v1/org/{org_uid}/cluster/"
    json = get(url, api_key).json()
    for cluster in json:
        if "/" not in cluster["uid"]:
            clusters.append(cluster)
    return clusters
