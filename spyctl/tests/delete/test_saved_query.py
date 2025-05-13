import spyctl.commands.delete.saved_query as saved_query


def test_handle_delete_saved_query(mocker):
    mock_ctx = mocker.MagicMock()
    mock_ctx.get_api_data.return_value = ("api_url", "api_key", "org_uid")
    mocker.patch(
        "spyctl.commands.delete.saved_query.cfg.get_current_context",
        return_value=mock_ctx,
    )

    mocker.patch(
        "spyctl.commands.delete.saved_query.get_saved_queries",
        return_value=(
            [{"name": "saved-test-query", "uid": "sq123"}],
            None,
        ),
    )

    mocker.patch(
        "spyctl.commands.delete.saved_query.cli.query_yes_no",
        return_value=True,
    )

    mocker.patch(
        "spyctl.commands.delete.saved_query.get_saved_query_dependents",
        return_value=None,
    )

    mock_delete = mocker.patch("spyctl.commands.delete.saved_query.delete_saved_query")

    # call the actual function.
    saved_query.handle_delete_saved_query("saved-test-query")

    # # Confirm the delete was hit
    mock_delete.assert_called_once_with("api_url", "api_key", "org_uid", "sq123")
