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
def test_enable_saved_query_success(
    mock_get_context,
    mock_get_saved_queries,
    mock_put_enable_notifications,
    mock_try_log,
):
    mock_ctx = MagicMock()
    mock_ctx.get_api_data.return_value = ("apikey", "orgid")
    mock_get_context.return_value = mock_ctx

    mock_get_saved_queries.return_value = ([{"uid": "query:123"}], None)

    enable_cmd.callback("saved-query-name")

    mock_get_saved_queries.assert_called_once_with(
        "apikey", "orgid", name_or_uid_contains="saved-query-name"
    )
    mock_put_enable_notifications.assert_called_once_with(
        "apikey", "orgid", "query:123"
    )
    mock_try_log.assert_called_once_with(
        "Notifications for saved query 'saved-query-name' enabled"
    )


@patch("spyctl.commands.notifications.enable.saved_query.lib.err_exit")
@patch("spyctl.commands.notifications.enable.saved_query.get_saved_queries")
@patch("spyctl.commands.notifications.enable.saved_query.cfg.get_current_context")
def test_enable_saved_query_not_found(
    mock_get_context,
    mock_get_saved_queries,
    mock_err_exit,
):
    mock_ctx = MagicMock()
    mock_ctx.get_api_data.return_value = ("apikey", "orgid")
    mock_get_context.return_value = mock_ctx

    mock_get_saved_queries.return_value = ([], None)

    enable_cmd.callback("missing-query")

    mock_err_exit.assert_called_once_with("Saved query 'missing-query' not found")
