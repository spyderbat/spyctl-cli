"""Handles the 'notifications' command group for spyctl."""

import click

import spyctl.spyctl_lib as lib
from spyctl.commands.notifications import list as list_notifications
from spyctl.commands.notifications.configure.custom_flag import (
    configure_custom_flag,
)
from spyctl.commands.notifications.configure.saved_query import (
    configure_saved_query,
)
from spyctl.commands.notifications.disable.custom_flag import (
    disable_custom_flag,
)
from spyctl.commands.notifications.disable.saved_query import (
    disable_saved_query,
)
from spyctl.commands.notifications.enable.custom_flag import enable_custom_flag
from spyctl.commands.notifications.enable.saved_query import enable_saved_query

# ----------------------------------------------------------------- #
#                      Notifications Subcommand                     #
# ----------------------------------------------------------------- #


@click.group("notifications", cls=lib.CustomSubGroup, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
def notifications():
    """Configure notifications for a Spyderbat resource."""


@notifications.group("configure", cls=lib.CustomSubGroup, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
def configure():
    """Configure notifications for a Spyderbat resource."""


configure.add_command(configure_custom_flag)
configure.add_command(configure_saved_query)


@notifications.group("enable", cls=lib.CustomSubGroup, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
def enable():
    """Enable notifications for a Spyderbat resource."""


enable.add_command(enable_custom_flag)
enable.add_command(enable_saved_query)


@notifications.group("disable", cls=lib.CustomSubGroup, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
def disable():
    """Disable notifications for a Spyderbat resource."""


disable.add_command(disable_custom_flag)
disable.add_command(disable_saved_query)

notifications.add_command(list_notifications.list_notifications)
