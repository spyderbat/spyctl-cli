import zulu

from spyctl.api.sources import get_sources


def test_get_sources(mocker):
    # mock response for the source endpoint
    mock_sources_response = [
        {
            "uid": "mach:4ZOEHeyUTXX",
            "last_data": str(zulu.now().isoformat()),
            "last_stored_chunk_end_time": str(zulu.now().isoformat()),
            "name": "integration-Node",
            "description": "xyz",
        }
    ]

    # mock response for the agent/ endpoint
    mock_agents_response = [
        {
            "uid": "agent:123",
            "description": "Test Machine",
            "runtime_details": {"src_uid": "mach:4ZOEHeyXXXX"},
        }
    ]

    mock_get = mocker.patch("spyctl.api.sources.get")

    # Create a side effect
    mock_get.side_effect = [
        # First call returns source JSON
        type("Response", (), {"json": lambda: mock_sources_response}),
        # Second call returns agent JSON
        type("Response", (), {"json": lambda: mock_agents_response}),
    ]

    api_url = "https://fake-url.com"
    api_key = "fake-api-key"
    org_uid = "spyderbat"

    result = get_sources(api_url, api_key, org_uid)

    # Assert
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["uid"] == "mach:4ZOEHeyXXXX"
    assert result[0]["name"] == "Test Machine"
