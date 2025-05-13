import spyctl.commands.delete.policy as policy


def test_handle_delete_policy(mocker):
    mock_ctx = mocker.MagicMock()
    mock_ctx.get_api_data.return_value = ("api_url", "api_key", "org_uid")
    mocker.patch(
        "spyctl.commands.delete.policy.cfg.get_current_context",
        return_value=mock_ctx,
    )

    mocker.patch(
        "spyctl.commands.delete.policy.get_policies",
        return_value=(
            {
                "apiVersion": "spyderbat/v1",
                "kind": "SpyderbatPolicy",
                "metadata": {
                    "createdBy": "test@spyderbat.com",
                    "name": "test-policy",
                    "type": "trace",
                    "uid": "pol:AKFXXXX",
                    "version": 1,
                },
                "spec": {
                    "allowedFlags": [
                        {
                            "class": "redflag/proc/command/high_severity/hidden/python",
                            "display_name": "command_python",
                            "display_severity": "high",
                        },
                    ],
                },
            },
        ),
    )

    mocker.patch(
        "spyctl.commands.delete.policy.cli.query_yes_no",
        return_value=True,
    )

    mock_delete = mocker.patch("spyctl.commands.delete.policy.delete_policy")

    # call the actual function.
    policy.handle_delete_policy("test-policy")

    # # Confirm the delete was hit
    mock_delete.assert_called_once_with("api_url", "api_key", "org_uid", "pol:AKFXXXX")
