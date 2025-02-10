"""Handles the delete saved query command"""

import json

import click

import spyctl.commands.delete.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.saved_queries import (
    delete_saved_query,
    get_saved_queries,
    get_saved_query_dependents,
)


@click.command("saved-query", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.delete_options
def delete_saved_query_cmd(name_or_id, yes=False):
    """Delete a saved query by name or uid"""
    if yes:
        cli.set_yes_option()
    handle_delete_saved_query(name_or_id)


def handle_delete_saved_query(name_or_uid):
    """
    Deletes a saved query based on the provided name or UID.

    Args:
        name_or_uid (str): The name or UID of the saved query to be deleted.

    Returns:
        None
    """
    ctx = cfg.get_current_context()
    params = {"name_or_uid_contains": name_or_uid}
    queries, _ = get_saved_queries(*ctx.get_api_data(), **params)
    if len(queries) == 0:
        cli.err_exit(f"No saved queries matching name_or_uid '{name_or_uid}'")
    for query in queries:
        name = query["name"]
        uid = query["uid"]
        perform_delete = cli.query_yes_no(
            f"Are you sure you want to delete saved query '{name} - {uid}'?"
        )
        if perform_delete:
            deps = get_saved_query_dependents(*ctx.get_api_data(), uid)
            if deps:
                cli.err_exit(
                    f"Saved query '{name} - {uid}' has dependents and cannot"
                    " be deleted.\n"
                    f"{json.dumps(deps, indent=2)}"
                )
            delete_saved_query(
                *ctx.get_api_data(),
                uid,
            )
            cli.try_log(f"Successfully deleted saved query '{name} - {uid}'")
        else:
            cli.try_log(f"Skipping delete of '{name} - {uid}'")
