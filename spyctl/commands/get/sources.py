"""Handles retrieval of sources."""

import click

import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.filter_resource as filt
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl.commands.get import get_lib
import spyctl.api.sources as src_api


@click.command("sources", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.help_option
@_so.name_or_id_arg
@_so.output_option
@click.option(
    "--include-expired",
    is_flag=True,
    help="Include expired sources in the output."
    " Expired sources are those that have not produced new data in over 24"
    " hours. The may come back online at any time.",
)
@click.option(
    "--exclude-clustermonitors",
    is_flag=True,
    help="Exclude the cluster monitor source from the output.",
)
def get_sources(name_or_id, output, **kwargs):
    """Get sources by name or id."""
    get_lib.output_time_log(lib.SOURCES_RESOURCE.name_plural, 0, 0)
    handle_get_sources(name_or_id, output, **kwargs)


def handle_get_sources(name_or_id, output, **kwargs):
    """Output sources by name or id."""
    ctx = cfg.get_current_context()
    sources = src_api.get_sources(*ctx.get_api_data(), **kwargs)
    if name_or_id:
        sources = filt.filter_obj(sources, ["name", "uid"], name_or_id)
    get_lib.show_get_data(sources, output, _r.sources.sources_summary_output)
