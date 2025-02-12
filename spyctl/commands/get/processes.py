"""Handles retrieval of processes."""

import click

import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl.api.athena_search import search_athena
from spyctl.commands.get import get_lib


@click.command("processes", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.name_or_id_arg
@_so.output_option
@_so.exact_match_option
@_so.help_option
@_so.time_options
@click.option(
    "--machine-uid",
    help="Filter by machine.",
)
@click.option(
    "--pid_equals",
    help="Filter by PID.",
)
@click.option(
    "--pid_above",
    help="Filter by PID.",
)
@click.option(
    "--pid_below",
    help="Filter by PID.",
)
@click.option(
    "--ppuid",
    help="Filter by Parent Process UID.",
)
def get_processes_cmd(name_or_id, output, st, et, **filters):
    """Get processes by name or id."""
    exact = filters.pop("exact")
    get_lib.output_time_log(lib.PROCESSES_RESOURCE.name_plural, st, et)
    name_or_id = get_lib.wildcard_name_or_id(name_or_id, exact)
    filters = {key: value for key, value in filters.items() if value is not None}
    handle_get_processes(name_or_id, output, st, et, **filters)


def handle_get_processes(name_or_id, output, st, et, **filters):
    """Output processes by name or id."""
    ctx = cfg.get_current_context()
    query = _r.processes.processes_query(name_or_id, **filters)

    processes = search_athena(
        *ctx.get_api_data(),
        "model_process",
        query,
        start_time=st,
        end_time=et,
        desc="Retrieving Processes",
    )
    get_lib.show_get_data(
        processes,
        output,
        lambda data: _r.processes.processes_stream_output_summary(
            data,
            wide=output == lib.OUTPUT_WIDE,
        ),
    )
