"""Tests for Athena search API"""

from unittest.mock import patch

import pytest

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
