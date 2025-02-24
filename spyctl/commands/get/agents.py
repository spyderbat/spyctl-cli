"""Handles retrieval of agents."""

import time
from typing import IO, Dict, List

import click

import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.athena_search import search_athena
from spyctl.commands.get import get_lib


@click.command("agents", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.athena_query_options
@_so.schema_options("model_agent")
@_so.schema_options("event_metric")
@click.option(
    "--usage-csv",
    help="Outputs the usage metrics for 1 or more agents to" " a specified csv file.",
    type=click.File(mode="w"),
)
@click.option(
    "--usage-json",
    help="Outputs the usage metrics for 1 or more agents to" " stdout in json format.",
    is_flag=True,
    default=False,
)
@click.option(
    "--raw-metrics-json",
    help="Outputs the raw metrics records for 1 or more agents"
    " to stdout in json format.",
    is_flag=True,
    default=False,
)
@click.option(
    "--health-only",
    help="This flag returns the agents list, but doesn't query"
    " metrics (Faster) in the '-o wide' output. You will still"
    " see the agent's health.",
    default=False,
    is_flag=True,
)
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
    usage_csv_file: IO = filters.pop("usage_csv", None)
    usage_json: bool = filters.pop("usage_json", None)
    raw_metrics_json: bool = filters.pop("raw_metrics_json", False)
    include_latest_metrics = not filters.pop("health_only", False)
    if usage_csv_file:
        agent_st = __st_at_least_2hrs(st)
        query = lib.query_builder("model_agent", name_or_id, **filters)
        agents = search_athena(
            *ctx.get_api_data(),
            "model_agent",
            query,
            start_time=agent_st,
            end_time=et,
            desc="Retrieving Agents",
        )
        # We're only outputting the metrics data to a csv file
        handle_agent_usage_csv(agents, agent_st, et, usage_csv_file)
    elif usage_json:
        agent_st = __st_at_least_2hrs(st)
        query = lib.query_builder("model_agent", name_or_id, **filters)
        agents = search_athena(
            *ctx.get_api_data(),
            "model_agent",
            query,
            start_time=agent_st,
            end_time=et,
            desc="Retrieving Agents",
        )
        handle_agent_usage_json(agents, agent_st, et)
    elif raw_metrics_json:
        agent_st = __st_at_least_2hrs(st)
        query = lib.query_builder("event_metric", name_or_id, **filters)
        agent_metrics = search_athena(
            *ctx.get_api_data(),
            "event_metric",
            query,
            start_time=agent_st,
            end_time=et,
            datatype="agent_status",
        )
        handle_agent_metrics_json(agent_metrics)
    else:
        query = lib.query_builder("model_agent", name_or_id, **filters)
        # Normal path for output
        agents = search_athena(
            *ctx.get_api_data(),
            "model_agent",
            query,
            start_time=st,
            end_time=et,
            desc="Retrieving Agents",
        )
        if output == lib.OUTPUT_DEFAULT:
            summary = _r.agents.agent_summary_output(agents)
            cli.show(summary, lib.OUTPUT_RAW)
        elif output == lib.OUTPUT_WIDE:
            query = lib.query_builder("model_agent", name_or_id, **filters)
            agents = search_athena(
                *ctx.get_api_data(),
                "model_agent",
                query,
                start_time=st,
                end_time=et,
                desc="Retrieving Agents",
            )
            query = lib.query_builder("model_machine", name_or_id, **filters)
            sources = search_athena(
                *ctx.get_api_data(),
                "model_machine",
                query,
                start_time=st,
                end_time=et,
            )
            rv = {}
            for source in sources:
                source_uid = source["id"]  # muid
                rv[source_uid] = {
                    "uid": source["id"],
                    "cloud_region": source.get(
                        "cloud_region", lib.NOT_AVAILABLE
                    ),
                    "cloud_type": source.get(
                        "cloud_type", lib.NOT_AVAILABLE
                    ),
                }
            summary = _r.agents.agents_output_wide(agents, rv, include_latest_metrics)
            cli.show(summary, lib.OUTPUT_RAW)
        else:
            for agent in agents:
                cli.show(agent, output)


def __st_at_least_2hrs(st: float):
    two_hours_secs = 60 * 60 * 2
    now = time.time()
    if now - st < two_hours_secs:
        return now - two_hours_secs
    return st


# ----------------------------------------------------------------- #
#                         Alternative Outputs                       #
# ----------------------------------------------------------------- #


def handle_agent_metrics_json(metrics_records: List[Dict]):
    for metrics_record in metrics_records:
        cli.show(metrics_record, lib.OUTPUT_JSON)


def handle_agent_usage_csv(agents: List[Dict], st, et, metrics_csv_file: IO):
    ctx = cfg.get_current_context()
    cli.try_log("Retrieving metrics records.")
    agent_map = _r.agents.metrics_ref_map(agents)
    metrics_csv_file.write(_r.agents.metrics_header())
    query = lib.query_builder("event_metric")

    for metrics_record in search_athena(
        *ctx.get_api_data(),
        "event_metric",
        query,
        start_time=st,
        end_time=et,
        datatype="agent_status",
    ):
        if metrics_record["schema"].startswith("event_metric_machine"):
            continue
        metrics_csv_file.write(
            _r.agents.usage_line(metrics_record, agent_map.get(metrics_record["ref"]))
        )


def handle_agent_usage_json(agents: List[Dict], st, et):
    ctx = cfg.get_current_context()
    cli.try_log("Retrieving metrics records.")
    agent_map = _r.agents.metrics_ref_map(agents)
    query = lib.query_builder("event_metric")
    for metrics_record in search_athena(
        *ctx.get_api_data(),
        "event_metric",
        query,
        start_time=st,
        end_time=et,
        datatype="agent_status",
    ):
        if metrics_record["schema"].startswith("event_metric_machine"):
            continue
        cli.show(
            _r.agents.usage_dict(metrics_record, agent_map.get(metrics_record["ref"])),
            lib.OUTPUT_JSON,
        )
