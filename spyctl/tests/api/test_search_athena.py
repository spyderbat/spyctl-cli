"""Tests for Athena search API"""

# import pytest
# from unittest import mock
# from spyctl.api.athena_search import search_athena


# @mock.patch("spyctl.api.athena_search.post_new_search")
# @mock.patch("spyctl.api.athena_search.retrieve_search_data")
# @mock.patch("spyctl.api.athena_search.get_objects")
# def test_search_athena(
#     mock_get_objects, mock_retrieve_search_data, mock_post_new_search
# ):
#     # Mock API responses
#     mock_post_new_search.return_value = "mock_search_id"
#     mock_retrieve_search_data.side_effect = [
#         ([{"id": "123"}], "mock_token", 1),
#         ([], None, 0),
#     ]
#     mock_get_objects.return_value = [{"id": "123", "name": "mock_result"}]

#     # Call the function
#     results = search_athena(
#         api_url="https://mock-api.com",
#         api_key="mock_api_key",
#         org_uid="mock_org",
#         schema="mock_schema",
#         query="*",
#         start_time=1710000000,
#         end_time=1710003600,
#         quiet=True,
#     )

#     # Assertions
#     assert isinstance(results, list)
#     assert len(results) == 1
#     assert results[0]["id"] == "123"
#     assert results[0]["name"] == "mock_result"

#     mock_post_new_search.assert_called_once()
#     mock_retrieve_search_data.assert_called()
#     mock_get_objects.assert_called_once()


# @mock.patch("spyctl.api.athena_search.post_new_search", return_value="mock_search_id")
# @mock.patch(
#     "spyctl.api.athena_search.retrieve_search_data", return_value=("FAILED", None, 0)
# )
# def test_search_athena_retrieve_fails(mock_retrieve_search_data, mock_post_new_search):
#     """Test when retrieve_search_data fails"""
#     results = search_athena(
#         "mock-url", "mock-key", "mock-org", "mock-schema", "*", quiet=True
#     )
#     assert results == []


# @mock.patch("spyctl.api.athena_search.post_new_search", return_value="FAILED")
# def test_search_athena_fails(mock_post_new_search):
#     """Test that search_athena handles failure properly."""
#     results = search_athena(
#         "mock-url", "mock-key", "mock-org", "mock-schema", "*", quiet=True
#     )
#     assert results == []  # Should return an empty list on failure

import pytest
from unittest.mock import patch, MagicMock
from spyctl.api import athena_search


@pytest.fixture
def sample_kwargs():
    return {
        "start_time": 1609459200,
        "end_time": 1609462800,
        "use_pbar": False,
        "quiet": True,
        "desc": "Test Search",
    }


@patch("spyctl.api.athena_search.post")
@patch("spyctl.api.athena_search.cli.err_exit")
def test_post_new_search_success(mock_err_exit, mock_post):
    mock_post.return_value.json.return_value = {"id": "search_123"}
    search_id = athena_search.post_new_search(
        "http://api.test",
        "apikey",
        "org123",
        "proc",
        "select * from proc",
        start_time=0,
        end_time=1,
    )
    assert search_id == "search_123"
    mock_err_exit.assert_not_called()


@patch("spyctl.api.athena_search.post")
@patch("spyctl.api.athena_search.cli.err_exit")
def test_post_new_search_failure(mock_err_exit, mock_post):
    mock_post.return_value.json.return_value = {"error": "Invalid schema"}
    athena_search.post_new_search(
        "http://api.test",
        "apikey",
        "org123",
        "proc",
        "select * from proc",
        start_time=0,
        end_time=1,
    )
    mock_err_exit.assert_called_once_with("Invalid schema")


@patch("spyctl.api.athena_search.post")
@patch("spyctl.api.athena_search.cli.err_exit")
def test_retrieve_search_data_completed(mock_err_exit, mock_post):
    mock_post.return_value.json.return_value = {
        "results": [{"id": "obj1"}],
        "token": None,
        "result_count": 1,
    }
    results, token, count = athena_search.retrieve_search_data(
        "http://api.test", "apikey", "org123", "search_123", token=None
    )
    assert results == [{"id": "obj1"}]
    assert token is None
    assert count == 1
    mock_err_exit.assert_not_called()


@patch("spyctl.api.athena_search.post")
@patch("spyctl.api.athena_search.cli.err_exit")
def test_validate_search_query_error(mock_err_exit, mock_post):
    mock_post.return_value.json.return_value = {"ok": False, "error": "Invalid query"}
    error_msg = athena_search.validate_search_query(
        "http://api.test", "apikey", "org123", "proc", "bad query"
    )
    assert error_msg == "Invalid query"
    mock_err_exit.assert_not_called()
