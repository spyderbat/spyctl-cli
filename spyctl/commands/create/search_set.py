"""Handles the creation of search sets."""

import csv
import json
from typing import IO, List

import click
import yaml

import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.search_sets import get_search_set
from spyctl.commands.apply_cmd.apply import handle_apply_search_set
from spyctl.resources import search_sets


@click.command("search-set", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
@click.option(
    "-o",
    "--output",
    default=lib.OUTPUT_DEFAULT,
    type=click.Choice(lib.OUTPUT_CHOICES, case_sensitive=False),
)
@click.option(
    "-a",
    "--apply",
    is_flag=True,
    help="Apply the search set during creation.",
)
@click.option(
    "-n",
    "--name",
    help="The name of the search set.",
    required=True,
)
@click.option(
    "-f",
    "--contents-file",
    help="File that contains the contents of the search set. Can be JSON, YAML, or CSV.",
    required=True,
    type=click.File(),
)
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    help="Automatically answer yes to all prompts.",
)
def create_search_set(output, **kwargs):
    """Create a search set."""
    yes_option = kwargs.pop("yes")
    if yes_option:
        cli.set_yes_option()
    handle_create_search_set(output, **kwargs)


def handle_create_search_set(output, **kwargs):
    """Handle the creation of a search set."""
    should_apply = kwargs.pop("apply")
    if output == lib.OUTPUT_DEFAULT:
        output = lib.OUTPUT_YAML
    name = kwargs["name"]
    contents = get_file_contents(kwargs["contents_file"])
    data = {"searchset": {"metadata": {"name": name}, "spec": contents}}
    search_set_resrc = search_sets.data_to_yaml(data)
    if should_apply:
        ctx = cfg.get_current_context()
        uid = handle_apply_search_set(search_set_resrc)
        model = get_search_set(*ctx.get_api_data(), uid)
        search_set_resrc = search_sets.data_to_yaml(model)
    cli.show(search_set_resrc, output)


def get_file_contents(contents_file: IO[str]) -> List[str]:
    fname = contents_file.name
    contents = []
    try:
        if fname.endswith(".json"):
            contents = json.load(contents_file)
        elif fname.endswith(".yaml") or fname.endswith(".yml"):
            contents = yaml.load(contents_file, lib.UniqueKeyLoader)
        elif fname.endswith(".csv"):
            for row in csv.reader(contents_file):
                contents.append(" ".join(row))
        else:
            lib.err_exit(f'Unrecognized file type "{fname}".')
    except Exception as e:
        lib.err_exit(f'Error decoding "{fname}": {" ".join(e.args)}')
    invalid = not isinstance(contents, list)
    if not invalid:
        for content in contents:
            if not isinstance(content, str):
                invalid = True
                break
    if invalid:
        lib.err_exit(f'"{fname}" does not contain an array of strings.')
    return contents
