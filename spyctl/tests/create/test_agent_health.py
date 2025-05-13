from unittest.mock import MagicMock, call, patch

from spyctl.commands.create.agent_health import (
    handle_create_agent_health_notification_settings,
    lib,
)


@patch("spyctl.commands.create.agent_health.cli.show")
@patch("spyctl.commands.create.agent_health.get_agent_health_notification_settings")
@patch("spyctl.commands.create.agent_health.handle_apply_agent_health_notification")
@patch("spyctl.commands.create.agent_health.data_to_yaml")
@patch("spyctl.commands.create.agent_health.get_target_map")
@patch("spyctl.config.configs.get_current_context")
def test_handle_create_agent_health_with_apply(
    mock_get_ctx,
    mock_get_target_map,
    mock_data_to_yaml,
    mock_handle_apply,
    mock_get_settings,
    mock_cli_show,
):
    # Setup
    mock_ctx = MagicMock()
    mock_ctx.get_api_data.return_value = ("api_key", "org_uid")
    mock_get_ctx.return_value = mock_ctx
    mock_data_to_yaml.side_effect = ["mock_yaml_1", "mock_yaml_2"]
    mock_handle_apply.return_value = "uid_123"
    mock_get_settings.return_value = MagicMock()

    kwargs = {
        "name": "test_settings",
        "description": "test desc",
        "scope_query": "test query",
        "is_disabled": True,
        "apply": True,
    }

    handle_create_agent_health_notification_settings(lib.OUTPUT_DEFAULT, **kwargs)

    # Assert
    assert mock_data_to_yaml.call_count == 2
    mock_handle_apply.assert_called_once()
    mock_get_settings.assert_called_once_with("api_key", "org_uid", "uid_123")
    mock_cli_show.assert_called_once_with("mock_yaml_2", lib.OUTPUT_YAML)
