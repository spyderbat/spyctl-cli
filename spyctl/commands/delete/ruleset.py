"""Handles the delete ruleset command"""

import click

import spyctl.commands.delete.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.rulesets import delete_ruleset, get_rulesets


@click.command("ruleset", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.delete_options
def delete_ruleset_cmd(name_or_id, yes=False):
    """Delete a ruleset by name or uid"""
    if yes:
        cli.set_yes_option()
    handle_delete_ruleset(name_or_id)


def handle_delete_ruleset(name_or_id):
    """Delete a ruleset by name or uid"""
    ctx = cfg.get_current_context()
    params = {"name_or_uid_contains": name_or_id}
    rulesets = get_rulesets(*ctx.get_api_data(), params=params)
    if not rulesets:
        cli.err_exit(f"No rulesets matching '{name_or_id}'")
    for rs in rulesets:
        name = rs[lib.METADATA_FIELD][lib.METADATA_NAME_FIELD]
        uid = rs[lib.METADATA_FIELD][lib.METADATA_UID_FIELD]
        perform_delete = cli.query_yes_no(
            f"Are you sure you want to delete ruleset '{name} - {uid}' from Spyderbat?"  # noqa
        )
        if perform_delete:
            delete_ruleset(
                *ctx.get_api_data(),
                rs[lib.METADATA_FIELD][lib.METADATA_UID_FIELD],
            )
            cli.try_log(f"Successfully deleted ruleset '{name} - {uid}'")
        else:
            cli.try_log(f"Skipping delete of '{name} -- {uid}'")
