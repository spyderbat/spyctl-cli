import spyctl.api.agent_health as ah


def test_get_agent_health_notification_settings(mocker):
    mock_get = mocker.patch("spyctl.api.agent_health.get")

    mock_response = {
        "agent_health_notification_settings": {
            "apiVersion": "spyderbat/v1",
            "kind": "AgentHealthNotification",
            "metadata": {
                "name": "All-Agents",
                "uid": "ahn:2OXXXXXXXXXXXXX",
                "version": 1,
            },
            "spec": {
                "notification_settings": {
                    "agent_healthy": {
                        "uid": "nset:AXXXXXXXX",
                        "aggregate_seconds": 0,
                        "target_map": {"ntgt:rWfmdZj": ""},
                    }
                }
            },
        }
    }

    # Set mock return value for .json()
    mock_get.return_value.json.return_value = mock_response

    # Test args
    api_url = "https://fake-url.com"
    api_key = "fake-api-key"
    org_uid = "spyderbat"
    ahn_uid = "ahn:2OXXXXXXXXXXXXX"

    # Call the function
    result = ah.get_agent_health_notification_settings(
        api_url, api_key, org_uid, ahn_uid
    )

    # Assertions
    assert result["metadata"]["name"] == "All-Agents"
    assert "notification_settings" in result["spec"]


def test_delete_agent_health_notification_settings(mocker):
    api_url = "https://fake-url.com"
    api_key = "fake-api-key"
    org_uid = "spyderbat"
    ahn_uid = "ahn:2OXXXXXXXXXXXXX"

    mocker.patch("spyctl.api.agent_health.delete")
    ah.delete_agent_health_notification_settings(api_url, api_key, org_uid, ahn_uid)
