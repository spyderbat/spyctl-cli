"""Handles the 'disable' command group for spyctl."""

import click
import spyctl.spyctl_lib as lib
from spyctl.commands.disable import (
    custom_flag,
)

# ----------------------------------------------------------------- #
#                         Disable Subcommand                        #
# ----------------------------------------------------------------- #


@click.group("disable", cls=lib.CustomSubGroup, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
def disable():
    """Disable a Spyderbat resource."""


disable.add_command(custom_flag.disable_custom_flag)
