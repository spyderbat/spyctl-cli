"""Handles the delete policy command"""

import click
import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
from spyctl import cli
import spyctl.commands.delete.shared_options as _so
from spyctl.api.policies import delete_policy, get_policies


@click.command("policy", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.delete_options
def delete_policy_cmd(name_or_id, yes=False):
    """Delete a policy by name or uid"""
    if yes:
        cli.set_yes_option()
    handle_delete_policy(name_or_id)


def handle_delete_policy(name_or_uid):
    ctx = cfg.get_current_context()
    params = {"name_or_uid_contains": name_or_uid}
    policies = get_policies(*ctx.get_api_data(), params=params)
    if len(policies) == 0:
        cli.err_exit(f"No policies matching name_or_uid '{name_or_uid}'")
    for policy in policies:
        name = policy[lib.METADATA_FIELD][lib.METADATA_NAME_FIELD]
        uid = policy[lib.METADATA_FIELD][lib.METADATA_UID_FIELD]
        perform_delete = cli.query_yes_no(
            f"Are you sure you want to delete policy '{name} - {uid}' from"
            " Spyderbat?"
        )
        if perform_delete:
            delete_policy(
                *ctx.get_api_data(),
                uid,
            )
            cli.try_log(f"Successfully deleted policy '{name} - {uid}'")
        else:
            cli.try_log(f"Skipping delete of '{name} - {uid}'")
