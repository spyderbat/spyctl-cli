"""Handles retrieval of linux services."""

import click

import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.commands.get import get_lib


@click.command("linux-services", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.help_option
@_so.name_or_id_arg
@_so.output_option
@_so.exact_match_option
@_so.time_options
@click.option(
    "--hostname",
    help="The hostname of the machine running the service.",
    metavar="",
)
def get_linux_svc(name_or_id, output, st, et, **filters):
    """Get linux services by name or id."""
    get_lib.output_time_log(lib.LINUX_SVC_RESOURCE.name_plural, st, et)
    filters = {
        key: value for key, value in filters.items() if value is not None
    }
    exact = filters.pop("exact")
    name_or_id = get_lib.wildcard_name_or_id(name_or_id, exact)
    handle_get_linux_svc(name_or_id, output, st, et, **filters)


def handle_get_linux_svc(name_or_id, output, st, et, **filters):
    """Get linux services by name or id."""
    ctx = cfg.get_current_context()
    if output in [lib.OUTPUT_DEFAULT, lib.OUTPUT_WIDE]:
        summary = _r.linux_services.linux_svc_summary_output(
            ctx, name_or_id, (st, et), **filters
        )
        cli.show(summary, lib.OUTPUT_RAW)
    else:
        for linux_svc in _r.linux_services.get_linux_services(
            ctx, name_or_id, (st, et), **filters
        ):
            cli.show(linux_svc, output)
