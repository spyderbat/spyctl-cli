import spyctl.commands.delete.notification_target as notification_target


def test_handle_delete_notif_tgt(mocker):
    mock_ctx = mocker.MagicMock()
    mock_ctx.get_api_data.return_value = ("api_url", "api_key", "org_uid")
    mocker.patch(
        "spyctl.commands.delete.notification_target.cfg.get_current_context",
        return_value=mock_ctx,
    )

    mocker.patch(
        "spyctl.commands.delete.notification_target.get_notification_targets",
        return_value=(
            [
                {
                    "name": "Test-Target",
                    "description": "Test description",
                    "type": "email",
                    "uid": "ntgt:AuXXXXXXXXXXX",
                }
            ],
            None,
        ),
    )
    mocker.patch(
        "spyctl.commands.delete.notification_target.cli.query_yes_no", return_value=True
    )

    mock_delete = mocker.patch(
        "spyctl.commands.delete.notification_target.delete_notification_target"
    )

    mock_log = mocker.patch("spyctl.commands.delete.notification_target.cli.try_log")

    # Calling the actual function.
    notification_target.handle_delete_notif_tgt("Test-Target")

    mock_delete.assert_called_once_with(
        "api_url", "api_key", "org_uid", "ntgt:AuXXXXXXXXXXX"
    )
    mock_log.assert_called_with(
        "Successfully deleted notification target 'Test-Target - ntgt:AuXXXXXXXXXXX'"
    )
