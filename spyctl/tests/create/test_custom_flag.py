import pytest
from click.testing import CliRunner
from unittest.mock import patch
from spyctl.commands.create.custom_flag import handle_create_custom_flag


@patch("spyctl.config.configs.get_current_context")
@patch("spyctl.commands.create.custom_flag.get_saved_query")
@patch("spyctl.commands.create.custom_flag.cli.show")
def test_create_custom_flag(
    mock_current_context,
    mock_get_saved_query,
    mock_cli_show,
):

    mock_current_context.return_value.get_api_data.return_value = ("org", "apikey")

    mock_get_saved_query.return_value = {
        "name": "Test Query",
        "query": "container.image = 'docker:latest'",
        "schema": "model_container",
        "description": "A test saved query",
        "uid": "query:123",
    }

    # custom-flag kwargs
    kwargs = {
        "query": "container.image = 'docker:latest'",
        "schema": "test.schema",
        "description": "A test saved query",
        "severity": "low",
        "type": "redflag",
        "name": "Custom-Flag-01",
        "saved_query": "query:123",
        "saved_query_name": "test-query",
    }

    handle_create_custom_flag("yaml", **kwargs)

    mock_get_saved_query.assert_called_once_with("query:123")
    mock_cli_show.assert_called_once()
