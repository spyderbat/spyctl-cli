"""Handles the creation of Suppression Policy objects"""

from typing import Optional

import click

import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.api_testing import api_create_suppression_policy


@click.command(
    "trace-suppression-policy",
    cls=lib.CustomCommand,
    epilog=lib.SUB_EPILOG,
)
@click.help_option("-h", "--help", hidden=True)
@click.option(
    "-i",
    "--id",
    "trace_id",
    default=None,
    help="UID of the object to build a Suppression Policy from.",
    metavar="",
)
@click.option(
    "-o",
    "--output",
    default=lib.OUTPUT_DEFAULT,
    type=click.Choice(lib.OUTPUT_CHOICES, case_sensitive=False),
)
@click.option(
    "-u",
    "--include-user-scope",
    "include_users",
    help="Include user scope in the suppression policy. Default is False.",
    default=False,
    is_flag=True,
    metavar="",
)
@click.option(
    "-n",
    "--name",
    help="Optional name for the Suppression Policy, if not provided, a name"
    " will be generated automatically",
    metavar="",
)
@click.option(
    "-m",
    "--mode",
    type=click.Choice(lib.POL_MODES),
    default=lib.POL_MODE_ENFORCE,
    metavar="",
    help="This determines what the policy should do when applied and enabled."
    " Default is audit mode. Audit mode will generate log messages when a"
    " an object matches the policy and would be suppressed, but it will not"
    " suppress the object. Enforce mode actually suppress the object if it"
    " matches the policy.",
    hidden=False,
)
@click.option(
    "-a",
    "--api",
    "use_api",
    metavar="",
    default=False,
    hidden=True,
    is_flag=True,
)
@lib.tmp_context_options
@lib.colorization_option
def create_trace_suppression_policy(
    trace_id,
    output,
    name,
    colorize,
    mode,
    use_api,
    **selectors,
):
    """Create a Suppression Policy object from a file, outputted to stdout"""
    if not colorize:
        lib.disable_colorization()
    selectors = {
        key: value for key, value in selectors.items() if value is not None
    }
    org_uid = selectors.pop(lib.CMD_ORG_FIELD, None)
    api_key = selectors.pop(lib.API_KEY_FIELD, None)
    api_url = selectors.pop(lib.API_URL_FIELD, "https://api.spyderbat.com")
    if org_uid and api_key and api_url:
        cfg.use_temp_secret_and_context(org_uid, api_key, api_url)
    handle_create_trace_suppression_policy(
        trace_id,
        output,
        mode,
        name,
        use_api,
        **selectors,
    )


def handle_create_trace_suppression_policy(
    trace_id: Optional[str],
    output: str,
    mode: str,
    name: str = None,
    do_api: bool = False,
    **selectors,
):
    """
    Handles the creation of a trace suppression policy.

    Args:
        trace_id (Optional[str]): The ID of the suppression policy.
        output (str): The output format for the suppression policy.
        mode (str): The mode of the suppression policy.
        name (str, optional): The name of the suppression policy.
            Defaults to None.
        do_api (bool, optional): Flag indicating whether to use the API for
            creating the suppression policy. Defaults to False.
        **selectors: Additional selectors for the suppression policy.

    Returns:
        None
    """
    include_users = selectors.pop("include_users", False)
    if do_api:
        ctx = cfg.get_current_context()
        policy = api_create_suppression_policy(
            *ctx.get_api_data(),
            name,
            lib.POL_TYPE_TRACE,
            include_users,
            trace_id,
            **selectors,
        )
        cli.show(policy, lib.OUTPUT_RAW)
    else:
        pol = _r.suppression_policies.build_trace_suppression_policy(
            trace_id, include_users, mode, name
        )
        if output == lib.OUTPUT_DEFAULT:
            output = lib.OUTPUT_YAML
        cli.show(pol, output)
