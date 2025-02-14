"""Library functions for the 'get' command."""

from typing import Callable, Dict, List, Optional

import spyctl.spyctl_lib as lib
from spyctl import cli


def show_get_data(
    data: List[Dict],
    output: str,
    summary_func: Optional[Callable] = None,
    wide_func: Optional[Callable] = None,
    data_parser: Optional[Callable] = None,
    raw_data: bool = False,
):
    """
    Display the data obtained from the 'get' command.

    Args:
        data (List[Dict]): The data to be displayed.
        output (str): The desired output format.
        summary_func (Callable): The function to generate the summary of the
            data.
        data_parser (Callable): The function to parse the data for yaml or
            json output.
        raw_data (bool): Setting raw_data to true bypasses the data_parser
            callable if it exists.

    Returns:
        None
    """
    if output in [lib.OUTPUT_DEFAULT, lib.OUTPUT_WIDE]:
        if not wide_func and output == lib.OUTPUT_WIDE:
            output = lib.OUTPUT_DEFAULT
        if output == lib.OUTPUT_DEFAULT:
            if not summary_func:
                cli.try_log(
                    "This resource has no summary or wide output.\n"
                    "Use -o yaml or -o json to retrieve the raw data."
                )
                return
            summary = summary_func(data)
            cli.show(summary, lib.OUTPUT_RAW)
        elif output == lib.OUTPUT_WIDE:
            summary = wide_func(data)
            cli.show(summary, lib.OUTPUT_RAW)
    else:
        for rec in data:
            if data_parser and not raw_data:
                rec = data_parser(rec)
            cli.show(rec, output)


NOT_TIME_BASED = [
    lib.SOURCES_RESOURCE,
    lib.POLICIES_RESOURCE,
    lib.RULESETS_RESOURCE,
    lib.CLUSTERS_RESOURCE,
    lib.NOTIFICATION_CONFIGS_RESOURCE,
    lib.NOTIFICATION_TARGETS_RESOURCE,
    lib.NOTIFICATION_CONFIG_TEMPLATES_RESOURCE,
    lib.NOTIFICATION_TEMPLATES_RESOURCE,
    lib.SAVED_QUERY_RESOURCE,
    lib.CUSTOM_FLAG_RESOURCE,
    lib.AGENT_HEALTH_NOTIFICATION_RESOURCE,
    "configured notifications",
]


def output_time_log(resource, st, et):
    """
    Logs the time range for retrieving a specific resource.

    Args:
        resource (str): The name of the resource.
        st (int): The start time in epoch format.
        et (int): The end time in epoch format.
    """
    resrc_plural = lib.get_plural_name_from_alias(resource)
    if resrc_plural == lib.DEVIATIONS_RESOURCE.name_plural:
        resrc_plural = f"policy {resrc_plural}"
    if resrc_plural and resrc_plural not in NOT_TIME_BASED:
        cli.try_log(
            f"Getting {resrc_plural} from {lib.epoch_to_zulu(st)} to"
            f" {lib.epoch_to_zulu(et)}"
        )
    elif resrc_plural:
        cli.try_log(f"Getting {resrc_plural}")


def wildcard_name_or_id(name_or_id: str, exact: bool) -> str:
    """
    Return the name or id if it is a wildcard.

    Args:
        name_or_id (str): The name or id to check.
        exact (bool): Whether the name or id is an exact match.

    Returns:
        str: The name or id if it is a wildcard.
    """
    if name_or_id and not exact:
        name_or_id = name_or_id + "*" if name_or_id[-1] != "*" else name_or_id
        name_or_id = "*" + name_or_id if name_or_id[0] != "*" else name_or_id
    return name_or_id
