"Tests Get Clusters"

from spyctl.api.clusters import get_clusters


def test_get_clusters(mocker):
    # This is the fake API response from .json()
    mock_response = [
        {
            "uid": "clus:test",
            "name": "learn-vault",
            "org_uid": "spyderbat",
            "cluster_details": {
                "cluster_uid": "1aa8e489-82af-43c9-xxxx-xxxxxxxxx",
                "cluster_name": "learn-vault",
                "agent_uid": "muid:test",
                "src_uid": "QeSrTQkX",
                "cluid": "clus:test",
            },
            "valid_from": "2025-03-18T18:40:18Z",
            "valid_to": "0001-01-01T00:00:00Z",
        }
    ]

    # Mock the 'get' function inside spyctl.api.clusters
    mock_get = mocker.patch("spyctl.api.clusters.get")
    mock_get.return_value.json.return_value = mock_response

    api_url = "https://fake-url.com"
    api_key = "fake-api-key"
    result = get_clusters(api_url, api_key, "spyderbat")

    # Assert that the data was processed correctly
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["uid"] == "clus:test"
