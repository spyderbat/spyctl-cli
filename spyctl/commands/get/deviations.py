"""Handles retrieval of deviations."""

import click

import spyctl.api.policies as pol_api
import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.filter_resource as filt
import spyctl.resources as _r
import spyctl.resources.api_filters as _af
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.commands.get import get_lib


@click.command("deviations", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.source_query_options
@_so.container_context_options
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
    filters = {key: value for key, value in filters.items() if value is not None}
    handle_get_deviations(name_or_id, output, st, et, **filters)


def handle_get_deviations(name_or_id, output, st, et, **filters):
    """Output deviations by name or id."""
    ctx = cfg.get_current_context()
    unique = not filters.pop("non_unique", False)  # Default is unique
    raw_data = filters.pop("raw_data", False)
    include_irrelevant = filters.pop("include_irrelevant", False)
    ctx = cfg.get_current_context()
    sources, filters = _af.Deviations.build_sources_and_filters(**filters)
    if _af.POLICIES_CACHE:
        policies = _af.POLICIES_CACHE
    else:
        policies = pol_api.get_policies(*ctx.get_api_data())
    sources_set = set(sources)
    if name_or_id:
        dev_uid = name_or_id if name_or_id.strip("*").startswith("audit:") else None
        if not dev_uid:
            policies = filt.filter_obj(
                policies,
                [
                    [lib.METADATA_FIELD, lib.NAME_FIELD],
                    [lib.METADATA_FIELD, lib.METADATA_UID_FIELD],
                ],
                name_or_id,
            )
            sources = [
                policy[lib.METADATA_FIELD][lib.METADATA_UID_FIELD]
                for policy in policies
            ]
        else:
            policies = [
                policy
                for policy in policies
                if policy[lib.METADATA_FIELD][lib.METADATA_UID_FIELD] in sources_set
            ]
    else:
        dev_uid = None
        policies = [
            policy
            for policy in policies
            if policy[lib.METADATA_FIELD][lib.METADATA_UID_FIELD] in sources_set
        ]
    pipeline = _af.Deviations.generate_pipeline(dev_uid, filters=filters)
    if output in [lib.OUTPUT_DEFAULT, lib.OUTPUT_WIDE]:
        summary = _r.policies.policies_summary_output(
            policies,
            (st, et),
            get_deviations_count=True,
            suppress_msg=True,
            dev_name_or_uid=dev_uid,
            dev_filters=filters,
            include_irrelevant=include_irrelevant,
        )
        cli.show(summary, lib.OUTPUT_RAW)
    else:
        for deviation in _r.deviations.get_deviations_stream(
            ctx,
            sources,
            (st, et),
            pipeline,
            disable_pbar_on_first=not lib.is_redirected(),
            unique=unique,
            raw_data=raw_data,
            include_irrelevant=include_irrelevant,
            policies=policies,
        ):
            cli.show(deviation, output)
