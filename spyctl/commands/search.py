"""Handles the "search" command."""

import time
from dataclasses import dataclass
from typing import Dict, List

import click
import zulu
from tabulate import tabulate

from spyctl.commands.apply_cmd.apply import handle_apply_saved_query
import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.athena_search import search_athena, validate_search_query
from spyctl.api.primitives import get
from spyctl.api.saved_queries import get_saved_queries, put_update_last_used
import spyctl.resources as _r


@click.command("search", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@click.argument("schema", required=False, type=str)
@click.argument("query", required=False, type=str)
@click.help_option("-h", "--help", hidden=True)
@click.option(
    "-l",
    "--list-schemas",
    is_flag=True,
    help="",
)
@click.option(
    "-d",
    "--describe",
    is_flag=True,
    help="",
)
@click.option(
    "-o",
    "--output",
    type=click.Choice(
        [
            lib.OUTPUT_YAML,
            lib.OUTPUT_JSON,
            lib.OUTPUT_NDJSON,
            lib.OUTPUT_DEFAULT,
        ]
    ),
    default=lib.OUTPUT_DEFAULT,
    help="Output format.",
)
@click.option(
    "-t",
    "--start-time",
    "st",
    help="Start time of the query. Default is 24 hours ago.",
    default="24h",
    type=lib.time_inp,
)
@click.option(
    "-u",
    "--use-query",
    help="The name or uid of a saved query. Use 'spyctl get saved-queries' to"
    " list available saved queries.",
    metavar="",
)
@click.option(
    "-s",
    "--save-query",
    help="Save the query you use for future use. Once saved, you can use the"
    " --use-query option to run the query again. Supplying a value for this"
    "option will save the query with the given name.",
    is_flag=False,
    flag_value="__save__",
    default=None,
    metavar="",
)
@click.option(
    "-D",
    "--description",
    help="Provide a description of up to 500 characters when saving a query.",
    metavar="",
)
@click.option(
    "-S",
    "--skip-results",
    is_flag=True,
    help="Validates the query without retrieving results."
    " Also useful for saving a query",
)
@click.option(
    "-e",
    "--end-time",
    "et",
    help="End time of the query. Default is now.",
    default=time.time(),
    type=lib.time_inp,
)
@click.option(
    "-y",
    "--yes",
    "--assume-yes",
    is_flag=True,
    help='Automatic yes to prompts; assume "yes" as answer to all prompts'
    " and run non-interactively.",
)
def search(schema, query, output, st, et, **kwargs):
    """Search for objects in the given schema."""
    load_schemas()
    handle_search(schema, query, output, st, et, **kwargs)


TITLE_TO_SCHEMA_MAP = {}
SCHEMAS = {}


def handle_search(schema, query, output, st, et, **kwargs):
    """Handle the 'search' command."""
    schema = TITLE_TO_SCHEMA_MAP.get(schema, schema)
    list_schemas = kwargs.get("list_schemas")
    describe = kwargs.get("describe")
    sq_name_or_uid = kwargs.get("use_query")
    skip_results = kwargs.get("skip_results")
    description = kwargs.get("description")
    if (
        list_schemas
        or describe
        or (not any([schema, query]) and not sq_name_or_uid)
    ):
        # If we're here we're outputting schema information
        # not running a query
        handle_search_schema(output, schema)
        return
    ctx = cfg.get_current_context()
    # Check if we're using a saved query
    rsq = None
    if sq_name_or_uid:
        rsq = __retrieve_saved_query(ctx, sq_name_or_uid)
        schema = rsq.schema
        query = rsq.query
    if not query:
        lib.err_exit(
            "Use --describe to view available search fields, or provide a query."  # noqa
        )
    if not skip_results:
        results = search_athena(
            *ctx.get_api_data(), schema, query, start_time=st, end_time=et
        )
        if rsq:
            # Updated the last used time of the saved query
            put_update_last_used(*ctx.get_api_data(), rsq.uid)
        if output == lib.OUTPUT_DEFAULT:
            output = lib.OUTPUT_NDJSON
        for result in results:
            cli.show(result, output=output)
    else:
        cli.try_log("Validating query...")
        error = validate_search_query(*ctx.get_api_data(), schema, query)
        if error:
            cli.err_exit(error)
        cli.try_log("Query is valid.")
    if kwargs.get("save_query") and not rsq:
        __save_query(schema, query, kwargs["save_query"], description)


def __save_query(
    schema, query, query_name: str = None, description: str = None
):
    """
    Save a query to the database.

    Args:
        schema (str): The schema of the query.
        query (str): The query to be saved.

    Returns:
        None
    """
    description = description or ""
    if query_name in [None, "__save__"]:
        query_name = (
            f"{schema} - {zulu.now().format('YYYY-MM-ddTHH:mm:ss')} UTC"
        )
    yaml_dict = _r.saved_queries.data_to_yaml(
        {
            "name": query_name,
            "query": query,
            "schema": schema,
            "description": description,
        }
    )
    handle_apply_saved_query(yaml_dict)


def load_schemas():
    """Load the schemas for the search command."""
    ctx = cfg.get_current_context()
    api_url, api_key, org_uid = ctx.get_api_data()
    url = f"{api_url}/api/v1/org/{org_uid}/search/schema/"
    response = get(url, api_key)
    schemas: Dict[str, Dict] = response.json()
    SCHEMAS.update(schemas)
    TITLE_TO_SCHEMA_MAP.update({v["title"]: k for k, v in schemas.items()})


def handle_search_schema(output: str, schema: str = None):
    """Handle the 'search-schema' command."""
    if schema:
        handle_specific_schema(output, schema)
        return
    if lib.OUTPUT_DEFAULT:
        schemas_lines = [
            [f"  {v['title']}", f"({k})"] for k, v in SCHEMAS.items()
        ]
        schemas_lines.sort()
        output = lib.OUTPUT_RAW
        lines = ["Available Schemas:"]
        lines.append(tabulate(schemas_lines, tablefmt="plain"))
        schemas = "\n".join(lines)
    else:
        schemas = SCHEMAS
    cli.show(schemas, output=output)


def handle_specific_schema(output: str, schema):
    """Handle the 'search-schema' command for a specific schema."""
    schema_data = SCHEMAS.get(schema)
    if not schema_data:
        available = "\n" + "\n".join(["  " + s for s in SCHEMAS])
        cli.err_exit(
            f"{schema} is not a valid schema for athena search."
            f" Available schemas are:{available}"
        )
    if lib.OUTPUT_DEFAULT:
        output = lib.OUTPUT_RAW
        lines = [f"{schema_data['title']} ({schema})"]
        lines.append("  Fields:")
        lines.extend(__create_description_table(schema_data))
        if "joins" in schema_data:
            lines.append("  Joins:")
            lines.extend(__create_join_table(schema_data))
        schema_data = "\n".join(lines)
    else:
        schema_data = {schema: schema_data}
    cli.show(schema_data, output=output)


@dataclass
class RetrievedQuery:
    """Data from a retrieved query."""

    schema: str
    query: str
    uid: str


def __retrieve_saved_query(
    ctx: cfg.Context, saved_query_name_or_uid
) -> RetrievedQuery:
    """Retrieve a saved query by name or uid."""
    cli.try_log("Retrieving saved query...")
    saved_queries, _ = get_saved_queries(
        *ctx.get_api_data(),
        name_or_uid=saved_query_name_or_uid,
        name_or_uid_contains=saved_query_name_or_uid,
        page_size=1,
    )
    if not saved_queries:
        cli.err_exit(f"No saved queries matching '{saved_query_name_or_uid}'")
    saved_query = saved_queries[0]
    return RetrievedQuery(
        schema=saved_query["schema"],
        query=saved_query["query"],
        uid=saved_query["uid"],
    )


def __create_description_table(schema_data: Dict) -> List[str]:
    """Create a table of the schema description"""
    headers = ["Field", "Type", "Description"]
    data = []
    for field, desc_data in sorted(schema_data["descriptions"].items()):
        s_type = schema_data["projection"].get(field)
        if s_type:
            data.append(
                [
                    field,
                    f"({s_type}):",
                    desc_data["desc"],
                ]
            )
    rv = tabulate(data, headers=headers, tablefmt="plain").splitlines()
    rv = [f"    {line}" for line in rv[2:]]
    return rv


def __create_join_table(schema_data: Dict) -> List[str]:
    """Create a table of the schema joins"""
    headers = ["Field", "New Schema"]
    data = []
    for field, join_data in sorted(schema_data["joins"].items()):
        data.append([f"{field}:", join_data["new_schema"]])
    rv = tabulate(data, headers=headers, tablefmt="plain").splitlines()
    rv = [f"    {line}" for line in rv[2:]]
    return rv
