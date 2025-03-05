"""Handles retrieval of deviations."""

import click

import spyctl.api.policies as pol_api
import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.athena_search import search_full_json
from spyctl.commands.get import get_lib


@click.command("deviations", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.athena_query_options
@_so.schema_options("event_deviation")
@click.option(
    f"--{lib.POLICIES_FIELD}",
    "policies",
    help="Policies to get deviations from.",
    type=lib.ListParam(),
    metavar="",
)
@click.option(
    "--non-unique",
    is_flag=True,
    help="By default json or yaml output will be unique. Set"
    " this flag to include all relevant deviations.",
)
@click.option(
    "--raw-data",
    is_flag=True,
    help="Return the raw event_audit:guardian_deviation data.",
)
@click.option(
    "--include-irrelevant",
    is_flag=True,
    help="Return deviations tied to a policy even if they"
    " are no longer relevant. The default behavior is to"
    " exclude deviations that have already been merged into"
    " the policy.",
)
def get_deviations_cmd(name_or_id, output, st, et, **filters):
    """Get deviations by name or id."""
    exact = filters.pop("exact")
    get_lib.output_time_log(lib.DEVIATIONS_RESOURCE.name_plural, st, et)
    name_or_id = get_lib.wildcard_name_or_id(name_or_id, exact)
    filters = {
        key: value for key, value in filters.items() if value is not None
    }
    handle_get_deviations(name_or_id, output, st, et, **filters)


def handle_get_deviations(name_or_id, output, st, et, **filters):
    """Output deviations by name or id."""
    ctx = cfg.get_current_context()
    include_irrelevant = filters.pop("include_irrelevant", False)
    policies = pol_api.get_policies(*ctx.get_api_data())
    if output in [lib.OUTPUT_DEFAULT, lib.OUTPUT_WIDE]:
        summary = _r.policies.policies_summary_output(
            policies,
            (st, et),
            get_deviations_count=True,
            suppress_msg=True,
            dev_name_or_uid=name_or_id,
            dev_filters=filters,
            include_irrelevant=include_irrelevant,
        )
        cli.show(summary, lib.OUTPUT_RAW)
    else:
        query = lib.query_builder("event_deviation", name_or_id, **filters)
        deviations = search_full_json(
            *ctx.get_api_data(),
            "event_deviation",
            query,
            start_time=st,
            end_time=et,
        )
        cli.show(deviations, output)
