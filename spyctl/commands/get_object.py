"""Handles the "get-object" command."""

import click

import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.objects import get_objects


@click.command("get-object", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
@click.argument("ids", required=True, type=lib.ListParam())
@click.option(
    "-c",
    "--complete-graph",
    is_flag=True,
    hidden=True,
    help="If set, return the complete graph for the query.",
)
@click.option(
    "-F",
    "--follow-target",
    is_flag=True,
    hidden=True,
    help="If set, follow the target of the query.",
)
@click.option(
    "-o",
    "--output",
    type=click.Choice([lib.OUTPUT_YAML, lib.OUTPUT_JSON, lib.OUTPUT_NDJSON]),
    default=lib.OUTPUT_NDJSON,
    help="Output format.",
)
def get_object(ids, complete_graph, follow_target, output):
    """Hydrate object(s) with the given ID(s)."""
    handle_get_object(ids, complete_graph, follow_target, output)


def handle_get_object(
    ids: bool, complete_graph: bool, follow_target: bool, output: str
):
    """Handle the 'get-object' command."""
    ctx = cfg.get_current_context()
    data = get_objects(
        *ctx.get_api_data(),
        ids,
        complete_graph=complete_graph,
        follow_target=follow_target,
    )
    for obj in data:
        cli.show(obj, output=output)
