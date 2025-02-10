"""Handles the creation of saved_queries."""

import click

import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.saved_queries import get_saved_query
from spyctl.commands import search
from spyctl.commands.apply_cmd.apply import handle_apply_saved_query
from spyctl.resources import saved_queries


@click.command("saved-query", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
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
    help="Apply the saved query during creation.",
)
@click.option(
    "-n",
    "--name",
    help="The name of the saved query.",
    default="",
)
@click.option(
    "-q",
    "--query",
    help="The query to be saved.",
    default="",
)
@click.option(
    "-d",
    "--description",
    help="A description of the saved query.",
    default="",
)
@click.option(
    "-s",
    "--schema",
    help="The schema of the saved query.",
    default="",
)
@click.option(
    "-S",
    "--auto-summarize",
    help="Enables automatic AI summarization of records that match the"
    " saved query if supported by the schema,"
    " and if the organization has opted in to AI summarization features.",
    is_flag=True,
)
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    help="Automatically answer yes to all prompts.",
)
def create_saved_query(output, **kwargs):
    """Create a saved query."""
    yes_option = kwargs.pop("yes")
    if yes_option:
        cli.set_yes_option()
    search.load_schemas()
    if kwargs.get("schema"):
        kwargs["schema"] = search.TITLE_TO_SCHEMA_MAP.get(
            kwargs["schema"], kwargs["schema"]
        )
    handle_create_saved_query(output, **kwargs)


def handle_create_saved_query(output, **kwargs):
    """Handle the creation of a saved query."""
    should_apply = kwargs.pop("apply")
    if output == lib.OUTPUT_DEFAULT:
        output = lib.OUTPUT_YAML
    auto_summarize = kwargs.pop("auto_summarize", False)
    additional_settings = None
    if auto_summarize:
        additional_settings = {
            "auto_ai_summarization": True,
        }
    data = {
        "name": kwargs.pop("name", ""),
        "query": kwargs.pop("query", ""),
        "schema": kwargs.pop("schema", ""),
        "description": kwargs.pop("description", ""),
        "additional_settings": additional_settings,
    }
    saved_query_resrc = saved_queries.data_to_yaml(data)
    if should_apply:
        ctx = cfg.get_current_context()
        uid = handle_apply_saved_query(saved_query_resrc)
        sq = get_saved_query(*ctx.get_api_data(), uid)
        model = saved_queries.data_to_yaml(sq)
    else:
        model = saved_query_resrc
    cli.show(model, output)
