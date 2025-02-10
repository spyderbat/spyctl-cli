"""Handles the validate subcommand for spyctl."""

import json
from typing import IO, Any, Dict, List, Union

import click

import spyctl.config.configs as cfg
import spyctl.schemas_v2 as schemas
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.api_testing import api_validate

# ----------------------------------------------------------------- #
#                       Validate Subcommand                         #
# ----------------------------------------------------------------- #


@click.command("validate", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
@click.option(
    "-f",
    "--filename",
    "file",
    help="Target file to validate",
    metavar="",
    required=True,
    type=click.File(),
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
@lib.colorization_option
def validate(file, colorize, use_api):
    """Validate spyderbat resource and spyctl configuration files.

    \b
    example:
      spyctl validate -f my_policy.yaml
    """
    if not colorize:
        lib.disable_colorization()
    handle_validate(file, use_api)


# ----------------------------------------------------------------- #
#                        Validate Handlers                          #
# ----------------------------------------------------------------- #


def handle_validate(file: IO, do_api=False):
    if file and do_api:
        ctx = cfg.get_current_context()
        resrc_data = lib.load_file_for_api_test(file)
        data = {"object": resrc_data}
        invalid_message = api_validate(*ctx.get_api_data(), data)
        if not invalid_message:
            kind = resrc_data[lib.KIND_FIELD]
            cli.try_log(f"{kind} valid!")
        else:
            print(invalid_message)
    elif file:
        resrc_data = lib.load_resource_file(file, validate_cmd=True)
        if isinstance(resrc_data, list):
            cli.try_log("List of objects valid!")
        else:
            kind = resrc_data[lib.KIND_FIELD]
            cli.try_log(f"{kind} valid!")


def validate_json(json_data: Union[str, Any]) -> bool:
    if isinstance(json_data, str):
        obj = json.loads(json_data)
    else:
        obj = json_data
    if isinstance(obj, list):
        return validate_list(obj)
    if isinstance(obj, dict):
        return validate_object(obj)
    cli.err_exit(
        "Invalid Object to Validate, expect dictionary or list of"
        " dictionaries."
    )


def validate_list(objs: List):
    for i, obj in enumerate(objs):
        if isinstance(obj, Dict):
            if not validate_object(obj):
                cli.try_log(f"Object at index {i} is invalid. See logs.")
                return False
        else:
            cli.try_log(f"Invalid Object at index {i}, expect dictionary.")
            return False
    return True


def validate_object(obj: dict) -> bool:
    return schemas.valid_object(obj)
