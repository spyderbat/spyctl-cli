import spyctl.api.notification_templates as nt


def test_get_notification_template(mocker):
    mock_get = mocker.patch("spyctl.api.notification_templates.get")
    mock_get.return_value.json.return_value = {
        "notification_template": {
            "metadata": {"uid": "tmpl:MXXXXXXXXXXXXXX", "name": "test-tmpl"},
            "spec": {"body_text": "hello", "subject": "Spyderbat notification"},
        }
    }

    result = nt.get_notification_template(
        "https://fake-url.com", "fake-api-key", "org:1234", "tmpl:MXXXXXXXXXXXXXX"
    )

    assert result["metadata"]["uid"] == "tmpl:MXXXXXXXXXXXXXX"
    assert result["metadata"]["name"] == "test-tmpl"
    assert result["spec"]["body_text"] == "hello"


def test_get_notification_templates(mocker):
    mock_get = mocker.patch("spyctl.api.notification_templates.get")
    mock_get.return_value.json.return_value = {
        "notification_templates": [
            {"uid": "tmpl:1", "metadata": {"name": "Template 1"}},
            {"uid": "tmpl:2", "metadata": {"name": "Template 2"}},
        ],
        "total_pages": 1,
    }

    templates, total_pages = nt.get_notification_templates(
        "https://fake-url.com", "fake-api-key", "org:1234"
    )

    assert len(templates) == 2
    assert templates[0]["uid"] == "tmpl:1"
    assert total_pages == 1


def test_create_email_notification_template(mocker):
    mock_post = mocker.patch("spyctl.api.notification_templates.post")
    mock_post.return_value.json.return_value = {"uid": "tmpl:created123"}

    result = nt.create_email_notification_template(
        "https://fake-url.com",
        "fake-api-key",
        "org:1234",
        name="Welcome Email",
        subject="Hello!",
        body_html="<p>Hello</p>",
        body_text="Hello",
        description="Test email",
    )

    assert result == "tmpl:created123"
    mock_post.assert_called_once()


def test_update_email_notification_template(mocker):
    mock_put = mocker.patch("spyctl.api.notification_templates.put")
    mock_put.return_value.json.return_value = {
        "notification_template": {
            "metadata": {"uid": "tmpl:updated456", "name": "Updated Template"},
            "spec": {"subject": "Updated Subject", "body_text": "Updated body"},
        }
    }

    result = nt.update_email_notification_template(
        "https://fake-url.com",
        "fake-api-key",
        "org:1234",
        "tmpl:updated456",
        name="Updated Template",
        subject="Updated Subject",
        body_text="Updated body",
        clear_description=True,
        clear_tags=False,
    )

    assert result["metadata"]["uid"] == "tmpl:updated456"
    assert result["spec"]["subject"] == "Updated Subject"
    mock_put.assert_called_once()


def test_create_pagerduty_notification_template(mocker):
    mock_post = mocker.patch("spyctl.api.notification_templates.post")
    mock_post.return_value.json.return_value = {"uid": "tmpl:pagerduty123"}

    result = nt.create_pagerduty_notification_template(
        "https://fake-url.com",
        "fake-api-key",
        "org:5678",
        name="PD Template",
        severity="critical",
        summary="Alert summary",
        class_="SystemAlert",
        source="host-1",
        component="cpu",
        custom_details={"error_code": "500"},
        description="Template for PagerDuty alerts",
        group="infra",
        tags=["pagerduty", "alert"],
    )

    assert result == "tmpl:pagerduty123"
    mock_post.assert_called_once()


def test_update_pagerduty_notification_template(mocker):
    mock_put = mocker.patch("spyctl.api.notification_templates.put")
    mock_put.return_value.json.return_value = {
        "notification_template": {
            "metadata": {"uid": "tmpl:pdupd456", "name": "Updated PD Template"},
            "spec": {
                "severity": "warning",
                "summary": "Updated alert",
                "description": "Updated desc",
            },
        }
    }

    result = nt.update_pagerduty_notification_template(
        "https://fake-url.com",
        "fake-api-key",
        "org:5678",
        "tmpl:pdupd456",
        name="Updated PD Template",
        severity="warning",
        summary="Updated alert",
        description="Updated desc",
        clear_description=False,
        clear_tags=True,
    )

    assert result["metadata"]["uid"] == "tmpl:pdupd456"
    assert result["spec"]["severity"] == "warning"
    mock_put.assert_called_once()


def test_create_slack_notification_template(mocker):
    mock_post = mocker.patch("spyctl.api.notification_templates.post")
    mock_post.return_value.json.return_value = {"uid": "tmpl:slack123"}

    result = nt.create_slack_notification_template(
        "https://fake-url.com",
        "fake-api-key",
        "org:abcd",
        name="Slack Template",
        text="Incident occurred",
        blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": "Alert"}}],
        channel="#alerts",
        description="Slack alert template",
        tags=["slack", "incident"],
    )

    assert result == "tmpl:slack123"
    mock_post.assert_called_once()


def test_update_slack_notification_template(mocker):
    mock_put = mocker.patch("spyctl.api.notification_templates.put")
    mock_put.return_value.json.return_value = {
        "notification_template": {
            "metadata": {"uid": "tmpl:slack456", "name": "Updated Slack Template"},
            "spec": {
                "text": "Updated message",
                "channel": "#alerts",
                "description": "Updated Slack description",
            },
        }
    }

    result = nt.update_slack_notification_template(
        "https://fake-url.com",
        "fake-api-key",
        "org:abcd",
        "tmpl:slack456",
        name="Updated Slack Template",
        text="Updated message",
        channel="#alerts",
        description="Updated Slack description",
        clear_description=True,
        clear_tags=False,
    )

    assert result["metadata"]["uid"] == "tmpl:slack456"
    assert result["spec"]["text"] == "Updated message"
    mock_put.assert_called_once()
