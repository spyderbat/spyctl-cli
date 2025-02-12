"""Handles the retrieval of sources from the API endpoint."""

from typing import Dict, List

import zulu

from spyctl.api.primitives import get

AUTO_HIDE_TIME = zulu.now().shift(days=-1)


def get_sources(api_url, api_key, org_uid, **kwargs) -> List[Dict]:
    """
    Retrieves a list of sources from the specified API endpoint.

    Args:
        api_url (str): The URL of the API endpoint.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        **kwargs: Additional keyword arguments.

    Keyword Args:
        include_expired (bool): Include expired sources in the output.
        exclude_clustermonitors (bool): Exclude the cluster monitor source
            from the output.

    Returns:
        List[Dict]: A list of dictionaries representing the sources.

    """
    machines: Dict[str, Dict] = {}
    url = f"{api_url}/api/v1/org/{org_uid}/source/"
    source_json = get(url, api_key).json()
    for source in source_json:
        src_uid = source["uid"]
        if not src_uid.startswith("global"):
            machines[src_uid] = source
    # agents API call to find "description" (name used by the UI)
    url = f"{api_url}/api/v1/org/{org_uid}/agent/"
    agent_json = get(url, api_key).json()
    for agent in agent_json:
        src_uid = agent["runtime_details"]["src_uid"]
        description = agent["description"]
        if not agent["uid"].startswith("global"):
            source = machines.get(src_uid)
            if source is None:
                continue
            source.update(agent)
            machine = {}
            machine["uid"] = src_uid
            machine["name"] = description
            del source["uid"]
            del source["description"]
            del source["name"]
            machine.update(source)
            machines[src_uid] = machine
    # Auto-hide inactive machines
    rv = []
    include_expired = kwargs.get("include_expired", False)
    if not include_expired:
        for machine in machines.values():
            if (
                zulu.Zulu.parse(machine["last_data"]) >= AUTO_HIDE_TIME
                or zulu.Zulu.parse(machine["last_stored_chunk_end_time"])
                >= AUTO_HIDE_TIME
            ) and "runtime_details" in machine:
                rv.append(machine)
    else:
        rv = list(machines.values())
    if kwargs.get("exclude_clustermonitors", False):
        rv = [machine for machine in rv if not machine["uid"].startswith("muid")]
    return rv
