"Handle the test for Agents"

from spyctl.api.agents import get_sources_data_for_agents


# Test get Orgs.
def test_get_sources_data_for_agents(mocker):
    mock_get = mocker.patch("spyctl.api.agents.get")

    mock_agents_response = [
        {
            "muid": "mach:xxxxx",
            "uid": "agent:123",
            "description": "Test Machine",
            "runtime_details": {"src_uid": "mach:xxxxx"},
        }
    ]

    mock_response = [
        {
            "uid": "mach:xxxxx",
            "runtime_description": "integration-Node",
            "last_data": "2025-04-15T11:03:10Z",
            "runtime_details": {
                "cloud_region": "us-east-1",
                "cloud_type": "aws",
            },
        }
    ]

    mock_get.return_value.json.return_value = mock_response
    api_url = "https://fake-url.com"
    api_key = "fake-api-key"
    agents_result, sources_map = get_sources_data_for_agents(
        api_url, api_key, "spyderbat", mock_agents_response
    )

    # Assert

    assert len(agents_result) == 1
    assert agents_result[0]["uid"] == "agent:123"
    assert sources_map["mach:xxxxx"]["cloud_region"] == "us-east-1"
