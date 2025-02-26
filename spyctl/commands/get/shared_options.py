"""Contains click options shared by multiple get commands."""

import json
import time
from importlib.resources import files

import click

import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib


def context_options(f):
    """Add context options to a click command."""
    f = click.option(
        f"--{cfg.MACHINES_FIELD}",
        help="Only show resources to these nodes."
        " Overrides value current context if it exists.",
        type=lib.ListParam(),
        metavar="",
    )(f)
    f = click.option(
        f"--{cfg.CLUSTER_FIELD}",
        help="Only show resources tied to this cluster."
        " Overrides value current context if it exists.",
        type=lib.ListParam(),
        metavar="",
    )(f)
    f = click.option(
        f"--{cfg.NAMESPACE_FIELD}",
        help="Only show resources tied to this namespace."
        " Overrides value current context if it exists.",
        type=lib.ListParam(),
        metavar="",
    )(f)
    f = click.option(
        "--pod",
        cfg.POD_FIELD,
        help="Only show resources tied to this pod uid."
        " Overrides value current context if it exists.",
        type=lib.ListParam(),
        metavar="",
    )(f)
    return f


def container_context_options(f):
    """Add container context options to a click command."""
    f = click.option(
        "--image",
        cfg.IMG_FIELD,
        help="Only show resources tied to this container image."
        " Overrides value current context if it exists.",
        type=lib.ListParam(),
        metavar="",
    )(f)
    f = click.option(
        "--image-id",
        cfg.IMGID_FIELD,
        help="Only show resources tied to containers running with this"
        " image id. Overrides value current context if it exists.",
        type=lib.ListParam(),
        metavar="",
    )(f)
    f = click.option(
        "--container-name",
        cfg.CONTAINER_NAME_FIELD,
        help="Only show resources tied to containers running with this"
        " container name. Overrides value current context if it exists.",
        type=lib.ListParam(),
        metavar="",
    )(f)
    f = click.option(
        "--container-id",
        cfg.CONT_ID_FIELD,
        help="Only show resources tied to containers running with this"
        " container id. Overrides value current context if it exists.",
        type=lib.ListParam(),
        metavar="",
    )(f)
    return f


def l_svc_context_options(f):
    """Add Linux service context options to a click command."""
    f = cgroup_option(f)
    return f


def time_options(f):
    """Add time options to a click command."""
    f = click.option(
        "-t",
        "--start-time",
        "st",
        help="Start time of the query. Default is 24 hours ago.",
        default="24h",
        type=lib.time_inp,
    )(f)
    f = click.option(
        "-e",
        "--end-time",
        "et",
        help="End time of the query. Default is now.",
        default=time.time(),
        type=lib.time_inp,
    )(f)
    return f


def source_query_options(f):
    """Add source query options to a click command."""
    time_options(f)
    context_options(f)
    f = exact_match_option(f)
    f = help_option(f)
    f = output_option(f)
    f = name_or_id_arg(f)
    return f


def athena_query_options(f):
    """Add athena query options to a click command."""
    f = time_options(f)
    f = help_option(f)
    f = output_option(f)
    f = name_or_id_arg(f)
    f = exact_match_option(f)
    f = uid_option(f)
    return f


SKIP_FIELDS = ["time", "valid_from", "valid_to"]


def schema_options(schema):
    """Build command line options dynamically based on the schema."""

    def _add_options(f):
        file = (
            files("spyctl.commands.get").joinpath("resource_schemas.json").read_text()
        )
        schemas = json.loads(file)
        schema_data = schemas[schema]
        title = schema_data["title"]
        for field, type_str in sorted(
            schema_data["projection"].items(),
            key=lambda x: x[0],
            reverse=True,
        ):
            if field in SKIP_FIELDS:
                continue
            schema_opts = lib.TYPE_STR_TO_CLICK_TYPE[type_str]
            field_title = schema_data["descriptions"].get(field, {}).get("title", field)
            if schema_opts.click_type == click.BOOL:
                option_name = f"is-{field.removeprefix('is-')}".replace("_", "-")
                lib.BUILT_QUERY_OPTIONS.setdefault(schema, {})[
                    option_name.replace("-", "_").replace(".", "_")
                ] = lib.SchemaOption(
                    click_type=schema_opts.click_type,
                    option_variant=lib.EQUALS_VARIANT,
                    query_field=field,
                )
                x = click.option(
                    f"--{option_name}",
                    help=f"Only show {title} resources where field"
                    f" '{field_title}' matches the provided boolean value.",
                    type=schema_opts.click_type,
                    metavar="",
                    multiple=True,
                )
                f = x(f)
            else:
                for option_variant in schema_opts.option_variants:
                    option_name = f"{field}-{option_variant}".replace("_", "-").replace(
                        ".", "_"
                    )
                    lib.BUILT_QUERY_OPTIONS.setdefault(schema, {})[
                        option_name.replace("-", "_")
                    ] = lib.SchemaOption(
                        click_type=schema_opts.click_type,
                        option_variant=option_variant,
                        query_field=field,
                    )
                    x = click.option(
                        f"--{option_name}",
                        help=f"Only show {title} resources where field"
                        f" '{field_title}' '{option_variant}' provided.",
                        type=schema_opts.click_type,
                        metavar="",
                        multiple=True,
                    )
                    f = x(f)
        return f

    return _add_options


help_option = click.help_option("-h", "--help", hidden=True)

uid_option = click.option(
    "--uid",
    help="Only show resources with this uid.",
    type=lib.ListParam(),
    metavar="",
)

exact_match_option = click.option(
    "-E",
    "--exact",
    "--exact-match",
    is_flag=True,
    help="Exact match for NAME_OR_ID. This command's default behavior"
    " displays any resource that contains the NAME_OR_ID.",
)

cgroup_option = click.option(
    "--cgroup",
    cfg.CGROUP_FIELD,
    help="Only show resources tied to machines running Linux services with"
    " this cgroup. Overrides value current context if it exists.",
    type=lib.ListParam(),
    metavar="",
)

output_option = click.option(
    "-o",
    "--output",
    default=lib.OUTPUT_DEFAULT,
    type=click.Choice(lib.OUTPUT_CHOICES + [lib.OUTPUT_WIDE], case_sensitive=False),
)

page_option = click.option(
    "--page",
    help="Page number of resources to display.",
    type=click.IntRange(1, clamp=True),
    default=1,
    metavar="",
)

page_size_option = click.option(
    "--page-size",
    help="Number of resources to display per page.",
    type=click.IntRange(-1),
    metavar="",
)

is_enabled_option = click.option(
    "--is-enabled",
    help="Only show resources that are enabled.",
    is_flag=True,
)

is_not_enabled_option = click.option(
    "--is-not-enabled",
    help="Only show resources that are not enabled.",
    is_flag=True,
)

action_taken_option = click.option(
    "--action-taken-equals",
    help="Only show historical 'audit' resources generated by a specific user"
    " action, such as 'insert' or 'delete'",
    type=click.Choice(["insert", "delete", "update", "enable", "disable"]),
    metavar="",
)

latest_version_option = click.option(
    "--latest-version",
    help="Pulling from the historical 'audit' tables, only retrieve the latest"
    " version of the resources by uid.",
    is_flag=True,
)

reversed_option = click.option(
    "--reversed",
    help="Reverse the order of the results.",
    is_flag=True,
)

tags_contain_option = click.option(
    "--tags-contain",
    help="Only show resources that contain these tags.",
    type=lib.ListParam(),
    metavar="",
)

raw_data_option = click.option(
    "--raw-data",
    is_flag=True,
)

# Arguments

name_or_id_arg = click.argument("name_or_id", required=False)
