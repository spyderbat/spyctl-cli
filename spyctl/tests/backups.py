"""Backup and restore the secrets file for testing purposes."""

import os
import shutil

from click.testing import CliRunner

from spyctl import spyctl


class SetupException(Exception):
    pass


CURRENT_CONTEXT = None


def backup_context():
    global CURRENT_CONTEXT
    CURRENT_CONTEXT = current_context()
    backup_secrets()


def restore_context():
    restore_secrets()
    if CURRENT_CONTEXT:
        use_current_context()


def backup_secrets():
    home_dir = os.path.expanduser("~")
    file_path = os.path.join(home_dir, ".spyctl/.secrets/secrets")
    backup_path = os.path.join(home_dir, ".spyctl/.secrets/secrets.bak")

    # Check if the file exists
    if not os.path.isfile(file_path):
        print(f"File {file_path} does not exist.")
        return

    # Backup the file
    shutil.copyfile(file_path, backup_path)
    print(f"File {file_path} has been backed up to {backup_path}.")


def restore_secrets():
    home_dir = os.path.expanduser("~")
    file_path = os.path.join(home_dir, ".spyctl/.secrets/secrets")
    backup_path = os.path.join(home_dir, ".spyctl/.secrets/secrets.bak")

    # Check if the backup file exists
    if not os.path.isfile(backup_path):
        print(f"Backup file {backup_path} does not exist.")
        return

    # Restore the file
    shutil.copyfile(backup_path, file_path)
    print(f"File {file_path} has been restored from {backup_path}.")
    # Remove the backup file
    os.remove(backup_path)


def current_context():
    runner = CliRunner()
    result = runner.invoke(
        spyctl.main,
        [
            "config",
            "current-context",
        ],
    )
    if result.exit_code != 0:
        raise SetupException("Unable get current context")
    current_ctx = result.output.strip("\n")
    return current_ctx


def use_current_context():
    if CURRENT_CONTEXT:
        runner = CliRunner()
        runner.invoke(spyctl.main, ["config", "use-context", CURRENT_CONTEXT])
