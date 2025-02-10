"""
A hidden command, used by support to assist with migrating documents
that need to be updated
"""

# pylint: disable=broad-exception-caught

from pathlib import Path
from typing import Optional

import click
import yaml

import spyctl.config.configs as cfg
import spyctl.resources.policies as p
import spyctl.spyctl_lib as lib
from spyctl.api.policies import get_policies
from spyctl.commands.apply_cmd import apply

# ----------------------------------------------------------------- #
#                    Hidden Update Subcommand                       #
# ----------------------------------------------------------------- #


@click.group(
    "update", cls=lib.CustomSubGroup, hidden=True, epilog=lib.SUB_EPILOG
)
@click.help_option("-h", "--help", hidden=True)
def update():
    pass


@update.command("response-actions", cls=lib.CustomCommand)
@click.help_option("-h", "--help", hidden=True)
@click.option(
    "-b",
    "--backup-file",
    "backup_file",
    help="location to place policy backups",
    type=click.Path(exists=True, writable=True, file_okay=False),
)
def update_response_actions(backup_file=None):
    handle_update_response_actions(backup_file)


@update.command("policy-modes", cls=lib.CustomCommand)
@click.help_option("-h", "--help", hidden=True)
@click.option(
    "-b",
    "--backup-file",
    "backup_file",
    help="location to place policy backups",
    required=True,
    type=click.Path(exists=True, writable=True, file_okay=False),
)
def update_policy_modes(backup_file=None):
    handle_update_policy_modes(backup_file)


# ----------------------------------------------------------------- #
#                         Update Handlers                           #
# ----------------------------------------------------------------- #


def handle_update_response_actions(backup_dir: Optional[str]):
    ctx = cfg.get_current_context()
    policies = get_policies(*ctx.get_api_data())
    if backup_dir:
        backup_path = Path(backup_dir)

    for policy in policies:
        pol_data = p.policies_output([policy])
        if backup_path:
            try:
                uid = pol_data[lib.METADATA_FIELD][lib.METADATA_UID_FIELD]
                outfile = Path.joinpath(backup_path, uid)
                print(f"Backing up {uid} tp {str(outfile)}")
                outfile.write_text(
                    yaml.dump(pol_data, sort_keys=False), encoding="utf-8"
                )
            except Exception:
                import traceback

                s = traceback.format_exc()
                print(s)
                lib.err_exit("Error saving policy backups.. canceling")
        del pol_data[lib.SPEC_FIELD][lib.RESPONSE_FIELD]
        pol_data = p.Policy(pol_data).as_dict()
        apply.handle_apply_policy(pol_data)


def handle_update_policy_modes(backup_dir: Optional[str]):
    ctx = cfg.get_current_context()
    print("Updating Guardian Policies")
    policies = get_policies(*ctx.get_api_data())
    if backup_dir:
        backup_path = Path(backup_dir)
    for policy in policies:
        pol_data = p.policies_output([policy])
        if backup_path:
            try:
                uid = pol_data[lib.METADATA_FIELD][lib.METADATA_UID_FIELD]
                outfile = Path.joinpath(backup_path, uid)
                print(f"Backing up {uid} tp {str(outfile)}")
                outfile.write_text(
                    yaml.dump(pol_data, sort_keys=False), encoding="utf-8"
                )
            except Exception:
                import traceback

                s = traceback.format_exc()
                print(s)
                lib.err_exit("Error saving policy backups.. canceling")
        mode = pol_data[lib.SPEC_FIELD].get(
            lib.POL_MODE_FIELD, lib.POL_MODE_ENFORCE
        )
        if mode not in lib.POL_MODES:
            mode = lib.POL_MODE_ENFORCE
        lib.try_log(
            f"Setting mode for policy"
            f" '{policy[lib.METADATA_FIELD][lib.METADATA_UID_FIELD]}' to"
            f" '{mode}'"
        )
        pol_data[lib.SPEC_FIELD][lib.POL_MODE_FIELD] = mode
        pol_data = p.Policy(pol_data).as_dict()
        apply.handle_apply_policy(pol_data)
    print("Updating Suppression Policies")
    policies = get_policies(
        *ctx.get_api_data(),
        params={lib.METADATA_TYPE_FIELD: lib.POL_TYPE_TRACE},
    )
    for policy in policies:
        if backup_path:
            try:
                uid = policy[lib.METADATA_FIELD][lib.METADATA_UID_FIELD]
                outfile = Path.joinpath(backup_path, uid)
                print(f"Backing up {uid} tp {str(outfile)}")
                outfile.write_text(
                    yaml.dump(policy, sort_keys=False), encoding="utf-8"
                )
            except Exception:
                import traceback

                s = traceback.format_exc()
                print(s)
                lib.err_exit("Error saving policy backups.. canceling")
        mode = policy[lib.SPEC_FIELD].get(
            lib.POL_MODE_FIELD, lib.POL_MODE_ENFORCE
        )
        if mode not in lib.POL_MODES:
            mode = lib.POL_MODE_ENFORCE
        lib.try_log(
            f"Setting mode for suppression policy"
            f" '{policy[lib.METADATA_FIELD][lib.METADATA_UID_FIELD]}' to"
            f" '{mode}'"
        )
        policy[lib.SPEC_FIELD][lib.POL_MODE_FIELD] = mode
        apply.handle_apply_policy(policy)
