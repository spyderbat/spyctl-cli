import spyctl.api.notification_targets as nt
from spyctl.api.notification_targets import create_slack_notification_target


def test_get_notification_target(mocker):
    mock_get = mocker.patch("spyctl.api.notification_targets.get")

    mock_response = {
        "notification_target": {
            "apiVersion": "spyderbat/v1",
            "kind": "NotificationTarget",
            "metadata": {
                "name": "Test-Target",
                "description": "Test description",
                "type": "email",
                "uid": "ntgt:AuXXXXXXXXXXX",
                "creationTimestamp": 1736181337,
                "createdBy": "test@spyderbat.com",
            },
            "spec": {"emails": ["test406@gmail.com"]},
        }
    }

    # Set mock return value for .json()
    mock_get.return_value.json.return_value = mock_response

    api_url = "https://fake-url.com"
    api_key = "fake-api-key"
    org_uid = "spyderbat"
    nt_uid = "ntgt:AuXXXXXXXXXXX"

    result = nt.get_notification_target(api_url, api_key, org_uid, nt_uid)

    # Assert
    assert result["metadata"]["name"] == "Test-Target"


def test_delete_notification_target(mocker):
    api_url = "https://fake-url.com"
    api_key = "fake-api-key"
    org_uid = "spyderbat"
    nt_uid = "ntgt:AuXXXXXXXXXXX"

    mocker.patch("spyctl.api.notification_targets.delete")
    nt.delete_notification_target(api_url, api_key, org_uid, nt_uid)


def test_create_email_notification_target(mocker):
    mock_post = mocker.patch("spyctl.api.notification_targets.post")
    mock_post.return_value.json.return_value = {"uid": "ntgt:1234abcd"}

    api_url = "https://fake-url.com"
    api_key = "fake-api-key"
    org_uid = "org:abcd1234"
    name = "test-email-target"

    result = nt.create_email_notification_target(
        api_url,
        api_key,
        org_uid,
        name,
        emails=["test@example.com"],
        description="Test email target",
        tags=["alert"],
    )

    assert result == "ntgt:1234abcd"
    mock_post.assert_called_once_with(
        f"{api_url}/api/v1/org/{org_uid}/notificationtarget/email/",
        {
            "name": name,
            "emails": ["test@example.com"],
            "description": "Test email target",
            "tags": ["alert"],
        },
        api_key,
    )


def test_create_slack_notification_target(mocker):
    mock_post = mocker.patch("spyctl.api.notification_targets.post")
    mock_post.return_value.json.return_value = {"uid": "ntgt:slack5678"}

    api_url = "https://fake-url.com"
    api_key = "fake-api-key"
    org_uid = "org:xyz987"
    name = "test-slack-target"

    result = nt.create_slack_notification_target(
        api_url,
        api_key,
        org_uid,
        name,
        url="https://hooks.slack.com/test",
        description="Test slack target",
        tags=["slack", "team"],
    )

    assert result == "ntgt:slack5678"
    mock_post.assert_called_once_with(
        f"{api_url}/api/v1/org/{org_uid}/notificationtarget/slack/",
        {
            "name": name,
            "url": "https://hooks.slack.com/test",
            "description": "Test slack target",
            "tags": ["slack", "team"],
        },
        api_key,
    )


def test_update_email_notification_target(mocker):
    mock_put = mocker.patch("spyctl.api.notification_targets.put")
    mock_put.return_value.json.return_value = {
        "notification_target": {"uid": "ntgt:email1234", "name": "Updated Email Target"}
    }

    api_url = "https://fake-url.com"
    api_key = "fake-api-key"
    org_uid = "org:abcd123"
    ntgt_uid = "ntgt:email1234"

    result = nt.update_email_notification_target(
        api_url,
        api_key,
        org_uid,
        ntgt_uid,
        name="Updated Email Target",
        emails=["updated@example.com"],
        description="Updated description",
        tags=["team1"],
        clear_description=True,
        clear_tags=True,
    )

    assert result["name"] == "Updated Email Target"
    mock_put.assert_called_once_with(
        f"{api_url}/api/v1/org/{org_uid}/notificationtarget/email/{ntgt_uid}",
        {
            "name": "Updated Email Target",
            "emails": ["updated@example.com"],
            "description": "Updated description",
            "tags": ["team1"],
        },
        api_key,
        {"clear_description": True, "clear_tags": True},
    )


def test_update_slack_notification_target(mocker):
    mock_put = mocker.patch("spyctl.api.notification_targets.put")
    mock_put.return_value.json.return_value = {
        "notification_target": {"uid": "ntgt:slack5678", "name": "Updated Slack Target"}
    }

    api_url = "https://fake-url.com"
    api_key = "fake-api-key"
    org_uid = "org:xyz987"
    ntgt_uid = "ntgt:slack5678"

    result = nt.update_slack_notification_target(
        api_url,
        api_key,
        org_uid,
        ntgt_uid,
        name="Updated Slack Target",
        url="https://hooks.slack.com/updated",
        description="Slack updated",
        tags=["devops"],
        clear_description=False,
        clear_tags=True,
    )

    assert result["name"] == "Updated Slack Target"
    mock_put.assert_called_once_with(
        f"{api_url}/api/v1/org/{org_uid}/notificationtarget/slack/{ntgt_uid}",
        {
            "name": "Updated Slack Target",
            "url": "https://hooks.slack.com/updated",
            "description": "Slack updated",
            "tags": ["devops"],
        },
        api_key,
        {"clear_description": False, "clear_tags": True},
    )


def test_update_webhook_notification_target(mocker):
    mock_put = mocker.patch("spyctl.api.notification_targets.put")
    mock_put.return_value.json.return_value = {
        "notification_target": {
            "uid": "nt:webhook123",
            "name": "Updated Webhook Target",
            "url": "https://example.com/hook",
            "description": "Updated webhook description",
            "tags": ["webhook", "notification"],
        }
    }

    result = nt.update_webhook_notification_target(
        "https://fake-url.com",
        "fake-api-key",
        "org:abcd",
        "nt:webhook123",
        name="Updated Webhook Target",
        url="https://example.com/hook",
        description="Updated webhook description",
        tags=["webhook", "notification"],
        clear_description=False,
        clear_tags=False,
    )

    assert result["uid"] == "nt:webhook123"
    assert result["name"] == "Updated Webhook Target"
    assert result["url"] == "https://example.com/hook"
    mock_put.assert_called_once()


def test_update_pagerduty_notification_target(mocker):
    mock_put = mocker.patch("spyctl.api.notification_targets.put")
    mock_put.return_value.json.return_value = {
        "notification_target": {
            "uid": "nt:pagerduty456",
            "name": "Updated PagerDuty Target",
            "routing_key": "new-routing-key",
            "description": "Updated PagerDuty description",
            "tags": ["pagerduty", "incident"],
        }
    }

    result = nt.update_pagerduty_notification_target(
        "https://fake-url.com",
        "fake-api-key",
        "org:abcd",
        "nt:pagerduty456",
        name="Updated PagerDuty Target",
        routing_key="new-routing-key",
        description="Updated PagerDuty description",
        tags=["pagerduty", "incident"],
        clear_description=True,
        clear_tags=False,
    )

    assert result["uid"] == "nt:pagerduty456"
    assert result["name"] == "Updated PagerDuty Target"
    assert result["routing_key"] == "new-routing-key"
    mock_put.assert_called_once()
