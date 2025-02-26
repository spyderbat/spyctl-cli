"""Handles the source queries around Agent Resources."""

import sys
from typing import Dict, List, Tuple

import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.primitives import get


def get_sources_data_for_agents(
    api_url, api_key, org_uid, agents: List[Dict]
) -> Tuple[List[Dict], Dict]:
    """
    Retrieves the sources data for agents from the specified API.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.

    Returns:
        dict: A dictionary containing the sources data for agents. The keys
            are the source UIDs and the values are dictionaries
            with the following keys: 'uid', 'cloud_region', 'cloud_type',
            and 'last_data'.
    """
    rv = {}
    url = f"{api_url}/api/v1/org/{org_uid}/source/"
    sources = get(url, api_key).json()
    for source in sources:
        source_uid = source["uid"]  # muid
        if "runtime_details" not in source:
            rv[source_uid] = {
                "uid": source["uid"],
                "name": source.get("runtime_description"),
                "cloud_region": lib.NOT_AVAILABLE,
                "cloud_type": lib.NOT_AVAILABLE,
                "last_data": source["last_data"],
            }
        else:
            rv[source_uid] = {
                "uid": source["uid"],
                "name": source.get("runtime_description"),
                "cloud_region": source["runtime_details"].get(
                    "cloud_region", lib.NOT_AVAILABLE
                ),
                "cloud_type": source["runtime_details"].get(
                    "cloud_type", lib.NOT_AVAILABLE
                ),
                "last_data": source["last_data"],
            }
    for agent in agents:
        agent["name"] = rv.get(agent["muid"], {}).get("name")
    return agents, rv


# ----------------------------------------------------------------- #
#                          Helper Functions                         #
# ----------------------------------------------------------------- #


def __log_interrupt():
    cli.try_log("\nRequest aborted, no partial results.. exiting.")
    sys.exit(0)
