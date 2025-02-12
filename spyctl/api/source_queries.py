"""Contains the basic logic for making API calls to the Source Query API."""

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Generator, List, Optional, Tuple, Union

import requests
import tqdm

from spyctl.api.primitives import NotFoundException, post
from spyctl.cache_dict import CacheDict

MAX_TIME_RANGE_SECS = 43200  # 12 hours
DEFAULT_CACHE_DICT_LEN = 10000


def retrieve_data(
    api_url: str,
    api_key: str,
    org_uid: str,
    sources: Union[str, List[str]],
    datatype: str,
    schema: Optional[str],
    time: Tuple[float, float],
    raise_notfound=False,
    pipeline: List = None,
    url: str = "api/v1/source/query/",
    disable_pbar=False,
    limit_mem=True,
    disable_pbar_on_first=False,
    api_data: Dict = None,
    last_model=True,
    projection_func: Optional[Callable] = None,
):
    """This is the defacto data retrieval function. Most queries that don't
    target the SQL db can be executed with this function. It enforces limited
    memory usage unless told otherwise, shows a progress bar unless told
    otherwise, and yields records one at a time. The data returned is unsorted.

    Args:
        api_url (str): Top-most part of the API url -- from context
        api_key (str): Key to access the API -- from context
        org_uid (str): Org to get data from -- from context
        source (str, List[str]): The uid(s) that the data are tied to
        datatype (str): The data stream to look for the data in
        schema (str): An optional prefix of the schema for the desired objects
            (ex. model_connection, model_process)
        time (Tuple[float, float]): A tuple with (starting time, ending time)
        raise_notfound (bool, optional): Error to raise if the API throws an
            404 error. Defaults to False.
        pipeline (list, optional): Filtering done by the api.
            Defaults to None.
        url (str, optional): Alternative url path (ex. f"{api_url}/{url}").
            Defaults to "api/v1/source/query/".
        disable_pbar (bool, optional): Does not show the progress bar if set
            to True. Defaults to False.
        limit_mem (bool, optional): Limits the memory usage on the Latest
            Model calculation. If True we may return duplicate objects.
            Defaults to True.
        disable_pbar_on_first (bool, optional): Closes and clears the progress
            bar after first item is returned. Defaults to False.
        api_data (dict, optional): Alternative data to pass to the API.
        last_model (bool, optional): If True, the API will return only the last model
            in the result set for each object. Defaults to True.

    Yields:
        Iterator[dict]: An iterator over retrieved objects.
    """

    progress_bar_tracker: List[tqdm.tqdm] = []
    popped_off_cache = []

    def yield_on_del(_, value):
        if disable_pbar_on_first:
            progress_bar_tracker[0].close()
        popped_off_cache.append(value)

    cache_len = DEFAULT_CACHE_DICT_LEN if limit_mem else None
    data = CacheDict(cache_len=cache_len, on_del=yield_on_del)

    def new_version(rec_id: str, obj: dict) -> bool:
        new_v = obj.get("version")
        if not new_v:
            return True
        old_obj: Dict = data.get(rec_id)
        if not old_obj:
            return True
        old_v = old_obj.get("version")
        if not old_v:
            return True
        return new_v > old_v

    if isinstance(sources, str):
        sources = [sources]

    for resp in threadpool_progress_bar_time_blocks(
        sources,
        time,
        lambda src_uid, time_tup: get_filtered_data(
            api_url,
            api_key,
            org_uid,
            src_uid,
            datatype,
            schema,
            time_tup,
            raise_notfound,
            pipeline,
            url,
            api_data,
        ),
        disable_pbar=disable_pbar,
        pbar_tracker=progress_bar_tracker,
    ):
        if not resp:
            continue
        for json_obj in resp.iter_lines():
            obj = json.loads(json_obj)
            rec_id = obj.get("id")
            if projection_func:
                obj_projected = projection_func(obj)
                if not obj_projected:
                    continue
                if "version" not in obj_projected:
                    obj_projected["version"] = obj.get("version")
                obj = obj_projected

            if rec_id and last_model:
                if new_version(rec_id, obj):
                    data[rec_id] = obj
                    while len(popped_off_cache) > 0:
                        yield popped_off_cache.pop()
            else:
                yield obj
    while len(data) > 0:
        yield data.popitem()[1]


def get_filtered_data(
    api_url,
    api_key,
    org_uid,
    source,
    datatype,
    schema,
    time,
    raise_notfound=False,
    pipeline=None,
    url="api/v1/source/query/",
    api_data=None,
) -> Optional[requests.Response]:
    """This function formats and makes a post request following the
    "source query" format. If a pipeline is not provided, this function will
    craft a basic one.

    Args:
        api_url (str): Top-most part of the API url -- from context
        api_key (str): Key to access the API -- from context
        org_uid (str): Org to get data from -- from context
        source (str, List[str]): The uid(s) that the data are tied to
        datatype (str): The data stream to look for the data in
        schema (str): A prefix of the schema for the desired objects
            (ex. model_connection, model_process)
        time (Tuple[float, float]): A tuple with (starting time, ending time)
        raise_notfound (bool, optional): Error to raise if the API throws an
            error. Defaults to False.
        pipeline (_type_, optional): Filtering done by the api.
            Defaults to None.
        url (_type_, optional): Alternative url path (ex. f"{api_url}/{url}").
            Defaults to "api/v1/source/query/".

    Returns:
        Response: The http response from the request.
    """
    url = f"{api_url}/{url}"
    if not api_data:
        data = {
            "start_time": time[0],
            "end_time": time[1],
            "data_type": datatype,
            "pipeline": [],
        }
        if schema is not None:
            data["pipeline"].append({"filter": {"schema": schema}})
        data["pipeline"].append({"latest_model": {}})
        if org_uid:
            data["org_uid"] = org_uid
        if pipeline:
            data["pipeline"] = pipeline
        if source:
            data["src_uid"] = source
    else:
        api_data["src_uid"] = source
        data = api_data
    try:
        return post(url, data, api_key, raise_notfound)
    except NotFoundException:
        return None


def threadpool_progress_bar_time_blocks(
    args_per_thread: List[str],
    time,
    function: Callable,
    max_time_range=MAX_TIME_RANGE_SECS,
    disable_pbar=False,
    pbar_tracker: List = None,
) -> Generator[Dict, None, None]:
    """This function runs a multi-threaded task such as making multiple API
    requests simultaneously. By default it shows a progress bar. This is a
    specialized function for the Spyderbat API because it will break up
    api-requests into time blocks of a maximum size if necessary. The
    Spyderbat API doesn't like queries spanning over 24 hours so we break them
    into smaller chunks.

    Args:
        args_per_thread (List[str]): The args to pass to each thread example:
            list of source uids.
        time (Tuple[float, float]): A tuple containing the start and end time
            of the task
        function (Callable): The function that each thread will perform
        max_time_range (_type_, optional): The maximum size of a time block.
            Defaults to MAX_TIME_RANGE_SECS.
        disable_pbar (bool, optional): Disable the progress bar.
            Defaults to False.
        pbar_tracker (list): A list that allows calling functions to control
            the pbar.

    Yields:
        Iterator[any]: The return value from the thread task.
    """
    if pbar_tracker is None:
        pbar_tracker = []
    t_blocks = time_blocks(time, max_time_range)
    args_per_thread = [
        [arg, t_block] for arg in args_per_thread for t_block in t_blocks
    ]
    pbar = tqdm.tqdm(
        total=len(args_per_thread),
        leave=False,
        file=sys.stderr,
        disable=disable_pbar,
    )
    pbar_tracker.clear()
    pbar_tracker.append(pbar)
    threads = []
    with ThreadPoolExecutor() as executor:
        for args in args_per_thread:
            threads.append(executor.submit(function, *args))
        for task in as_completed(threads):
            pbar.update(1)
            yield task.result()


def threadpool_progress_bar(
    args_per_thread: Union[List[List], List[str]],
    function: Callable,
    unpack_args=False,
):
    """A simplified version of the above function. In most cases it is
    best to use the time_blocks version unless you really know what you're
    doing.

    Args:
        args_per_thread (Union[List[List], List[str]]): The args to pass to
            each thread example:
            list of source uids.
        function (Callable): The function that each thread will perform
        unpack_args (bool, optional): _description_. Defaults to False.

    Yields:
        Iterator[any]: The return value from the thread task.
    """
    pbar = tqdm.tqdm(total=len(args_per_thread), leave=False, file=sys.stderr)
    threads = []
    with ThreadPoolExecutor() as executor:
        for args in args_per_thread:
            if unpack_args:
                threads.append(executor.submit(function, *args))
            else:
                threads.append(executor.submit(function, args))
        for task in as_completed(threads):
            pbar.update(1)
            yield task.result()


def time_blocks(time_tup: Tuple, max_time_range=MAX_TIME_RANGE_SECS) -> List[Tuple]:
    """Takes a time tuple (start, end) in epoch time and converts
    it to smaller chunks if necessary.

    Args:
        time_tup (Tuple): start, end

    Returns:
        List[Tuple]: A list of (start, end) tuples to be used in api
            queries
    """
    st, et = time_tup
    if et - st > max_time_range:
        rv = []
        while et - st > max_time_range:
            et2 = min(et, st + max_time_range)
            rv.append((st, et2))
            st = et2
        rv.append((st, et))
        return rv
    return [time_tup]
