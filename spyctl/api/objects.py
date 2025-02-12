"""Contains the logic for making API calls to the Objects API"""

import math
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

import requests
import tqdm

from spyctl import cli
from spyctl.api.primitives import post

OBJECTS_LIMIT = 500


def get_objects(
    api_url: str, api_key: str, org_uid: str, ids: List[str], **kwargs
) -> List[Dict]:
    """
    Retrieves a list of hydrated objects from the API.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        ids (List[str]): A list of object IDs to retrieve.
        **kwargs: Additional keyword arguments.

    Keyword Args:
        use_pbar (bool): Whether to use a progress bar (default: True).
        desc (str): Description for the progress bar.

    Returns:
        dict: The response from the API.

    """
    url = f"{api_url}/api/v1/org/{org_uid}/objects"
    rv = []
    with (
        tqdm.tqdm(
            total=math.ceil(len(ids) / OBJECTS_LIMIT),
            leave=False,
            file=sys.stderr,
            disable=not kwargs.get("use_pbar", True),
            desc=kwargs.get("desc", "Retrieving Objects"),
        ) as pbar,
        ThreadPoolExecutor(max_workers=10) as executor,
    ):
        id_groups = [
            ids[i : i + OBJECTS_LIMIT]  # noqa: E203
            for i in range(0, len(ids), OBJECTS_LIMIT)
        ]
        threads = []
        for group in id_groups:
            threads.append(executor.submit(post, url, {"ids": group}, api_key))
        for task in as_completed(threads):
            pbar.update(1)
            response = task.result()
            try:
                json_data = response.json()
                results = json_data.get("results", [])
                rv.extend(results)
            except requests.exceptions.JSONDecodeError:
                cli.err_exit(f"Failed to decode JSON response: {response.text}")
    return rv
