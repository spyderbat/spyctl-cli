"""Handles retrieval of processes."""

import click

import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl.api.athena_search import search_athena
from spyctl.commands.get import get_lib


@click.command("bash-cmds", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.name_or_id_arg
@_so.output_option
@_so.exact_match_option
@_so.help_option
@_so.time_options
@click.option(
    "--cwd",
    help="Filter by cwd.",
)
@click.option(
    "--euser",
    help="Filter by effective user.",
)
@click.option(
    "--machine-uid",
    help="Filter by machine.",
)
@click.option(
    "--process-uid",
    help="Filter by process.",
)
def get_bash_cmds_cmd(name_or_id, output, st, et, **filters):
    """Get bash commands."""
    exact = filters.pop("exact")
    get_lib.output_time_log(lib.BASH_CMDS_RESOURCE.name_plural, st, et)
    name_or_id = get_lib.wildcard_name_or_id(name_or_id, exact)
    filters = {
        key: value for key, value in filters.items() if value is not None
    }
    handle_get_bash_cmds(name_or_id, output, st, et, **filters)


def handle_get_bash_cmds(name_or_id, output, st, et, **filters):
    """Output bash commands."""
    ctx = cfg.get_current_context()
    query = _r.bash_cmds.bash_cmds_query(name_or_id, **filters)
    bash_cmds = search_athena(
        *ctx.get_api_data(),
        "event_bash_cmd",
        query,
        start_time=st,
        end_time=et,
    )
    get_lib.show_get_data(
        bash_cmds,
        output,
        lambda data: _r.bash_cmds.bash_cmds_summary_output(
            data,
            wide=output == lib.OUTPUT_WIDE,
        ),
    )
