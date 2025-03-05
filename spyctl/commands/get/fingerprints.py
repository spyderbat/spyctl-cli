"""Handles retrieval of fingerprints."""

import click

import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.athena_search import search_full_json
from spyctl.commands.get import get_lib


@click.command("fingerprints", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.athena_query_options
@_so.schema_options("model_fingerprint")
@click.option(
    "-T",
    "--type",
    type=click.Choice(
        [lib.POL_TYPE_CONT, lib.POL_TYPE_SVC],
        case_sensitive=False,
    ),
    required=True,
    help="The type of fingerprint to return.",
)
@click.option(
    "--raw-data",
    is_flag=True,
    help="When outputting to yaml or json, this outputs the"
    " raw fingerprint data, instead of the fingerprint groups",
)
@click.option(
    "--group-by",
    type=lib.ListParam(),
    metavar="",
    help="Group by fields in the fingerprint, comma delimited. Such as"  # noqa: E501
    " cluster_name,namespace. At a basic level"
    " fingerprints are always grouped by image + image_id."
    " This option allows you to group by additional fields.",
)
@click.option(
    "--sort-by",
    metavar="",
    type=lib.ListParam(),
    help="Group by fields in the fingerprint, comma delimited. Such as"  # noqa: E501
    " cluster_name,namespace. At a basic level"
    " fingerprints are always grouped by image + image_id."
    " This option allows you to group by additional fields.",
)
def get_fingerprints_cmd(name_or_id, output, st, et, **filters):
    """Get fingerprints by name or id."""
    exact = filters.pop("exact")
    fprint_type = filters.pop("type") or filters.pop("T")
    if fprint_type == "container":
        filters["metadata_type_equals"] = ("container",)
    else:
        filters["metadata_type_equals"] = ("linux-service",)

    get_lib.output_time_log(lib.FINGERPRINTS_RESOURCE.name_plural, st, et)
    name_or_id = get_lib.wildcard_name_or_id(name_or_id, exact)
    filters = {key: value for key, value in filters.items() if value is not None}

    handle_get_fingerprints(name_or_id, output, st, et, fprint_type, **filters)


def handle_get_fingerprints(name_or_id, output, st, et, fprint_type, **filters):
    """Output fingerprints by name or id."""
    ctx = cfg.get_current_context()
    # Pop any extra options
    raw = filters.pop("raw_data", False)
    group_by = filters.pop("group_by", [])
    sort_by = filters.pop("sort_by", [])
    query = lib.query_builder("model_fingerprint", name_or_id, **filters)
    # Output in desired format
    if output == lib.OUTPUT_DEFAULT:
        fingerprints = search_full_json(
            *ctx.get_api_data(),
            "model_fingerprint",
            query,
            start_time=st,
            end_time=et,
            desc="Retrieving Fingerprints",
        )
        summary = _r.fingerprints.fprint_output_summary(
            fprint_type=fprint_type,
            fingerprints=fingerprints,
            group_by=group_by,
            sort_by=sort_by,
            wide=False,
        )
        cli.show(summary, lib.OUTPUT_RAW)
    elif output == lib.OUTPUT_WIDE:
        fingerprints = search_athena(
            *ctx.get_api_data(),
            "model_fingerprint",
            query,
            start_time=st,
            end_time=et,
            desc="Retrieving Fingerprints",
        )
        summary = _r.fingerprints.fprint_output_summary(
            fprint_type=fprint_type,
            fingerprints=fingerprints,
            group_by=group_by,
            sort_by=sort_by,
            wide=True,
        )
        cli.show(summary, lib.OUTPUT_RAW)
    else:
        if raw:
            fprints = search_athena(
                *ctx.get_api_data(),
                "model_fingerprint",
                query,
                start_time=st,
                end_time=et,
                desc="Retrieving Fingerprints",
            )
            for fprint in fprints:
                cli.show(fprint, output)
        else:
            fprints = search_athena(
                *ctx.get_api_data(),
                "model_fingerprint",
                query,
                start_time=st,
                end_time=et,
                desc="Retrieving Fingerprints",
            )
            fprint_groups = _r.fingerprints.make_fingerprint_groups(fprints)
            tmp_grps = []
            for grps in fprint_groups:
                tmp_grps.extend(grps)
            fprint_groups = _r.fingerprints.fprint_groups_output(tmp_grps)
            cli.show(fprint_groups, output)
