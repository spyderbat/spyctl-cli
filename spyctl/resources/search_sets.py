"""Contains functions specific to the search set resource."""

from typing import Dict, List

from tabulate import tabulate

import spyctl.schemas_v2 as schemas
import spyctl.spyctl_lib as lib


def data_to_yaml(data: Dict) -> Dict:
    """
    Convert data to a YAML representation of a SearchSetModel.

    Args:
        data (Dict): The data to be converted.

    Returns:
        Dict: The YAML representation of a SearchSetModel.
    """
    search_set = data["searchset"]
    set_meta = search_set["metadata"]
    metadata = schemas.SearchSetMetadataModel(
        name=set_meta["name"],
        creationTimestamp=set_meta.get("creationTimestamp"),
        createdBy=set_meta.get("createdBy"),
        lastUpdatedTimestamp=set_meta.get("lastUpdatedTimestamp"),
        lastUpdatedBy=set_meta.get("lastUpdatedBy"),
        uid=set_meta.get("uid"),
    )
    model = schemas.SearchSetModel(
        apiVersion=lib.API_VERSION,
        kind=lib.SEARCH_SET_KIND,
        metadata=metadata,
        spec=search_set["spec"],
    )
    return model.model_dump(exclude_unset=True, exclude_none=True, by_alias=True)


def yaml_to_data(search_set: Dict):
    """
    Convert a YAML representation of a SearchSetModel to data for the API.

    Args:
        search_set (Dict): The YAML representation of a SearchSetModel.

    Returns:
        Dict: The data for use in the API.
    """
    data = {"searchset": {**search_set}}
    del data["searchset"]["kind"]
    return data


SUMMARY_HEADERS = [
    "NAME",
    "UID",
    "ITEM COUNT",
]


def summary_output(sets: List[Dict]):
    """
    Print a summary of search sets.

    Args:
        sets (List[Dict]): The search sets to be summarized.
    """
    data = []
    for raw_set in sets:
        search_set = raw_set["searchset"]
        metadata = search_set[lib.METADATA_FIELD]
        data.append(
            [
                metadata[lib.NAME_FIELD],
                metadata[lib.METADATA_UID_FIELD],
                len(search_set[lib.SPEC_FIELD]),
            ]
        )
    return tabulate(data, headers=SUMMARY_HEADERS, tablefmt="plain")


WIDE_HEADERS = [
    "NAME",
    "UID",
    "CREATED",
    "LAST UPDATED",
    "ITEM COUNT",
    "ITEMS",
]


def wide_output(sets: List[Dict]):
    """
    Print a summary of search sets.

    Args:
        queries (List[Dict]): The search sets to be summarized.
    """
    data = []
    for raw_set in sets:
        search_set = raw_set["searchset"]
        metadata = search_set[lib.METADATA_FIELD]
        items = search_set[lib.SPEC_FIELD]
        data.append(
            [
                metadata[lib.NAME_FIELD],
                metadata[lib.METADATA_UID_FIELD],
                lib.epoch_to_zulu(metadata[lib.METADATA_CREATE_TIME]),
                lib.epoch_to_zulu(metadata[lib.METADATA_LAST_UPDATE_TIME]),
                len(items),
                lib.limit_line_length(", ".join(items)),
            ]
        )
    return tabulate(data, headers=WIDE_HEADERS, tablefmt="plain")
