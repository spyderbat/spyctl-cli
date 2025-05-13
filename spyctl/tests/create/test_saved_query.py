from unittest.mock import patch

from spyctl.commands.create.saved_query import handle_create_saved_query


@patch("spyctl.cli.show")
@patch("spyctl.commands.create.saved_query.get_saved_query")
@patch("spyctl.commands.create.saved_query.handle_apply_saved_query")
@patch("spyctl.config.configs.get_current_context")
def test_handle_create_saved_query_with_apply(
    mock_get_ctx, mock_handle_apply, mock_get_sq, mock_cli_show
):
    # Mock context and returned UID
    mock_get_ctx.return_value.get_api_data.return_value = ("org", "apikey")
    mock_handle_apply.return_value = "mock_uid"

    mock_get_sq.return_value = {
        "name": "Test Query",
        "query": "container.image = 'docker:latest'",
        "schema": "model_container",
        "description": "A test saved query",
    }

    kwargs = {
        "apply": True,
        "name": "Test Query",
        "query": "container.image = 'docker:latest'",
        "schema": "test.schema",
        "description": "A test saved query",
    }

    handle_create_saved_query("yaml", **kwargs)

    mock_get_sq.assert_called_once_with("org", "apikey", "mock_uid")
