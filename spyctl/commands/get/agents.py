"""Handles retrieval of agents."""

import click

import spyctl.api.agents as ag_api
import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.athena_search import search_athena
from spyctl.commands.get import get_lib
from spyctl.filter_resource import filter_obj


@click.command("agents", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.athena_query_options
@_so.schema_options("model_agent")
def get_agents(name_or_id, output, st, et, **filters):
    """Get agents by name or id."""
    exact = filters.pop("exact")
    get_lib.output_time_log(lib.AGENT_RESOURCE.name_plural, st, et)
    name_or_id = get_lib.wildcard_name_or_id(name_or_id, exact)
    filters = {key: value for key, value in filters.items() if value is not None}
    handle_get_agents(name_or_id, output, st, et, **filters)


def handle_get_agents(name_or_id, output, st, et, **filters):
    """Output agents by name or id."""
    ctx = cfg.get_current_context()
    query = lib.query_builder("model_agent", None, **filters)
    # Normal path for output
    agents = search_athena(
        *ctx.get_api_data(),
        "model_agent",
        query,
        start_time=st,
        end_time=et,
        desc="Retrieving Agents",
    )
    agents, sources = ag_api.get_sources_data_for_agents(*ctx.get_api_data(), agents)
    if name_or_id:
        agents = filter_obj(agents, ["id", "name", "hostname", "muid"], name_or_id)
    if output == lib.OUTPUT_DEFAULT:
        summary = _r.agents.agent_summary_output(agents, sources)
        cli.show(summary, lib.OUTPUT_RAW)
    elif output == lib.OUTPUT_WIDE:
        summary = _r.agents.agents_output_wide(agents, sources)
        cli.show(summary, lib.OUTPUT_RAW)
    else:
        for agent in agents:
            cli.show(agent, output)
