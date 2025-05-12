from unittest.mock import patch, MagicMock
from spyctl.commands.notifications.enable.saved_query import (
    enable_saved_query as enable_cmd,
)


@patch("spyctl.commands.notifications.enable.saved_query.lib.try_log")
@patch(
    "spyctl.commands.notifications.enable.saved_query.put_enable_notification_settings"
)
@patch("spyctl.commands.notifications.enable.saved_query.get_saved_queries")
@patch("spyctl.commands.notifications.enable.saved_query.cfg.get_current_context")
def test_enable_saved_query_direct(
    mock_get_context,
    mock_get_saved_queries,
    mock_put_enable_notifications,
    mock_try_log,
):
    # Mock context and API data
    mock_context = MagicMock()
    mock_context.get_api_data.return_value = ("apikey", "orgid")
    mock_get_context.return_value = mock_context

    # Mock saved query lookup result
    mock_get_saved_queries.return_value = ([{"uid": "query:123"}], None)

    # Call command's callback directly with argument
    enable_cmd.callback("Test-SavedQuery")

    mock_get_saved_queries.assert_called_once_with(
        "apikey", "orgid", name_or_uid_contains="Test-SavedQuery"
    )
    mock_put_enable_notifications.assert_called_once_with(
        "apikey", "orgid", "query:123"
    )
    mock_try_log.assert_called_once_with(
        "Notifications for saved query 'Test-SavedQuery' enabled"
    )
