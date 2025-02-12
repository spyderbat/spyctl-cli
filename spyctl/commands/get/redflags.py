"""Handles retrieval of redflags."""

import click

import spyctl.api.source_query_resources as sq_api
import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.resources.api_filters as _af
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.commands.get import get_lib


@click.command("redflags", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.source_query_options
@_so.container_context_options
@click.option(
    "--severity",
    lib.FLAG_SEVERITY,
    help="Only show flags with the given" " severity or higher.",
)
@click.option(
    "--include-exceptions",
    "exceptions",
    is_flag=True,
    help="Include redflags marked as exceptions in output. Off by default.",
)
def get_redflags_cmd(name_or_id, output, st, et, **filters):
    """Get redflags by name or id."""
    exact = filters.pop("exact")
    get_lib.output_time_log(lib.REDFLAGS_RESOURCE.name_plural, st, et)
    name_or_id = get_lib.wildcard_name_or_id(name_or_id, exact)
    filters = {key: value for key, value in filters.items() if value is not None}
    handle_get_redflags(name_or_id, output, st, et, **filters)


def handle_get_redflags(name_or_id, output, st, et, **filters):
    """Output redflags by name or id."""
    ctx = cfg.get_current_context()
    sources, filters = _af.RedFlags.build_sources_and_filters(**filters)
    pipeline = _af.RedFlags.generate_pipeline(name_or_id, filters=filters)
    if output in [lib.OUTPUT_DEFAULT, lib.OUTPUT_WIDE]:
        summary = _r.flags.flags_output_summary(
            ctx, lib.EVENT_REDFLAG_PREFIX, sources, (st, et), pipeline
        )
        cli.show(summary, lib.OUTPUT_RAW)
    else:
        for redflag in sq_api.get_redflags(
            *ctx.get_api_data(),
            sources,
            (st, et),
            pipeline=pipeline,
            disable_pbar_on_first=not lib.is_redirected(),
        ):
            cli.show(redflag, output)
