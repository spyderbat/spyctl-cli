"""Handles the source queries around Agent Resources."""

import json
import sys
from typing import Dict, Generator, List, Tuple

import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.primitives import get
from spyctl.api.source_queries import (
    get_filtered_data,
    retrieve_data,
    threadpool_progress_bar,
)


def get_agents(
    api_url,
    api_key,
    org_uid,
    muids,
    time,
    pipeline=None,
    limit_mem: bool = True,
    disable_pbar_on_first: bool = False,
    disable_pbar: bool = False,
) -> Generator[Dict, None, None]:
    """
    Retrieves a generator of agents based on the provided parameters.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        muids (List[str]): The list of unique identifiers for the agents.
        time (str): The time parameter for retrieving agents.
        pipeline (Optional[str]): The pipeline parameter for retrieving agents.
            Defaults to None.
        limit_mem (bool): Flag indicating whether to limit memory usage.
            Defaults to False.
        disable_pbar_on_first (bool): Flag indicating whether to disable
            progress bar on the first retrieval. Defaults to False.
        disable_pbar (bool): Whether to disable the progress bar completely

    Yields:
        Dict: A dictionary representing an agent.

    Raises:
        KeyboardInterrupt: If the retrieval process is interrupted by a
            keyboard interrupt.

    """
    try:
        datatype = lib.DATATYPE_AGENTS
        schema = lib.MODEL_AGENT_SCHEMA_PREFIX
        for agent in retrieve_data(
            api_url,
            api_key,
            org_uid,
            muids,
            datatype,
            schema,
            time,
            pipeline=pipeline,
            limit_mem=limit_mem,
            disable_pbar_on_first=disable_pbar_on_first,
            disable_pbar=disable_pbar,
        ):
            yield agent
    except KeyboardInterrupt:
        __log_interrupt()


def get_agent_metrics(
    api_url,
    api_key,
    org_uid,
    sources,
    time,
    pipeline=None,
    limit_mem: bool = True,
    disable_pbar_on_first: bool = False,
    disable_pbar: bool = False,
) -> Generator[Dict, None, None]:
    """
    Retrieves agent metrics from the specified API.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        sources (List[str]): The list of agent sources to retrieve metrics
            from.
        time (str): The time range for the metrics.
        pipeline (Optional[str]): The pipeline to filter the metrics.
        limit_mem (bool): Whether to limit memory usage.
        disable_pbar_on_first (bool): Whether to disable the progress bar on
            the first metric.
        disable_pbar (bool): Whether to disable the progress bar completely

    Yields:
        Dict: A dictionary containing the agent metrics.

    Raises:
        KeyboardInterrupt: If the function is interrupted by the user.

    """
    try:
        datatype = lib.DATATYPE_AGENTS
        schema = lib.EVENT_METRICS_PREFIX
        for metric in retrieve_data(
            api_url,
            api_key,
            org_uid,
            sources,
            datatype,
            schema,
            time,
            pipeline=pipeline,
            limit_mem=limit_mem,
            disable_pbar_on_first=disable_pbar_on_first,
            disable_pbar=disable_pbar,
        ):
            yield metric
    except KeyboardInterrupt:
        __log_interrupt()


def get_latest_agent_metrics(
    api_url,
    api_key,
    org_uid,
    args: List[Tuple[str, Tuple]],  # list (source_uid, (st, et))
    pipeline=None,
):
    """
    Retrieves the latest agent metrics from the specified API.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        args (List[Tuple[str, Tuple]]): A list of tuples containing the source
            UID and the time range (start time, end time).
        pipeline (Optional): The pipeline to use for data retrieval.

    Yields:
        dict: A dictionary containing the metrics record for each agent.

    Raises:
        KeyboardInterrupt: If the function is interrupted by the user.

    """
    try:
        for resp in threadpool_progress_bar(
            args,
            lambda source, time_tup: get_filtered_data(
                api_url,
                api_key,
                org_uid,
                source,
                lib.DATATYPE_AGENTS,
                lib.EVENT_METRICS_PREFIX,
                time_tup,
                pipeline=pipeline,
            ),
            unpack_args=True,
        ):
            latest_time = 0
            for json_obj in reversed(list(resp.iter_lines())):
                metrics_record = json.loads(json_obj)
                time = metrics_record["time"]
                if time <= latest_time:
                    break
                latest_time = time
                yield metrics_record
    except KeyboardInterrupt:
        __log_interrupt()


def get_sources_data_for_agents(api_url, api_key, org_uid) -> Dict:
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
                "cloud_region": lib.NOT_AVAILABLE,
                "cloud_type": lib.NOT_AVAILABLE,
                "last_data": source["last_data"],
            }
        else:
            rv[source_uid] = {
                "uid": source["uid"],
                "cloud_region": source["runtime_details"].get(
                    "cloud_region", lib.NOT_AVAILABLE
                ),
                "cloud_type": source["runtime_details"].get(
                    "cloud_type", lib.NOT_AVAILABLE
                ),
                "last_data": source["last_data"],
            }
    return rv


# ----------------------------------------------------------------- #
#                          Helper Functions                         #
# ----------------------------------------------------------------- #


def __log_interrupt():
    cli.try_log("\nRequest aborted, no partial results.. exiting.")
    sys.exit(0)
