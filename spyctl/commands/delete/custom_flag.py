"""Handles the delete custom flag command"""

import click

import spyctl.commands.delete.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.custom_flags import delete_custom_flag, get_custom_flags
from spyctl.commands.delete import saved_query


@click.command("custom-flag", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.delete_options
def delete_custom_flag_cmd(name_or_id, yes=False):
    """Delete a custom flag by name or uid"""
    if yes:
        cli.set_yes_option()
    handle_delete_custom_flag(name_or_id)


def handle_delete_custom_flag(name_or_uid):
    """
    Deletes a custom flag based on the provided name or UID.

    Args:
        name_or_uid (str): The name or UID of the custom flag to be deleted.

    Returns:
        None
    """
    ctx = cfg.get_current_context()
    params = {"name_or_uid_contains": name_or_uid}
    custom_flags, _ = get_custom_flags(*ctx.get_api_data(), **params)
    if len(custom_flags) == 0:
        cli.err_exit(f"No custom flags matching name_or_uid '{name_or_uid}'")
    for custom_flag in custom_flags:
        name = custom_flag["name"]
        uid = custom_flag["uid"]
        saved_query_uid = custom_flag["saved_query_uid"]
        perform_delete = cli.query_yes_no(
            f"Are you sure you want to delete custom flag '{name} - {uid}'?"
        )
        if perform_delete:
            delete_custom_flag(
                *ctx.get_api_data(),
                uid,
            )
            cli.try_log(f"Successfully deleted custom flag '{name} - {uid}'")
            if cli.query_yes_no(
                "Would you also like to delete the associated saved query?"
            ):
                saved_query.handle_delete_saved_query(saved_query_uid)
        else:
            cli.try_log(f"Skipping delete of '{name} - {uid}'")
