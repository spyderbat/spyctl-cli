"""Handles retrieval of connections."""

import click

import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl.api.athena_search import search_athena
from spyctl.commands.get import get_lib


@click.command("connections", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.name_or_id_arg
@_so.output_option
@_so.exact_match_option
@_so.help_option
@_so.time_options
@click.option(
    "--ignore-ips",
    "ignore_ips",
    is_flag=True,
    help="Ignores differing ips in the table output." " Off by default.",
)
@click.option(
    "--local-port-above",
    help="The port number on the local side of the connection.",
    type=click.INT,
)
@click.option(
    "--local-port",
    lib.LOCAL_PORT,
    help="The port number on the local side of the connection.",
    type=click.INT,
)
@click.option(
    "--local-port-below",
    help="The port number on the local side of the connection.",
    type=click.INT,
)
@click.option(
    "--remote-port",
    help="The port number on the remote side of the connection.",
    type=click.INT,
)
@click.option(
    "--remote-port-above",
    help="The port number on the remote side of the connection.",
    type=click.INT,
)
@click.option(
    "--remote-port-below",
    help="The port number on the remote side of the connection.",
    type=click.INT,
)
def get_connections_cmd(name_or_id, output, st, et, **filters):
    """Get connections by name or id."""
    exact = filters.pop("exact")
    get_lib.output_time_log(lib.CONNECTIONS_RESOURCE.name_plural, st, et)
    name_or_id = get_lib.wildcard_name_or_id(name_or_id, exact)
    filters = {key: value for key, value in filters.items() if value is not None}
    handle_get_connections(name_or_id, output, st, et, **filters)


def handle_get_connections(name_or_id, output, st, et, **filters):
    """Output connections by name or id."""
    ctx = cfg.get_current_context()
    query = _r.connections.connection_query(name_or_id, **filters)

    connections = search_athena(
        *ctx.get_api_data(),
        "model_connection",
        query,
        start_time=st,
        end_time=et,
        desc="Retrieving Connections",
    )
    get_lib.show_get_data(
        connections,
        output,
        lambda data: _r.connections.connection_stream_output_summary(
            data, wide=output == lib.OUTPUT_WIDE, ignore_ips=False
        ),
    )
