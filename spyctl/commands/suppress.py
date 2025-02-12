"""Handles the suppress subcommand for spyctl."""

from typing import Dict

import click

import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.commands.apply_cmd import apply

# ----------------------------------------------------------------- #
#                       Suppress Subcommand                         #
# ----------------------------------------------------------------- #


@click.group("suppress", cls=lib.CustomSubGroup, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
def suppress():
    "Tune your environment by suppressing Spyderbat Resources"


@suppress.command("trace", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
@click.argument("trace_uid", required=True)
@click.option(
    "-u",
    "--include-users",
    help="Scope the trace suppression policy to the users found in the trace",
    metavar="",
    is_flag=True,
    default=False,
)
@click.option(
    "-n",
    "--name",
    help="Optional name for the Suppression Policy, if not provided, a name"
    " will be generated automatically",
    metavar="",
)
@click.option(
    "-y",
    "--yes",
    "--assume-yes",
    is_flag=True,
    help='Automatic yes to prompts; assume "yes" as answer to all prompts and'
    " run non-interactively.",
)
def suppress_spydertrace(include_users, yes, trace_uid, name):
    "Suppress one or many Spyderbat Resources"
    if yes:
        cli.set_yes_option()
    handle_suppress_trace_by_id(trace_uid, include_users, name)


# ----------------------------------------------------------------- #
#                        Suppress Handlers                          #
# ----------------------------------------------------------------- #


def handle_suppress_trace_by_id(trace_uid: str, include_users: bool, name: str):
    """
    Handles the suppression of a trace by its ID.

    Args:
        trace_uid (str): The ID of the trace to be suppressed.
        include_users (bool): Flag indicating whether to include user
            information in the suppression policy scope.

    Returns:
        None
    """
    pol = _r.suppression_policies.build_trace_suppression_policy(
        trace_uid, include_users, lib.POL_MODE_ENFORCE, name
    )
    if prompt_upload_policy(pol):
        apply.handle_apply_policy(pol)


def prompt_upload_policy(pol: Dict) -> bool:
    """
    Prompts the user to upload a trace suppression policy.

    Args:
        pol (TraceSuppressionPolicy): The trace suppression policy to prompt
            for.

    Returns:
        bool: True if the user chooses to upload the policy, False otherwise.
    """
    query = cli.make_yaml(pol)
    query += "\nSuppress spydertraces matching this policy?"
    return cli.query_yes_no(query)
