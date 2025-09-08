"""Handles the deletion of search sets."""

import json

import click

import spyctl.commands.delete.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.search_sets import (
    delete_search_set,
    get_search_sets,
)
from spyctl.resources import search_sets as ss


@click.command("search-set", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.delete_options
def delete_search_set_cmd(name_or_id, yes=False):
    """Delete a search set by name or uid"""
    if yes:
        cli.set_yes_option()
    handle_delete_search_set(name_or_id)


def handle_delete_search_set(name_or_uid):
    """
    Deletes a search set based on the provided name or UID.

    Args:
        name_or_uid (str): The name or UID of the search set to be deleted.

    Returns:
        None
    """
    ctx = cfg.get_current_context()
    params = {"name_or_uid_contains": name_or_uid}
    search_sets = get_search_sets(*ctx.get_api_data(), **params)
    if len(search_sets) == 0:
        cli.err_exit(f"No search sets matching name_or_uid '{name_or_uid}'")
    for search_set in search_sets:
        metadata = ss.data_to_yaml(search_set)["metadata"]
        name = metadata["name"]
        uid = metadata["uid"]
        perform_delete = cli.query_yes_no(
            f"Are you sure you want to delete search set '{name} - {uid}'?"
        )
        if perform_delete:
            delete_search_set(*ctx.get_api_data(), uid)
            cli.try_log(f"Successfully deleted search set '{name} - {uid}'")
        else:
            cli.try_log(f"Skipping delete of '{name} - {uid}'")
