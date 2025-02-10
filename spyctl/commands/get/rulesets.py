"""Handles retrieval of rulesets."""

import click

import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.rulesets import get_rulesets
from spyctl.commands.get import get_lib


@click.command("rulesets", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.help_option
@_so.name_or_id_arg
@_so.output_option
@_so.exact_match_option
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
@click.option(
    "--type",
    type=click.Choice(lib.RULESET_TYPES),
    help="The type of ruleset to return.",
    metavar="",
)
def get_rulesets_cmd(name_or_id, output, **filters):
    """Get rulesets by name or id."""
    get_lib.output_time_log(lib.RULESETS_RESOURCE.name_plural, None, None)
    exact = filters.pop("exact")
    name_or_id = get_lib.wildcard_name_or_id(name_or_id, exact)
    handle_get_rulesets(name_or_id, output, **filters)


def handle_get_rulesets(name_or_id, output, **filters):
    """Output rulesets by name or id."""
    ctx = cfg.get_current_context()
    from_archive = filters.pop("from_archive", False)
    version = filters.pop("version", None)
    if version:
        from_archive = True
    params = {
        "from_archive": from_archive,
    }
    if "type" in filters:
        params["type"] = filters.pop("type")
    if name_or_id:
        params["name_or_uid_contains"] = name_or_id.strip("*")
    rulesets = get_rulesets(*ctx.get_api_data(), params)
    if version:
        rulesets = [
            rs
            for rs in rulesets
            if rs[lib.METADATA_FIELD][lib.VERSION_FIELD] == version
        ]
    if output in [lib.OUTPUT_DEFAULT, lib.OUTPUT_WIDE]:
        summary = _r.rulesets.rulesets_summary_output(rulesets)
        cli.show(summary, lib.OUTPUT_RAW)
    else:
        for ruleset in rulesets:
            cli.show(ruleset, output)
