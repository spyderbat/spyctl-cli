import spyctl.api.custom_flags as cf


def test_get_custom_flag(mocker):
    mock_get = mocker.patch("spyctl.api.custom_flags.get")

    mock_response = {
        "custom_flag": {
            "apiVersion": "spyderbat/v1",
            "kind": "SpyderbatCustomFlag",
            "metadata": {
                "name": "cronjob_flag_r",
                "creationTimestamp": 1724088382,
                "uid": "flag:rXXXXXXXXXXXXXXX",
                "createdBy": "test@spyderbat.com",
                "lastUpdatedTimestamp": 1724088382,
                "version": 1,
                "savedQueryUID": "query:RXXXXXXXXXXXX",
                "schema": "model_k8s_cronjob",
            },
            "spec": {
                "enabled": True,
                "query": "metadata.name ~= '*'",
                "flagSettings": {
                    "type": "redflag",
                    "description": "cronjob found with critical severity",
                    "severity": "critical",
                },
                "notification_settings": {
                    "uid": "",
                    "aggregate": False,
                    "aggregate_seconds": 0,
                    "is_enabled": False,
                    "cooldown": 0,
                },
            },
        }
    }

    # Set mock return value for .json()
    mock_get.return_value.json.return_value = mock_response

    # Test args
    api_url = "https://fake-url.com"
    api_key = "fake-api-key"
    org_uid = "spyderbat"
    cf_uid = "flag:rXXXXXXXXXXXXXXX"

    # Call the function
    result = cf.get_custom_flag(api_url, api_key, org_uid, cf_uid)

    # Assertions
    assert result["metadata"]["name"] == "cronjob_flag_r"


def test_delete_custom_flag(mocker):
    api_url = "https://fake-url.com"
    api_key = "fake-api-key"
    org_uid = "spyderbat"
    cf_uid = "flag:rXXXXXXXXXXXXXXX"

    mocker.patch("spyctl.api.custom_flags.delete")
    cf.delete_custom_flag(api_url, api_key, org_uid, cf_uid)
