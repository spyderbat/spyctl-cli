"""Handles retrieval of fingerprints."""

import click

import spyctl.api.source_query_resources as sq_api
import spyctl.commands.get.shared_options as _so
import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.resources.api_filters as _af
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.commands.get import get_lib


@click.command("fingerprints", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@_so.source_query_options
@_so.container_context_options
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
    get_lib.output_time_log(lib.FINGERPRINTS_RESOURCE.name_plural, st, et)
    name_or_id = get_lib.wildcard_name_or_id(name_or_id, exact)
    filters = {key: value for key, value in filters.items() if value is not None}
    handle_get_fingerprints(name_or_id, output, st, et, **filters)


def handle_get_fingerprints(name_or_id, output, st, et, **filters):
    """Output fingerprints by name or id."""
    ctx = cfg.get_current_context()
    # Pop any extra options
    raw = filters.pop("raw_data", False)
    group_by = filters.pop("group_by", [])
    sort_by = filters.pop("sort_by", [])
    fprint_type = filters.pop(lib.TYPE_FIELD)
    sources, filters = _af.Fingerprints.build_sources_and_filters(
        use_property_fields=True, **filters
    )
    # Hacky -- need to fix this in the API code
    if "image" in filters:
        value = filters.pop("image")
        filters["image_name"] = value
    name_or_id_expr = None
    if name_or_id:
        name_or_id_expr = _af.Fingerprints.generate_name_or_uid_expr(name_or_id)
    # Output in desired format
    if output == lib.OUTPUT_DEFAULT:
        summary = _r.fingerprints.fprint_output_summary(
            ctx,
            fprint_type,
            sources,
            filters,
            st,
            et,
            name_or_id_expr,
            group_by=group_by,
            sort_by=sort_by,
        )
        cli.show(summary, lib.OUTPUT_RAW)
    elif output == lib.OUTPUT_WIDE:
        summary = _r.fingerprints.fprint_output_summary(
            ctx,
            fprint_type,
            sources,
            filters,
            st,
            et,
            name_or_id_expr,
            group_by=group_by,
            sort_by=sort_by,
            wide=True,
        )
        cli.show(summary, lib.OUTPUT_RAW)
    else:
        if raw:
            fprints = sq_api.get_guardian_fingerprints(
                *ctx.get_api_data(),
                sources,
                (st, et),
                fprint_type,
                unique=True,
                limit_mem=True,
                expr=name_or_id_expr,
                **filters,
            )
            for fprint in fprints:
                cli.show(fprint, output)
        else:
            fprints = list(
                sq_api.get_guardian_fingerprints(
                    *ctx.get_api_data(),
                    sources,
                    (st, et),
                    fprint_type,
                    unique=True,
                    limit_mem=True,
                    expr=name_or_id_expr,
                    **filters,
                )
            )
            fprint_groups = _r.fingerprints.make_fingerprint_groups(fprints)
            tmp_grps = []
            for grps in fprint_groups:
                tmp_grps.extend(grps)
            fprint_groups = _r.fingerprints.fprint_groups_output(tmp_grps)
            cli.show(fprint_groups, output)
