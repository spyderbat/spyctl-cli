import pytest
from unittest.mock import patch, MagicMock
from spyctl.commands.create.agent_health import (
    handle_create_agent_health_notification_settings,
)
from spyctl import cfg, schemas, lib, cli
from spyctl.commands.create.notification_target import get


@pytest.fixture
def mock_cfg():
    mock = MagicMock()
    mock.get_current_context.return_value = MagicMock()
    return mock


@pytest.fixture
def mock_get_target_map():
    return MagicMock(return_value={"target_type": "test", "target_ids": ["id1"]})


@pytest.fixture
def mock_data_to_yaml():
    return MagicMock(side_effect=lambda data: f"YAML: {data}")


@pytest.fixture
def mock_handle_apply_agent_health_notification():
    return MagicMock(return_value="mocked_uid")


@pytest.fixture
def mock_get_agent_health_notification_settings():
    return MagicMock(
        return_value={"name": "test_settings", "notification_settings": {}}
    )


@pytest.fixture
def mock_cli_show():
    return MagicMock()


# def test_handle_create_agent_health_notification_settings_no_apply(
#         mock_cfg,
#         mock_get_target_map,
#         mock_data_to_yaml,
#         mock_handle_apply_agent_health_notification,
#         mock_get_agent_health_notification_settings,
#         mock_cli_show,
# ):
#     output = lib.OUTPUT_DEFAULT
#     kwargs = {
#         "name": "test_settings",
#         "description": "test desc",
#         "scope_query": "test query",
#         "is_disabled": True,
#     }

#     with patch("spyctl.cfg", mock_cfg):
#         patch("spyctl.commands.create.targets.get_target_map", mock_get_target_map),
#         patch("spyctl.commands.create.agent_health.data_to_yaml", mock_data_to_yaml),
#         patch(
#             "spyctl.commands.create.agent_health.handle_apply_agent_health_notification",
#             mock_handle_apply_agent_health_notification,
#         ),
#         patch(
#             "spyctl.commands.create.agent_health.get_agent_health_notification_settings",
#             mock_get_agent_health_notification_settings,
#         ),
#         patch("spyctl.cli.show", mock_cli_show),

#     handle_create_agent_health_notification_settings(output, **kwargs)

#     mock_cfg.get_current_context.assert_called_once()
#     mock_get_target_map.assert_not_called()
#     mock_data_to_yaml.assert_called_once_with(
#         {
#             "name": "test_settings",
#             "description": "test desc",
#             "scope_query": "test query",
#             "is_disabled": True,
#         }
#     )
#     mock_handle_apply_agent_health_notification.assert_not_called()
#     mock_get_agent_health_notification_settings.assert_not_called()
#     mock_cli_show.assert_called_once_with(
#         "YAML: {'name': 'test_settings', 'description': 'test desc', 'scope_query': 'test query', 'is_disabled': True}",
#         lib.OUTPUT_YAML,
#     )
