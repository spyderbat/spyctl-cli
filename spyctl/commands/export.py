"""Handle the export subcommand for spyctl."""

from typing import Optional

import click

import spyctl.config.configs as cfg
import spyctl.filter_resource as filt
import spyctl.resources.suppression_policies as s_pol
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.policies import get_policies

# ----------------------------------------------------------------- #
#                         Export Subcommand                         #
# ----------------------------------------------------------------- #


@click.command("export", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
@click.argument("resource", type=lib.ExportResourcesParam())
@click.argument("name_or_id", required=False)
@click.option(
    "-E",
    "--exact",
    "--exact-match",
    is_flag=True,
    help="Exact match for NAME_OR_ID. This command's default behavior "
    "displays any resource that contains the NAME_OR_ID.",
    required=False,
)
@click.option(
    "--type",
    "meta_type",
    help="The type of policy to return.",
    type=click.Choice([lib.POL_TYPE_TRACE, lib.POL_TYPE_CONT, lib.POL_TYPE_SVC]),
    metavar="",
    required=False,
)
@click.option(
    "-o",
    "--output",
    default=lib.OUTPUT_YAML,
    type=click.Choice(lib.OUTPUT_CHOICES + [lib.OUTPUT_WIDE], case_sensitive=False),
    required=False,
)
def export(
    resource,
    output,
    exact=False,
    meta_type: Optional[type] = None,
    name_or_id=None,
):
    """Export Spyderbat Resources for later use to import."""
    handle_export(resource, name_or_id, exact, meta_type, output)


# ----------------------------------------------------------------- #
#                          Export Handlers                          #
# ----------------------------------------------------------------- #


def handle_export(
    resource: str,
    name_or_id: Optional[str],
    exact: bool,
    rtype: Optional[str],
    output: str = lib.OUTPUT_YAML,
) -> None:
    if name_or_id and not exact:
        name_or_id = name_or_id + "*" if name_or_id[-1] != "*" else name_or_id
        name_or_id = "*" + name_or_id if name_or_id[0] != "*" else name_or_id
    elif resource == lib.POLICIES_RESOURCE:
        handle_export_policies(name_or_id, output, rtype)
    else:
        cli.err_exit(f"The 'export' command is not supported for {resource}")


def handle_export_suppression_policies(name_or_id: Optional[str]) -> None:
    ctx = cfg.get_current_context()
    policies = get_policies(
        *ctx.get_api_data(),
        params={lib.METADATA_TYPE_FIELD: lib.POL_TYPE_TRACE},
    )
    if name_or_id:
        policies = filt.filter_obj(
            policies,
            [
                [lib.METADATA_FIELD, lib.NAME_FIELD],
                [lib.METADATA_FIELD, lib.METADATA_UID_FIELD],
            ],
            name_or_id,
        )
    for policy in policies:
        metadata: dict = {}
        metadata[lib.METADATA_NAME_FIELD] = policy[lib.METADATA_FIELD][
            lib.METADATA_NAME_FIELD
        ]
        metadata[lib.METADATA_TYPE_FIELD] = policy[lib.METADATA_FIELD][
            lib.METADATA_TYPE_FIELD
        ]
        policy[lib.METADATA_FIELD] = metadata
    policies = s_pol.s_policies_output(policies)
    cli.show(policies, lib.OUTPUT_YAML)


def handle_export_policies(
    name_or_id: Optional[str], output: str, rtype: Optional[str]
):
    ctx = cfg.get_current_context()
    params = {
        "name_or_uid_contains": (name_or_id.strip("*") if name_or_id else None),
    }
    if rtype:
        params["type"] = rtype

    policies = get_policies(*ctx.get_api_data(), params=params)
    exported_pols = []
    for policy in policies:
        if policy[lib.METADATA_FIELD][lib.METADATA_TYPE_FIELD] == lib.POL_TYPE_CLUS:
            continue
        old_meta = policy[lib.METADATA_FIELD]
        policy[lib.METADATA_FIELD] = {
            lib.METADATA_NAME_FIELD: old_meta[lib.METADATA_NAME_FIELD][:64],
            lib.METADATA_TYPE_FIELD: old_meta[lib.METADATA_TYPE_FIELD],
        }
        exported_pols.append(policy)

    exported = {lib.API_FIELD: lib.API_VERSION, lib.ITEMS_FIELD: exported_pols}
    cli.show(exported, output)
