"""Handles all the API calls related to reports."""

from typing import Dict

from spyctl.api.primitives import delete, get, post


def get_report_inventory(api_url: str, api_key: str, org_uid: str):
    """
    Retrieves the report inventory for a given organization.

    Args:
        api_url (str): The base URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.

    Returns:
        dict: The report inventory as a JSON object.

    Raises:
        Any exceptions raised by the `get` function.

    """
    url = f"{api_url}/api/v1/org/{org_uid}/spyctl/report/inventory"
    resp = get(url, api_key)
    if resp.status_code == 200:
        return resp.json()
    return None


def generate_report(api_url: str, api_key: str, org_uid: str, report_data: Dict):
    """
    Generate a report using the provided API URL, API key, organization UID,
    and report data.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The UID of the organization.
        report_data (Dict): The data for generating the report.

    Returns:
        dict: The response from the API.

    """
    url = f"{api_url}/api/v1/org/{org_uid}/spyctl/report"
    if "api_key" not in report_data:
        report_data["api_key"] = api_key
    if "api_url" not in report_data:
        report_data["api_url"] = api_url
    resp = post(url, report_data, api_key)
    return resp


def get_report_status(api_url: str, api_key: str, org_uid: str, rid: str):
    """
    Retrieves the status of a report from the specified API endpoint.

    Args:
        api_url (str): The base URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        rid (str): The identifier of the report.

    Returns:
        dict: A dictionary containing the report status information.

    Raises:
        Any exceptions that may occur during the API request.

    """
    url = f"{api_url}/api/v1/org/{org_uid}/spyctl/report/status/{rid}"
    resp = get(url, api_key)
    if resp.status_code == 200:
        return resp.json()
    return None


def get_report_download(api_url: str, api_key: str, org_uid: str, rid: str, fmt: str):
    """
    Downloads a report from the specified API URL using the provided API key.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        rid (str): The identifier of the report to download.
        fmt (str): The format of the report (e.g., 'pdf', 'csv').

    Returns:
        bytes: The content of the downloaded report.

    Raises:
        Any exceptions raised by the `get` function.

    """
    url = f"{api_url}/api/v1/org/{org_uid}/spyctl/report/download/{rid}.{fmt}"
    resp = get(url, api_key)
    if resp.status_code == 200:
        return resp.content
    return None


def delete_report(api_url: str, api_key: str, org_uid: str, rid: str):
    """
    Deletes a report with the given report ID.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.
        rid (str): The ID of the report to be deleted.

    Returns:
        dict: The JSON response from the API.

    Raises:
        Any exceptions raised by the `delete` function.
    """
    url = f"{api_url}/api/v1/org/{org_uid}/spyctl/report/{rid}"
    resp = delete(url, api_key)
    if resp.status_code == 200:
        return resp.json()
    return None


def get_report_list(api_url: str, api_key: str, org_uid: str):
    """
    Retrieves a list of reports from the specified API endpoint.

    Args:
        api_url (str): The base URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The unique identifier of the organization.

    Returns:
        list: A list of reports in JSON format.

    """
    url = f"{api_url}/api/v1/org/{org_uid}/spyctl/report/"
    resp = get(url, api_key)
    if resp.status_code == 200:
        return resp.json()
    return None
