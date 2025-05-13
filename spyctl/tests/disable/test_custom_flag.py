from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from spyctl.commands.disable.custom_flag import (
    disable_custom_flag,
    handle_disable_custom_flag,
)


@patch("spyctl.commands.disable.custom_flag.cli.try_log")
@patch("spyctl.commands.disable.custom_flag.put_disable_custom_flag")
@patch("spyctl.commands.disable.custom_flag.cli.query_yes_no")
@patch("spyctl.commands.disable.custom_flag.get_custom_flags")
@patch("spyctl.commands.disable.custom_flag.cfg.get_current_context")
def test_disable_custom_flag_success(
    mock_get_context,
    mock_get_custom_flags,
    mock_query_yes_no,
    mock_put_disable_custom_flag,
    mock_try_log,
):
    mock_context = MagicMock()
    mock_context.get_api_data.return_value = ("apikey", "org_uid")
    mock_get_context.return_value = mock_context

    mock_get_custom_flags.return_value = (
        [{"uid": "flag:123", "name": "Test-Flag"}],
        {"count": 1},
    )

    mock_query_yes_no.return_value = True

    # actual function call.
    handle_disable_custom_flag("Test-Flag")

    # Assert
    mock_get_custom_flags.assert_called_once_with(
        "apikey", "org_uid", name_or_uid_contains="Test-Flag", page_size=-1
    )
    mock_query_yes_no.assert_called_once_with(
        "Are you sure you want to disable custom flag 'Test-Flag - flag:123'?"
    )
    mock_put_disable_custom_flag.assert_called_once_with(
        "apikey", "org_uid", "flag:123"
    )
    mock_try_log.assert_called_once_with(
        "Successfully disabled custom flag 'Test-Flag - flag:123'"
    )


@patch("spyctl.commands.disable.custom_flag.lib.err_exit")
@patch("spyctl.commands.disable.custom_flag.get_custom_flags")
@patch("spyctl.commands.disable.custom_flag.cfg.get_current_context")
def test_disable_custom_flag_not_found(
    mock_get_context,
    mock_get_custom_flags,
    mock_err_exit,
):
    mock_context = MagicMock()
    mock_context.get_api_data.return_value = ("apikey", "orguid")
    mock_get_context.return_value = mock_context

    mock_get_custom_flags.return_value = ([], None)

    runner = CliRunner()
    runner.invoke(disable_custom_flag, ["Missing-Flag"])

    mock_err_exit.assert_called_once_with(
        "No custom flags matching name_or_uid 'Missing-Flag'", None
    )
