import pytest
import spyctl.commands.delete.agent_health as agent_health
from unittest.mock import MagicMock


def test_delete_agent_health_notification_settings_direct(mocker):
    # Minimal mocks to reach delete_agent_health_notification_settings
    mock_ctx = mocker.MagicMock()
    mock_ctx.get_api_data.return_value = ("api_url", "api_key", "org_uid")
    mocker.patch(
        "spyctl.commands.delete.agent_health.cfg.get_current_context",
        return_value=mock_ctx,
    )

    mocker.patch(
        "spyctl.commands.delete.agent_health.get_agent_health_notification_settings_list",
        return_value=([{"name": "health-flag", "uid": "uid123"}], None),
    )

    mocker.patch(
        "spyctl.commands.delete.agent_health.cli.query_yes_no", return_value=True
    )

    # ✅ Mock ONLY this function (the one you're focused on)
    mock_delete = mocker.patch(
        "spyctl.commands.delete.agent_health.delete_agent_health_notification_settings"
    )

    agent_health.handle_delete_agent_health_notification_settings("health-flag")

    # Confirm the delete was hit
    mock_delete.assert_called_once_with("api_url", "api_key", "org_uid", "uid123")
