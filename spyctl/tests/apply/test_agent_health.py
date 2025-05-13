from unittest.mock import MagicMock, patch

import pytest

from spyctl.commands.apply_cmd.agent_health import \
    handle_apply_agent_health_notification

# Sample data (no UID)
SAMPLE_CREATE_DATA = {
    "metadata": {
        "name": "test_name",
        "description": "test_desc",
    },
    "spec": {
        "scope_query": "test query",
        "notification_settings": {"mock_setting": True},
    },
}

# Sample data for update (with UID)
SAMPLE_UPDATE_DATA = {
    "metadata": {
        "uid": "ahn-1234",
        "name": "test_name",
        "description": "test_desc",
    },
    "spec": {
        "scope_query": "test query",
        "notification_settings": {"mock_setting": True},
    },
}


@patch("spyctl.commands.apply_cmd.agent_health.cfg.get_current_context")
@patch("spyctl.commands.apply_cmd.agent_health.cli.try_log")
@patch(
    "spyctl.commands.apply_cmd.agent_health.post_new_agent_health_notification_settings"
)
def test_handle_apply_cmd_create(mock_post, mock_log, mock_ctx):
    # Setup
    mock_ctx.return_value.get_api_data.return_value = ("org", "key")
    mock_post.return_value = "ahn:new"

    uid = handle_apply_agent_health_notification(SAMPLE_CREATE_DATA)

    # Assertions
    mock_post.assert_called_once()
    mock_log.assert_called_once_with(
        "Successfully created agent health notification ahn:new"
    )
    assert uid == "ahn:new"


@patch("spyctl.commands.apply_cmd.agent_health.cfg.get_current_context")
@patch("spyctl.commands.apply_cmd.agent_health.cli.try_log")
@patch(
    "spyctl.commands.apply_cmd.agent_health.put_update_agent_health_notification_settings"
)
def test_handle_apply_cmd_update(mock_put, mock_log, mock_ctx):
    mock_ctx.return_value.get_api_data.return_value = ("org", "key")

    uid = handle_apply_agent_health_notification(SAMPLE_UPDATE_DATA)

    # Assert
    mock_put.assert_called_once()
    mock_log.assert_called_once_with(
        "Successfully created agent health notification ahn-1234"
    )
    assert uid == "ahn-1234"


@patch("spyctl.commands.apply_cmd.agent_health.cfg.get_current_context")
@patch("spyctl.commands.apply_cmd.agent_health.cli.try_log")
@patch(
    "spyctl.commands.apply_cmd.agent_health.put_update_agent_health_notification_settings"
)
def test_handle_apply_cmd_update_from_edit(mock_put, mock_log, mock_ctx):
    mock_ctx.return_value.get_api_data.return_value = ("org", "key")

    uid = handle_apply_agent_health_notification(SAMPLE_UPDATE_DATA, from_edit=True)

    # Assert
    mock_put.assert_called_once()
    mock_log.assert_called_once_with(
        "Successfully edited agent health notification ahn-1234"
    )
    assert uid == "ahn-1234"
