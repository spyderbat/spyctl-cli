"""Handles the fetching of Resource logs from the API."""

import json
from typing import Dict, List

import spyctl.spyctl_lib as lib


def get_audit_events(
    api_url,
    api_key,
    org_uid,
    time,
    src_uid,
    msg_type=None,
    since_id=None,
    disable_pbar: bool = False,
) -> List[Dict]:
    """
    Retrieve audit log events from the API.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The organization UID.
        time (Tuple[int, int]): A tuple representing the start and end time o
            the events to retrieve.
        src_uid (str): The source UID.
        msg_type (str, optional): The type of message to filter by. Defaults
            to None.
        since_id (str, optional): The ID of the event to start retrieving from.
            Defaults to None.
        disable_pbar (bool, optional): Whether to disable the progress bar.
            Defaults to False.

    Returns:
        List[Dict]: A list of dictionaries representing the audit events.

    """
    audit_events = []
    # TODO: Add guardian logs to athena search
    return []
    for event_json in []:
        event = json.loads(event_json)
        audit_events.append(event)
    audit_events.sort(key=lambda event: event["time"])
    if since_id:
        for i, rec in enumerate(audit_events):
            if rec["id"] == since_id:
                if len(audit_events) > i + 1:
                    ind = i + 1
                    audit_events = audit_events[ind:]
                    break
                return []
    return audit_events


def get_audit_events_tail(
    api_url: str,
    api_key: str,
    org_uid: str,
    time: str,
    src_uid: str,
    tail: int = -1,  # -1 for all
    msg_type: str = None,
    since_id: str = None,
    disable_pbar: bool = False,
) -> List[Dict]:
    """
    Retrieves a tail of audit events based on the specified parameters.

    Args:
        api_url (str): The URL of the API.
        api_key (str): The API key for authentication.
        org_uid (str): The organization UID.
        time (str): The time of the audit events.
        src_uid (str): The source UID.
        tail (int, optional): The number of events to retrieve
            Defaults to -1, which retrieves all events.
        msg_type (str, optional): The type of message to filter by. Defaults
            to None, which retrieves all message types.
        since_id (str, optional): The ID of the event to start retrieving from.
            Defaults to None, which retrieves all events.
        disable_pbar (bool, optional): Whether to disable the progress bar.
            Defaults to False.

    Returns:
        List[Dict]: A list of audit events.

    """
    audit_events = get_audit_events(
        api_url,
        api_key,
        org_uid,
        time,
        src_uid,
        msg_type,
        since_id,
        disable_pbar=disable_pbar,
    )
    if tail > 0:
        return audit_events[-tail:]
    if tail == 0:
        return []
    return audit_events
