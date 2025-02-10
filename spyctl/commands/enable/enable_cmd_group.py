"""Handle the enable subcommand group for spyctl."""

import click
import spyctl.spyctl_lib as lib
from spyctl.commands.enable import custom_flag

# ----------------------------------------------------------------- #
#                         Enable Subcommand                         #
# ----------------------------------------------------------------- #


@click.group("enable", cls=lib.CustomSubGroup, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
def enable():
    """Enable a Spyderbat resource."""


enable.add_command(custom_flag.enable_custom_flag)
