from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from spyctl.commands.notifications.enable.custom_flag import enable_custom_flag


@patch("spyctl.commands.notifications.enable.custom_flag.lib.try_log")
@patch(
    "spyctl.commands.notifications.enable.custom_flag.put_enable_notification_settings"
)
@patch("spyctl.commands.notifications.enable.custom_flag.get_custom_flags")
@patch("spyctl.commands.notifications.enable.custom_flag.cfg.get_current_context")
def test_enable_custom_flag_success(
    mock_get_context,
    mock_get_custom_flags,
    mock_put_enable_notifications,
    mock_try_log,
):
    runner = CliRunner()

    # Setup context and mock return values
    mock_context = MagicMock()
    mock_context.get_api_data.return_value = ("apikey", "orgid")
    mock_get_context.return_value = mock_context

    mock_get_custom_flags.return_value = (
        [{"uid": "flag:123", "name": "Test-Flag"}],
        None,
    )

    result = runner.invoke(enable_custom_flag, ["Test-Flag"])

    assert result.exit_code == 0
    mock_get_custom_flags.assert_called_once_with(
        "apikey", "orgid", name_or_uid_contains="Test-Flag"
    )
    mock_put_enable_notifications.assert_called_once_with(
        "apikey",
        "orgid",
        "flag:123",
    )
    mock_try_log.assert_called_once_with(
        "Notifications for custom flag 'Test-Flag' enabled"
    )


@patch("spyctl.commands.notifications.enable.custom_flag.lib.err_exit")
@patch("spyctl.commands.notifications.enable.custom_flag.get_custom_flags")
@patch("spyctl.commands.notifications.enable.custom_flag.cfg.get_current_context")
def test_enable_custom_flag_not_found(
    mock_get_context,
    mock_get_custom_flags,
    mock_err_exit,
):
    mock_context = MagicMock()
    mock_context.get_api_data.return_value = ("apikey", "orguid")
    mock_get_context.return_value = mock_context

    mock_get_custom_flags.return_value = ([], None)

    runner = CliRunner()
    runner.invoke(enable_custom_flag, ["Missing-Flag"])

    mock_err_exit.assert_called_once_with(("Custom flag 'Missing-Flag' not found"))
