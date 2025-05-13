from unittest.mock import MagicMock, patch

import pytest

from spyctl.commands.apply_cmd.notification_target import (handle_apply_email_notification_target,
                                                           handle_apply_slack_notification_target)

# Sample resource data for a successful "create" (no UID)
sample_resrc_data = {
    "metadata": {
        "name": "email-target-1",
        "description": "test description",
        "tags": ["teamA", "critical"],
    },
    "spec": {"emails": ["alert@example.com"]},
}


@patch("spyctl.commands.apply_cmd.notification_target.cfg.get_current_context")
@patch("spyctl.commands.apply_cmd.notification_target.cli.try_log")
@patch("spyctl.commands.apply_cmd.notification_target.create_email_notification_target")
def test_handle_apply_email_notification_create(mock_create, mock_log, mock_ctx):
    mock_ctx.return_value.get_api_data.return_value = ("org", "api_key")
    mock_create.return_value = "email-uid-123"

    uid = handle_apply_email_notification_target(sample_resrc_data)

    # Assert
    mock_create.assert_called_once_with(
        "org",
        "api_key",
        name="email-target-1",
        emails=["alert@example.com"],
        description="test description",
        tags=["teamA", "critical"],
    )
    mock_log.assert_called_once_with(
        "Successfully created email notification target email-uid-123"
    )
    assert uid == "email-uid-123"


sample_slack_resrc_data = {
    "metadata": {
        "name": "slack-target-1",
        "description": "slack desc",
        "tags": ["devops", "alerts"],
    },
    "spec": {"url": "https://hooks.slack.com/services/test"},
}


@patch("spyctl.commands.apply_cmd.notification_target.cfg.get_current_context")
@patch("spyctl.commands.apply_cmd.notification_target.cli.try_log")
@patch("spyctl.commands.apply_cmd.notification_target.create_slack_notification_target")
def test_handle_apply_slack_notification_create(mock_create, mock_log, mock_ctx):
    # Setup
    mock_ctx.return_value.get_api_data.return_value = ("org", "api_key")
    mock_create.return_value = "slack-uid-456"

    uid = handle_apply_slack_notification_target(sample_slack_resrc_data)

    mock_create.assert_called_once_with(
        "org",
        "api_key",
        name="slack-target-1",
        url="https://hooks.slack.com/services/test",
        description="slack desc",
        tags=["devops", "alerts"],
    )
    mock_log.assert_called_once_with(
        "Successfully created slack notification target slack-uid-456"
    )
    assert uid == "slack-uid-456"


# TODO: Add pagerduty and webhook test
