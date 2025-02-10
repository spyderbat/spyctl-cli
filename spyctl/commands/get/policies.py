"""Handles retrieval of policies."""

import click

import spyctl.api.policies as pol_api
import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.commands.get import get_lib


@click.command("policies", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.help_option
@_so.name_or_id_arg
@_so.output_option
@_so.exact_match_option
@_so.time_options
@click.option(
    "-O",
    "--output-to-file",
    help="Should output policies to a file. Unique filename"
    " created from the name in each policy's metadata.",
    is_flag=True,
)
@click.option(
    "--raw-data",
    is_flag=True,
    hidden=True,
)
@click.option(
    "--get-deviations",
    help="In the summary output, show deviations count for the"
    " provided time window",
    is_flag=True,
)
@click.option(
    "--type",
    help="The type of policy to return.",
    type=click.Choice(lib.POL_TYPES),
    metavar="",
)
@click.option(
    "--from-archive",
    is_flag=True,
    help="Retrieve archived ruleset versions.",
)
@click.option(
    "--version",
    type=click.INT,
    help="Retrieve archived rulesets with a specific version.",
    metavar="",
)
def get_policies_cmd(name_or_id, output, st, et, **filters):
    """Get policies by name or id."""
    get_lib.output_time_log(lib.POLICIES_RESOURCE.name_plural, None, None)
    exact = filters.pop("exact")
    name_or_id = get_lib.wildcard_name_or_id(name_or_id, exact)
    handle_get_policies(name_or_id, output, st, et, **filters)


def handle_get_policies(name_or_id, output, st, et, **filters):
    """Output policies by name or id."""
    file_output = filters.pop("output_to_file", False)
    get_deviations_count = filters.pop("get_deviations", False)
    raw_data = filters.pop("raw_data", False)
    from_archive = filters.pop("from_archive", False)
    version = filters.pop("version", None)
    if version:
        from_archive = True
    ctx = cfg.get_current_context()
    params = {
        "name_or_uid_contains": (
            name_or_id.strip("*") if name_or_id else None
        ),
        "from_archive": from_archive,
    }
    if "type" in filters:
        params["type"] = filters.pop("type")
    policies = pol_api.get_policies(
        *ctx.get_api_data(), raw_data=raw_data, params=params
    )
    if version:
        policies = [
            pol
            for pol in policies
            if pol[lib.METADATA_FIELD][lib.VERSION_FIELD] == version
        ]
    if file_output:
        for policy in policies:
            out_fn = lib.find_resource_filename(policy, "policy_output")
            if output != lib.OUTPUT_JSON:
                output = lib.OUTPUT_YAML
            out_fn = lib.unique_fn(out_fn, output)
            cli.show(
                policy, output, dest=lib.OUTPUT_DEST_FILE, output_fn=out_fn
            )
    else:
        if output in [lib.OUTPUT_DEFAULT, lib.OUTPUT_WIDE]:
            summary = _r.policies.policies_summary_output(
                policies, (st, et), get_deviations_count
            )
            cli.show(summary, lib.OUTPUT_RAW)
        else:
            for policy in policies:
                cli.show(policy, output)
