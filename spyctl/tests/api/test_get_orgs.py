"Handle the test for get orgs"

from spyctl.api.orgs import get_orgs


# Test get Orgs.
def test_get_orgs(mocker):
    mock_get = mocker.patch("spyctl.api.orgs.get")
    mock_response = [
        {"uid": "org1", "name": "Org One"},
        {"uid": "org2", "name": "Org Two"},
    ]
    mock_get.return_value.json.return_value = mock_response

    api_url = "https://fake-url.com"
    api_key = "fake-api-key"
    org_uids, org_names = get_orgs(api_url, api_key)

    # Assert
    assert org_uids == ["org1", "org2"]
    assert org_names == ["Org One", "Org Two"]
    mock_get.assert_called_once_with(f"{api_url}/api/v1/org/", api_key)
