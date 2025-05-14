"""Contains the API primitives for making requests to the Spyderbat API."""

import json
import time

import requests

import spyctl.spyctl_lib as lib
from spyctl import cli

TIMEOUT = (30, 300)

MAX_TIME_RANGE_SECS = 43200  # 12 hours
NAMESPACES_MAX_RANGE_SECS = 2000
TIMEOUT_MSG = "A timeout occurred during the API request. "
LOG_REQUEST_TIMES = False


class NotFoundException(ValueError):
    """Used to indicate that a 404 was returned from the API."""


# ----------------------------------------------------------------- #
#                           API Primitives                          #
# ----------------------------------------------------------------- #


def get(url, key, params=None, raise_notfound=False):
    """
    Sends a GET request to the specified URL with optional parameters and
    headers.

    Args:
        url (str): The URL to send the GET request to.
        key (str): The authorization key to include in the request headers.
        params (dict, optional): The optional parameters to include in the
            request URL.
        raise_notfound (bool, optional): Whether to raise a NotFoundException
            if the response status code is 404.

    Returns:
        requests.Response: The response object containing the server's
            response to the GET request.

    Raises:
        NotFoundException: If raise_notfound is True and the response status
            code is 404.
    """
    start_time = None
    if LOG_REQUEST_TIMES:
        start_time = time.time()
    if key:
        headers = {
            "Authorization": f"Bearer {key}",
            "content-type": "application/json",
            "accept": "application/json",
        }
    else:
        headers = None
    try:
        r = requests.get(
            url, headers=headers, timeout=TIMEOUT, params=params, stream=True
        )
    except requests.exceptions.Timeout as e:
        cli.err_exit(TIMEOUT_MSG + str(*e.args))
    context_uid = r.headers.get("x-context-uid", "No context uid found.")
    if LOG_REQUEST_TIMES:
        end_time = time.time()
        cli.try_log(
            f"GET {url}: {end_time - start_time} seconds | {context_uid}"
        )
    if lib.DEBUG:
        print(
            f"Request to {url}\n\tcontext_uid: {context_uid}\n\tstatus: {r.status_code}"
        )
    if r.status_code == 404 and raise_notfound:
        raise NotFoundException()
    if r.status_code != 200:
        cli.err_exit(response_err_msg(r))
    return r


def post(url, data, key, raise_notfound=False, params=None):
    """
    Send a POST request to the specified URL with the provided data.

    Args:
        url (str): The URL to send the request to.
        data (dict): The data to include in the request body.
        key (str): The authorization key to include in the request headers.
        raise_notfound (bool, optional): Whether to raise a NotFoundException
            if the response status code is 404. Defaults to False.
        params (dict, optional): Additional query parameters to include in the
            request URL. Defaults to None.

    Returns:
        requests.Response: The response object.

    Raises:
        NotFoundException: If raise_notfound is True and the response status
            code is 404.
    """
    start_time = None
    if LOG_REQUEST_TIMES:
        start_time = time.time()
    headers = {"Authorization": f"Bearer {key}"}
    try:
        r = requests.post(
            url,
            json=data,
            headers=headers,
            timeout=TIMEOUT,
            params=params,
            stream=True,
        )
    except requests.exceptions.Timeout as e:
        cli.err_exit(TIMEOUT_MSG + str(e.args))
    context_uid = r.headers.get("x-context-uid", "No context uid found.")
    if LOG_REQUEST_TIMES:
        end_time = time.time()
        cli.try_log(
            f"POST {url}: {end_time - start_time} seconds | {context_uid}"
        )
    if lib.DEBUG:
        print(
            f"Request to {url}\n\tcontext_uid: {context_uid}\n\tstatus: {r.status_code}"
        )
    if r.status_code == 404 and raise_notfound:
        raise NotFoundException()
    if r.status_code != 200:
        cli.err_exit(response_err_msg(r))
    return r


def put(url, data, key, params=None):
    """
    Sends a PUT request to the specified URL with the provided data and key.

    Args:
        url (str): The URL to send the request to.
        data (dict): The data to include in the request body.
        key (str): The key used for authorization.

    Returns:
        requests.Response: The response object received from the server.

    Raises:
        requests.exceptions.Timeout: If the request times out.

    """
    start_time = None
    if LOG_REQUEST_TIMES:
        start_time = time.time()
    headers = {"Authorization": f"Bearer {key}"}
    try:
        r = requests.put(
            url,
            json=data,
            headers=headers,
            timeout=TIMEOUT,
            params=params,
            stream=True,
        )
    except requests.exceptions.Timeout as e:
        cli.err_exit(TIMEOUT_MSG + str(e.args))
    context_uid = r.headers.get("x-context-uid", "No context uid found.")
    if LOG_REQUEST_TIMES:
        end_time = time.time()
        cli.try_log(
            f"PUT {url}: {end_time - start_time} seconds | {context_uid}"
        )
    if lib.DEBUG:
        print(
            f"Request to {url}\n\tcontext_uid: {context_uid}\n\tstatus: {r.status_code}"
        )
    if r.status_code != 200:
        cli.err_exit(response_err_msg(r))
    return r


def delete(url, key):
    """
    Sends a DELETE request to the specified URL with the provided key as the
    authorization token.

    Args:
        url (str): The URL to send the DELETE request to.
        key (str): The authorization key to include in the request headers.

    Returns:
        requests.Response: The response object returned by the DELETE request.

    Raises:
        requests.exceptions.Timeout: If the request times out.
        cli.CLIError: If the response status code is not 200.

    """
    start_time = None
    if LOG_REQUEST_TIMES:
        start_time = time.time()
    headers = {"Authorization": f"Bearer {key}"}
    try:
        r = requests.delete(url, headers=headers, timeout=TIMEOUT)
    except requests.exceptions.Timeout as e:
        cli.err_exit(TIMEOUT_MSG + str(e.args))
    context_uid = r.headers.get("x-context-uid", "No context uid found.")
    if LOG_REQUEST_TIMES:
        end_time = time.time()
        cli.try_log(
            f"DELETE {url}: {end_time - start_time} seconds | {context_uid}"
        )
    if lib.DEBUG:
        print(
            f"Request to {url}\n\tcontext_uid: {context_uid}\n\tstatus: {r.status_code}"
        )
    if r.status_code != 200:
        cli.err_exit(response_err_msg(r))
    return r


def response_err_msg(r: requests.Response) -> str:
    """
    Generate an error message based on the given requests.Response object.

    Args:
        r (requests.Response): The response object to generate the error
            message from.

    Returns:
        str: The generated error message.

    """
    context_uid = r.headers.get("x-context-uid", "No context uid found.")
    msg = [f"{r.status_code}, {r.reason}", f"\tContext UID: {context_uid}"]
    if r.text:
        try:
            error = json.loads(r.text)
            if "msg" in error:
                msg.append(error["msg"])
            else:
                msg.append(f"{r.text}")
        except json.JSONDecodeError:
            msg.append(f"{r.text}")
    return "\n".join(msg)
