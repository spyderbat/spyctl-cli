"""Contains functions specific to the Spydertraces resource."""

from typing import Dict, List, Tuple

from tabulate import tabulate

import spyctl.spyctl_lib as lib

SUMMARY_HEADERS = [
    "HIGHEST_SCORING_UID",
    "TRIGGER_NAME",
    "ROOT_PROCESS",
    "HIGHEST_SCORE",
    "COUNT",
    "LATEST_TIMESTAMP",
]

WIDE_HEADERS = [
    "HIGHEST_SCORING_UID",
    "TRIGGER_NAME",
    "ROOT_PROCESS",
    "HIGHEST_SCORE",
    "COUNT",
    "LATEST_TIMESTAMP",
    "TRIGGER_ANCESTORS",
    "TRIGGER_CLASS",
]


class TraceSummaryRow:
    """
    Represents a summary row for a trace.

    Attributes:
        trigger_name (str): The short name of the trigger.
        first_uid (int): The ID of the first trace.
        root_process (str): The name of the root process.
        highest_score (float): The highest score of the trace.
        count (int): The number of traces.
        latest_timestamp (int): The latest timestamp of the trace.
        trigger_ancestors (list): The ancestors of the trigger.
        trigger_class (str): The class of the trigger.
    """

    def __init__(self, trace: Dict, include_linkback: bool):
        self.trigger_name = trace["trigger_short_name"]
        self.highest_scoring_uid = trace["id"]
        self.root_process = trace["root_proc_name"]
        self.highest_score = trace["score"]
        self.count = 1
        self.latest_timestamp = trace["time"]
        self.trigger_ancestors = trace["trigger_ancestors"]
        self.trigger_class = trace["trigger_class"]
        self.include_linkback = include_linkback
        self.linkback = None
        if include_linkback:
            self.linkback = trace.get("linkback")

    def update(self, trace: Dict):
        """
        Updates the summary row with a new trace.

        Args:
            trace (dict): The trace to update the row with.
        """
        self.count += 1
        self.latest_timestamp = max(self.latest_timestamp, trace["time"])
        if trace["score"] > self.highest_score:
            self.highest_scoring_uid = trace["id"]
            self.highest_score = trace["score"]
            if self.include_linkback:
                self.linkback = trace.get("linkback")

    def as_row(self) -> List:
        """
        Returns the summary row as a list.

        Returns:
            list: The summary row as a list.
        """
        rv = [
            self.highest_scoring_uid,
            self.trigger_name,
            self.root_process,
            self.highest_score,
            self.count,
            lib.epoch_to_zulu(self.latest_timestamp),
        ]
        if self.include_linkback:
            rv.append(self.linkback)
        return rv

    def as_wide_row(self) -> List:
        """
        Returns the summary row as a wide list.

        Returns:
            list: The summary row as a wide list.
        """
        rv = [
            self.highest_scoring_uid,
            self.trigger_name,
            self.root_process,
            self.highest_score,
            self.count,
            lib.epoch_to_zulu(self.latest_timestamp),
            self.trigger_ancestors,
            self.trigger_class,
        ]
        if self.include_linkback:
            rv.append(self.linkback)
        return rv


def spydertraces_stream_summary_output(
    traces: List[Dict], wide: bool, include_linkback: bool
) -> str:
    """
    Generate a summary output of Spydertraces grouped by similar activity.

    Args:
        traces (List[Dict]): A list of dictionaries representing the traces.

    Returns:
        str: A string containing the summary output.

    """

    def make_key(trace: Dict) -> str:
        return (trace["trigger_ancestors"], trace["trigger_class"])

    trace_summary_rows: Dict[Tuple, TraceSummaryRow] = {}
    for trace in traces:
        key = make_key(trace)
        if key not in trace_summary_rows:
            trace_summary_rows[key] = TraceSummaryRow(trace, include_linkback)
        else:
            trace_summary_rows[key].update(trace)
    rv = ["Showing Spydertraces grouped by similar activity"]
    if wide:
        headers = WIDE_HEADERS
        data = [row.as_wide_row() for row in trace_summary_rows.values()]
    else:
        headers = SUMMARY_HEADERS
        data = [row.as_row() for row in trace_summary_rows.values()]
    if include_linkback:
        headers.append("LINKBACK")
    data.sort(key=lambda x: x[3], reverse=True)
    rv.append(
        tabulate(
            data,
            headers=headers,
            tablefmt="plain",
        )
    )
    return "\n".join(rv)
