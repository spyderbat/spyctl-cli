"""Contains the logic for making API calls to the Athena Search API"""

import math
import sys
import time
from typing import Dict, List, Optional, Tuple, Union

import requests
import tqdm

import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.objects import get_objects
from spyctl.api.primitives import post

# Athena Search
SEARCH_RESULT_LIMIT = 10000
SEARCH_PAGE_LIMIT = 999


def search_athena(
    api_url: str, api_key: str, org_uid: str, schema: str, query: str, **kwargs
) -> List[Dict]:
    """
    Sends a POST request to create a new search.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        schema (str): The schema for the search.
        query (str): The query for the search.
        **kwargs: Additional keyword arguments.

    Keyword Args:
        start_time (int): starting epoch time of query.
        end_time (int): ending epoch time of the query.
        order_by (list[dict]): The field and ordering to order the results by.
            Example:[{"name":"pid", "ascending": true}],
        group_by (list[dict]): The field to group the results by, with optional bins to group in.
            Example: [{"name": "time","bins": [1727714225, 1727714325, 1727714425]}, {"name": "exe"}],
        output_fields (list[str]): The fields athena includes in the output (if omitted, only "id" is included).
            If this field is present, no further call to the objects api is done to get the full object.
        use_pbar (bool): Whether to use a progress bar (default: True).
        desc (str): Description for the progress bar.
        quiet (bool): Suppress cli output during search (default: False).
        limit (int): The limit of results to return.
    Returns:
        List[Dict]: The search results.
    """
    use_pbar: bool = kwargs.get("use_pbar", True)
    quiet: bool = kwargs.get("quiet", False)
    rv = []
    all_results = []
    desc = kwargs.get("desc")
    desc = f" for {desc}" if desc else ""
    if not quiet:
        cli.try_log(f"Creating new search job{desc}...")
    kwargs["start_time"] = int(kwargs["start_time"])
    kwargs["end_time"] = int(kwargs["end_time"])
    search_id = post_new_search(api_url, api_key, org_uid, schema, query, **kwargs)
    if search_id == "FAILED":
        return []
    token = None
    with tqdm.tqdm(
        total=math.ceil(SEARCH_RESULT_LIMIT / SEARCH_PAGE_LIMIT),
        leave=False,
        file=sys.stderr,
        disable=not kwargs.get("use_pbar", True),
        desc="Waiting for job to complete...",
    ) as pbar:
        while True:
            results, token, _result_count = retrieve_search_data(
                api_url, api_key, org_uid, search_id, token
            )
            if results == "FAILED":
                return []
            if isinstance(results, str):
                time.sleep(0.1)
                continue
            all_results.extend(results)
            pbar.update(1)
            if not token:
                pbar.total = pbar.n
                pbar.refresh()
                break
    if not quiet:
        cli.try_log("Job completed. Retrieving objects...")
    if "output_fields" in kwargs:
        # We got already projected fields, no need to fetch objects
        return all_results
    if len(all_results) > 0:
        ids = list({result["id"] for result in all_results})
        rv.extend(
            get_objects(
                api_url,
                api_key,
                org_uid,
                ids,
                use_pbar=use_pbar,
                desc=kwargs.get("desc"),
            )
        )
    return rv


def post_new_search(
    api_url: str, api_key: str, org_uid: str, schema: str, query: str, **kwargs
) -> str:
    """
    Sends a POST request to create a new search.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        schema (str): The schema for the search.
        query (str): The query for the search.
        **kwargs: Additional keyword arguments.

    Keyword Args:
        start_time (bool): starting epoch time of query.
        end_time (bool): ending epoch time of the query.
        limit (int): The limit of results to return.

    Returns:
        str: The search's job ID.
    """
    now = time.time()
    start_time = kwargs.get("start_time", now - 86400)
    end_time = kwargs.get("end_time", now)
    url = f"{api_url}/api/v1/org/{org_uid}/search/"
    data = {
        "schema": schema,
        "query": query,
        "start_time": start_time,
        "end_time": end_time,
    }
    for kw in ["order_by", "group_by", "output_fields"]:
        if kw in kwargs:
            data[kw] = kwargs[kw]
    limit = kwargs.get("limit", SEARCH_RESULT_LIMIT)
    params = {"limit": limit}
    response = post(url, data, api_key, params=params)
    try:
        json_data = response.json()
        if "error" in json_data:
            cli.err_exit(json_data["error"])
        return json_data.get("id", "FAILED")
    except requests.exceptions.JSONDecodeError:
        cli.err_exit(f"Failed to decode JSON response: {response.text}")
    return "FAILED"


def retrieve_search_data(
    api_url: str, api_key: str, org_uid: str, search_job_id: str, token: str
) -> Tuple[Union[str, List[str]], Optional[str], Optional[int]]:
    """
    Retrieve search data from the specified API endpoint.

    Args:
        api_url (str): The URL of the API endpoint.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        search_job_id (str): The ID of the search job.
        token (str): For retrieving partial results.

    Returns:
        Union[str, List[str], str, str]: The search data retrieved from the
        API endpoint, a token if there is one, and a result count if there
        is one.
        If the search is still in progress, the function returns the status.
        If the search is completed, the function returns a list of result IDs.
        If an unexpected response is received, an error message is displayed.
        If there is a JSON decoding error, an error message is displayed.
        If the retrieval fails, the function returns "FAILED".
    """
    url = f"{api_url}/api/v1/org/{org_uid}/search/{search_job_id}"
    data = {
        "limit": SEARCH_PAGE_LIMIT,
        "token": token,
    }
    response = post(url, data, api_key)
    rv_token = None
    result_count = 0
    try:
        json_data = response.json()
        if "status" in json_data:
            return json_data["status"], rv_token, result_count
        if "results" in json_data:
            rv = json_data["results"]
            rv_token = json_data.get("token")
            result_count = json_data.get("result_count", 0)
            return rv, rv_token, result_count
        cli.err_exit(f"Unexpected response: {json_data}")
    except requests.exceptions.JSONDecodeError:
        cli.err_exit(f"Failed to decode JSON response: {response.text}")
    return "FAILED", rv_token, result_count


def validate_search_query(api_url, api_key, org_uid, schema_type: str, query: str):
    """
    Validates a search query against a specified schema.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        schema_type (str): The type of schema to validate against.
        query (str): The search query to validate.

    Returns:
        str: An error message if the validation fails, otherwise an empty
            string.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/search/validate"
    data = {
        "context_uid": lib.build_ctx(),
        "query": query,
        "schema": schema_type,
    }
    resp = post(url, data, api_key)
    resp = resp.json()
    if not resp["ok"]:
        return resp["error"]
    return ""
