"""Command handling the creation of custom flags."""

import click

import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.custom_flags import get_custom_flag
from spyctl.api.saved_queries import get_saved_query
from spyctl.commands import search
from spyctl.commands.apply_cmd.apply import handle_apply_custom_flag
from spyctl.resources.custom_flags import data_to_yaml


@click.command("custom-flag", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
@click.argument("name", required=True)
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
    help="Apply the custom flag during creation.",
)
@click.option(
    "-d",
    "--description",
    help="A description explaining what the flag detects.",
    required=True,
    metavar="",
)
@click.option(
    "-q",
    "--query",
    help="Objects matching this query + schema combination will be flagged."
    " If used, this will create a saved query.",
    metavar="",
)
@click.option(
    "-s",
    "--schema",
    help="The schema for the SpyQL query used by the custom flag."
    " If used, this will create a saved query.",
    metavar="",
)
@click.option(
    "-Q",
    "--saved-query",
    help="The UID of a previously saved query. If used, this will override"
    " the query and schema options.",
    metavar="",
)
@click.option(
    "-t",
    "--type",
    help=f"The type of the custom flag. One of {lib.FLAG_TYPES}.",
    type=click.Choice(lib.FLAG_TYPES, case_sensitive=False),
    default=lib.FLAG_TYPE_RED,
    metavar="",
)
@click.option(
    "-S",
    "--severity",
    help=f"The severity of the custom flag. One of {lib.ALLOWED_SEVERITIES}.",
    type=click.Choice(lib.ALLOWED_SEVERITIES, case_sensitive=False),
    required=True,
    metavar="",
)
@click.option(
    "-D",
    "--disable",
    is_flag=True,
    help="Disable the custom flag on creation.",
    metavar="",
)
@click.option(
    "-T",
    "--tags",
    help="The tags associated with the custom flag. Comma delimited.",
    type=lib.ListParam(),
    metavar="",
)
@click.option(
    "-i",
    "--impact",
    help="The impact of the custom flag on the organization.",
    metavar="",
)
@click.option(
    "-c",
    "--content",
    help="Markdown content describing extra details about the custom flag.",
    metavar="",
)
@click.option(
    "-N",
    "--saved_query_name",
    help="If a new saved query needs to be created, this overrides the"
    " auto-generated name.",
    metavar="",
)
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    help="Automatically answer yes to all prompts.",
)
def create_custom_flag(output, **kwargs):
    """Create a custom flag from a saved query.

    This command allows you to write custom detections using the
    Spyderbat Query Language (SpyQL).

    \b
    At a minimum you must provide the following:
    - schema
    - query
    - description
    - severity
    - name

    \b
    To view available schema options run:
      'spyctl search --describe'
    To view available query fields for your schema run:
      'spyctl search --describe <schema>'
    Query operators are described here:
      https://docs.spyderbat.com/reference/search/search-operators

    \b
    Example:
    spyctl create custom-flag --schema Process --query "interactive = true and container_uid ~= '*'" --description "Detects interactive processes in containers" --severity high interactive-container-process
    """
    yes_option = kwargs.pop("yes")
    if yes_option:
        cli.set_yes_option()
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    search.load_schemas()
    handle_create_custom_flag(output, **kwargs)


def handle_create_custom_flag(output, **kwargs):
    """
    Create a custom flag.

    Args:
        output (str): The output format for displaying the custom flag.
        **kwargs: Additional keyword arguments for configuring the custom flag.

    Returns:
        None

    Raises:
        None
    """
    __validate_input(**kwargs)
    ctx = cfg.get_current_context()
    if output == lib.OUTPUT_DEFAULT:
        output = lib.OUTPUT_YAML
    cf_name = kwargs["name"]
    saved_query_uid = kwargs.get("saved_query")
    saved_query_name = kwargs.get("saved_query_name")
    if saved_query_uid:
        sq = get_saved_query(*ctx.get_api_data(), saved_query_uid)
        schema = sq["schema"]
        query = sq["query"]
    else:
        schema = kwargs["schema"]
        schema = search.TITLE_TO_SCHEMA_MAP.get(schema, schema)
        query = kwargs["query"]
    data = {
        "name": cf_name,
        "description": kwargs["description"],
        "severity": kwargs["severity"],
        "type": kwargs["type"],
        "query": query,
        "schema": schema,
    }
    if saved_query_uid:
        data["saved_query_uid"] = saved_query_uid
    for opt, req_field in {
        "disable": "is_disabled",
        "tags": "tags",
        "impact": "impact",
        "content": "content",
    }.items():
        if opt in kwargs:
            data[req_field] = kwargs[opt]
    custom_flag_rec = data_to_yaml(data)
    if kwargs.get("apply"):
        ctx = cfg.get_current_context()
        uid = handle_apply_custom_flag(custom_flag_rec, saved_query_name)
        cf = get_custom_flag(*ctx.get_api_data(), uid)
        model = data_to_yaml(cf)
    else:
        model = custom_flag_rec
    cli.show(model, output)


def __validate_input(**kwargs):
    query = kwargs.get("query")
    schema = kwargs.get("schema")
    saved_query_uid = kwargs.get("saved_query")
    if not saved_query_uid and (not query or not schema):
        cli.err_exit("Query and schema are required if saved query is not provided.")
