"""Handles retrieval of clusters."""

import click

import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.filter_resource as filt
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl.commands.get import get_lib
import spyctl.api.clusters as cl_api


@click.command("clusters", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.help_option
@_so.name_or_id_arg
@_so.output_option
@_so.exact_match_option
def get_clusters(name_or_id, output, exact):
    """Get clusters by name or id."""
    get_lib.output_time_log(lib.CLUSTERS_RESOURCE.name_plural, None, None)
    name_or_id = get_lib.wildcard_name_or_id(name_or_id, exact)
    handle_get_clusters(name_or_id, output)


def handle_get_clusters(name_or_id, output):
    """Output clusters by name or id."""
    ctx = cfg.get_current_context()
    clusters = cl_api.get_clusters(*ctx.get_api_data())
    if name_or_id:
        clusters = filt.filter_obj(clusters, ["name", "uid"], name_or_id)
    get_lib.show_get_data(
        clusters, output, _r.clusters.clusters_summary_output
    )
