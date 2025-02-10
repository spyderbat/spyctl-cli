"""Handles retrieval of top data."""

import click

import spyctl.api.source_query_resources as sq_api
import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources.api_filters as _af
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.commands.get import get_lib


@click.command("top-data", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.source_query_options
@_so.container_context_options
def get_top_data_cmd(name_or_id, output, st, et, **filters):
    """Get top-data by name or id."""
    exact = filters.pop("exact")
    get_lib.output_time_log(lib.TOP_DATA_RESOURCE.name_plural, st, et)
    name_or_id = get_lib.wildcard_name_or_id(name_or_id, exact)
    filters = {
        key: value for key, value in filters.items() if value is not None
    }
    handle_get_top_data(name_or_id, output, st, et, **filters)


def handle_get_top_data(name_or_id, output, st, et, **filters):
    """Output top-data by name or id."""
    ctx = cfg.get_current_context()
    if not name_or_id and lib.MACHINES_FIELD not in filters:
        cli.err_exit(
            "Provide the machine uid or source of the machine you want top data for.\n"  # noqa
            "'spyctl get sources' will provide a list."
        )
    if lib.MACHINES_FIELD not in filters:
        filters[lib.MACHINES_FIELD] = name_or_id
        name_or_id = None
    sources, filters = _af.SpydertopData.build_sources_and_filters(**filters)
    pipeline = _af.SpydertopData.generate_pipeline(name_or_id, filters=filters)
    if output in [lib.OUTPUT_DEFAULT, lib.OUTPUT_WIDE]:
        cli.try_log(
            "Spydertop data has no summary or wide output.\n"
            "Use the Spyderbat Console or SpyderTop CLI to see the 'htop' style view.\n"  # noqa
            "Use -o yaml or -o json to retrieve the raw data."
        )
    else:
        for top_data in sq_api.get_top_data(
            *ctx.get_api_data(),
            sources,
            (st, et),
            pipeline,
            not lib.is_redirected(),
        ):
            cli.show(top_data, output)
