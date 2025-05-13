from unittest.mock import patch

import pytest
from click.testing import CliRunner

from spyctl.commands.create.notification_template import (
    email,
    pagerduty,
    slack,
    webhook,
)


@patch("spyctl.cli.set_yes_option")
@patch("spyctl.cli.show")
@patch(
    "spyctl.commands.create.notification_template.handle_apply_notification_template"
)
@patch("spyctl.resources.notification_templates.data_to_yaml")
@patch("spyctl.config.configs.get_current_context")
def test_slack_command_basic(
    mock_get_ctx, mock_data_to_yaml, mock_handle_apply, mock_show, mock_set_yes
):
    runner = CliRunner()

    # Setup mocks
    mock_data_to_yaml.return_value = "mock_yaml"
    mock_get_ctx.return_value.get_api_data.return_value = ("org", "apikey")

    # Simulate CLI call
    result = runner.invoke(
        slack,
        [
            "--name",
            "SlackTemplate",
        ],
    )

    # Assertions
    assert result.exit_code == 0
    mock_data_to_yaml.assert_called()
    mock_show.assert_called_once_with("mock_yaml", "yaml")
    mock_set_yes.assert_not_called()
    mock_handle_apply.assert_not_called()


@patch("spyctl.cli.set_yes_option")
@patch("spyctl.cli.show")
@patch(
    "spyctl.commands.create.notification_template.handle_apply_notification_template"
)
@patch("spyctl.resources.notification_templates.data_to_yaml")
@patch("spyctl.config.configs.get_current_context")
def test_email_command_basic(
    mock_get_ctx, mock_data_to_yaml, mock_handle_apply, mock_show, mock_set_yes
):
    runner = CliRunner()

    # Setup mocks
    mock_data_to_yaml.return_value = "mock_yaml"
    mock_get_ctx.return_value.get_api_data.return_value = ("org", "apikey")

    # Simulate CLI call
    result = runner.invoke(
        email,
        [
            "--name",
            "EmailTemplate",
        ],
    )

    # Assertions
    assert result.exit_code == 0
    mock_data_to_yaml.assert_called()
    mock_show.assert_called_once_with("mock_yaml", "yaml")
    mock_set_yes.assert_not_called()
    mock_handle_apply.assert_not_called()


@patch("spyctl.cli.set_yes_option")
@patch("spyctl.cli.show")
@patch(
    "spyctl.commands.create.notification_template.handle_apply_notification_template"
)
@patch("spyctl.resources.notification_templates.data_to_yaml")
@patch("spyctl.config.configs.get_current_context")
def test_pagerduty_command_basic(
    mock_get_ctx, mock_data_to_yaml, mock_handle_apply, mock_show, mock_set_yes
):
    runner = CliRunner()

    # Setup mocks
    mock_data_to_yaml.return_value = "mock_yaml"
    mock_get_ctx.return_value.get_api_data.return_value = ("org", "apikey")

    # Simulate CLI call
    result = runner.invoke(
        pagerduty,
        [
            "--name",
            "PagerdutyTemplate",
        ],
    )

    # Assertions
    assert result.exit_code == 0
    mock_data_to_yaml.assert_called()
    mock_show.assert_called_once_with("mock_yaml", "yaml")
    mock_set_yes.assert_not_called()
    mock_handle_apply.assert_not_called()


@patch("spyctl.cli.set_yes_option")
@patch("spyctl.cli.show")
@patch(
    "spyctl.commands.create.notification_template.handle_apply_notification_template"
)
@patch("spyctl.resources.notification_templates.data_to_yaml")
@patch("spyctl.config.configs.get_current_context")
def test_webhook_command_basic(
    mock_get_ctx, mock_data_to_yaml, mock_handle_apply, mock_show, mock_set_yes
):
    runner = CliRunner()

    # Setup mocks
    mock_data_to_yaml.return_value = "mock_yaml"
    mock_get_ctx.return_value.get_api_data.return_value = ("org", "apikey")

    # Simulate CLI call
    result = runner.invoke(
        webhook,
        [
            "--name",
            "WebhookTarget",
        ],
    )

    # Assertions
    assert result.exit_code == 0
    mock_data_to_yaml.assert_called()
    mock_show.assert_called_once_with("mock_yaml", "yaml")
    mock_set_yes.assert_not_called()
    mock_handle_apply.assert_not_called()
