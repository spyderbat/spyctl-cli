

import spyctl.commands.delete.custom_flag as custom_flag


def test_delete_custom_flag(mocker):
    # Minimal mocks to reach delete_agent_health_notification_settings
    mock_ctx = mocker.MagicMock()
    mock_ctx.get_api_data.return_value = ("api_url", "api_key", "org_uid")
    mocker.patch(
        "spyctl.commands.delete.custom_flag.cfg.get_current_context",
        return_value=mock_ctx,
    )

    mocker.patch(
        "spyctl.commands.delete.custom_flag.get_custom_flags",
        return_value=(
            [{"name": "custom-flag", "uid": "uid123", "saved_query_uid": "sq123"}],
            None,
        ),
    )

    mocker.patch(
        "spyctl.commands.delete.custom_flag.cli.query_yes_no",
        side_effect=[True, True],
    )

    mock_saved_query_delete = mocker.patch(
        "spyctl.commands.delete.custom_flag.saved_query.handle_delete_saved_query"
    )

    # ✅ Mock ONLY this function (the one you're focused on)
    mock_delete = mocker.patch("spyctl.commands.delete.custom_flag.delete_custom_flag")
    mocker.patch("spyctl.commands.delete.custom_flag.cli.try_log")
    # mocker.patch("spyctl.commands.delete.handle_custom_flag.handle_delete_custom_flag")

    custom_flag.handle_delete_custom_flag("custom-flag")

    # Confirm the delete was hit
    mock_delete.assert_called_once_with("api_url", "api_key", "org_uid", "uid123")
    mock_saved_query_delete.assert_called_once_with("sq123")
