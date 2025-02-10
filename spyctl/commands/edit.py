"""Handles the 'edit' subcommand for spyctl."""

# pylint: disable=broad-exception-caught

import json
import tempfile
from io import TextIOWrapper
from typing import IO, Callable, Dict

import click
import yaml

import spyctl.config.configs as cfg
import spyctl.resources as r
import spyctl.schemas_v2 as schemas
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.agent_health import get_agent_health_notification_settings_list
from spyctl.api.custom_flags import get_custom_flags
from spyctl.api.notification_targets import get_notification_targets
from spyctl.api.notification_templates import get_notification_templates
from spyctl.api.policies import get_policies, put_policy_update
from spyctl.api.rulesets import get_rulesets, put_ruleset_update
from spyctl.api.saved_queries import get_saved_queries
from spyctl.commands.apply_cmd.agent_health import (
    handle_apply_agent_health_notification,
)
from spyctl.commands.apply_cmd.apply import (
    handle_apply_custom_flag,
    put_saved_query_from_yaml,
)
from spyctl.commands.apply_cmd.notification_target import (
    handle_apply_notification_target,
)
from spyctl.commands.apply_cmd.notification_template import (
    handle_apply_notification_template,
)

# ----------------------------------------------------------------- #
#                          Edit Subcommand                          #
# ----------------------------------------------------------------- #


@click.command("edit", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
@click.argument("resource", type=lib.EditResourcesParam(), required=False)
@click.argument("name_or_id", required=False)
@click.option(
    "-f",
    "--filename",
    help="Filename to use to edit the resource.",
    metavar="",
    type=click.File(mode="r+"),
)
@click.option(
    "-y",
    "--yes",
    "--assume-yes",
    is_flag=True,
    help='Automatic yes to prompts; assume "yes" as answer to all prompts and'
    " run non-interactively.",
)
def edit(resource, name_or_id, filename, yes=False):
    """Edit resources by resource and name, or by resource and ids"""
    if yes:
        cli.set_yes_option()
    handle_edit(resource, name_or_id, filename)


# ----------------------------------------------------------------- #
#                          Edit Handlers                            #
# ----------------------------------------------------------------- #

EDIT_PROMPT = (
    "# Please edit the object below. Lines beginning with a '#' will be ignored,\n"  # noqa
    "# and an empty file will abort the edit. If an error occurs while saving this file will be\n"  # noqa
    "# reopened with the relevant failures.\n"
    "#\n"
)

KIND_TO_RESOURCE_TYPE: Dict[str, str] = {
    lib.BASELINE_KIND: lib.BASELINES_RESOURCE.name,
    lib.CONFIG_KIND: lib.CONFIG_ALIAS.name,
    lib.FPRINT_GROUP_KIND: lib.FINGERPRINT_GROUP_RESOURCE.name,
    lib.FPRINT_KIND: lib.FINGERPRINTS_RESOURCE.name,
    lib.POL_KIND: lib.POLICIES_RESOURCE.name,
    (
        lib.POL_KIND,
        lib.POL_TYPE_TRACE,
    ): lib.TRACE_SUPPRESSION_POLICY_RESOURCE.name,
    (lib.POL_KIND, lib.POL_TYPE_CLUS): lib.CLUSTER_POLICY_RESOURCE.name,
    lib.SECRET_KIND: lib.SECRETS_ALIAS.name,
    lib.UID_LIST_KIND: lib.UID_LIST_RESOURCE.name,
    lib.DEVIATION_KIND: lib.DEVIATIONS_RESOURCE.name,
    lib.NOTIFICATION_KIND: lib.NOTIFICATION_CONFIGS_RESOURCE.name,
    lib.TEMPLATE_KIND: lib.NOTIFICATION_TEMPLATES_RESOURCE.name,
    lib.TARGET_KIND: lib.NOTIFICATION_TARGETS_RESOURCE.name,
    lib.CUSTOM_FLAG_KIND: lib.CUSTOM_FLAG_RESOURCE.name,
    lib.RULESET_KIND: "ruleset",
    lib.AGENT_HEALTH_NOTIFICATION_KIND: lib.AGENT_HEALTH_NOTIFICATION_RESOURCE.name,
}


def handle_edit(resource=None, name_or_id=None, file_io=None):
    """
    Handles the 'edit' command for a specified resource and name or id.

    Args:
        resource (str): The resource to edit.
        name_or_id (str): The name or id of the resource to edit.
        file_io (IO): The file to edit.

    Returns:
        None
    """
    if file_io is not None:
        handle_edit_file(file_io)
    else:
        if not resource or not name_or_id:
            cli.err_exit("Must specify resource and name or id.")
        if resource in [lib.CLUSTER_RULESET_RESOURCE, lib.RULESETS_RESOURCE]:
            handle_edit_ruleset(name_or_id)
        elif resource == lib.NOTIFICATION_TARGETS_RESOURCE:
            handle_edit_notif_tgt(name_or_id)
        elif resource == lib.CONTAINER_POL_RESOURCE:
            handle_edit_policy(name_or_id, lib.POL_TYPE_CONT)
        elif resource == lib.LINUX_SVC_POL_RESOURCE:
            handle_edit_policy(name_or_id, lib.POL_TYPE_SVC)
        elif resource in [lib.POLICIES_RESOURCE, lib.CLUSTER_POLICY_RESOURCE]:
            handle_edit_policy(name_or_id)
        elif resource == lib.TRACE_SUPPRESSION_POLICY_RESOURCE:
            handle_edit_policy(name_or_id, lib.POL_TYPE_TRACE)
        elif resource == lib.NOTIFICATION_TEMPLATES_RESOURCE:
            handle_edit_notif_tmpl(name_or_id)
        elif resource == lib.CUSTOM_FLAG_RESOURCE:
            handle_edit_custom_flag(name_or_id)
        elif resource == lib.SAVED_QUERY_RESOURCE:
            handle_edit_saved_query(name_or_id)
        elif resource == lib.AGENT_HEALTH_NOTIFICATION_RESOURCE:
            handle_edit_agent_health_notification(name_or_id)
        else:
            cli.err_exit(
                f"The 'edit' command is not supported for '{resource}'"
            )


def handle_edit_file(file: IO):
    """
    Handle editing a file.

    Args:
        file (IO): The file to be edited.

    Raises:
        ValueError: If the file is not a valid resource file.
        ValueError: If editing a resource of the given kind is not supported.
    """
    resource = lib.load_resource_file(file)
    if not isinstance(resource, Dict):
        cli.err_exit("Invalid file for editing.")
    kind = resource.get(lib.KIND_FIELD)
    if kind not in KIND_TO_RESOURCE_TYPE:
        cli.err_exit(f"Editing resource of kind '{kind}' not supported.")
    if kind == lib.POL_KIND:
        m_type = resource[lib.METADATA_FIELD][lib.METADATA_TYPE_FIELD]
        if m_type == lib.POL_TYPE_TRACE:
            kind = (lib.POL_KIND, lib.POL_TYPE_TRACE)
    m_type = resource[lib.METADATA_FIELD].get(lib.METADATA_TYPE_FIELD)
    key = (kind, m_type)
    if key not in schemas.KIND_TO_SCHEMA:
        key = kind
    resource_type = KIND_TO_RESOURCE_TYPE[key]
    edit_resource(
        cli.make_yaml(resource),
        file,
        resource_type,
        schemas.KIND_TO_SCHEMA[key],
        apply_file_edits,
    )


def handle_edit_ruleset(name_or_id, rs_type=None):
    ctx = cfg.get_current_context()
    params = {
        "type": rs_type,
        "name_or_uid_contains": name_or_id,
    }
    rulesets = get_rulesets(*ctx.get_api_data(), params=params)
    if not rulesets:
        desc = f" {rs_type} " if rs_type else " "
        cli.err_exit(f"No{desc}rulesets matching '{name_or_id}'")
    if len(rulesets) > 1:
        cli.err_exit(f"Ruleset '{name_or_id}' is ambiguous, use full UID.")
    ruleset = rulesets[0]
    resource_yaml = cli.make_yaml(ruleset)
    edit_resource(
        resource_yaml,
        ruleset[lib.METADATA_FIELD][lib.METADATA_UID_FIELD],
        "ruleset",
        schemas.KIND_TO_SCHEMA[lib.RULESET_KIND],
        apply_ruleset_edits,
    )


def handle_edit_policy(name_or_id, pol_type=None):
    """
    Handle the editing of a policy based on the given name or ID.

    Args:
        name_or_id (str): The name or ID of the policy to be edited.

    Returns:
        None
    """
    ctx = cfg.get_current_context()
    params = {
        "type": pol_type,
        "name_or_uid_contains": name_or_id,
    }
    policies = get_policies(*ctx.get_api_data(), params=params)
    if len(policies) > 1:
        cli.err_exit(f"Policy '{name_or_id}' is ambiguous, use full UID.")
    if not policies:
        desc = f" {pol_type} " if pol_type else " "
        cli.err_exit(f"No{desc}policies matching '{name_or_id}'.")
    policy = policies[0]
    key = (
        lib.POL_KIND,
        policy.get(lib.METADATA_FIELD).get(lib.METADATA_TYPE_FIELD),
    )
    if key not in schemas.KIND_TO_SCHEMA:
        key = lib.POL_KIND
    resource_yaml = cli.make_yaml(policy)
    edit_resource(
        resource_yaml,
        policy[lib.METADATA_FIELD][lib.METADATA_UID_FIELD],
        lib.POLICIES_RESOURCE.name,
        schemas.KIND_TO_SCHEMA[key],
        apply_policy_edits,
    )


def handle_edit_agent_health_notification(name_or_id):
    """
    Handle the editing of agent health notification settings based on the given name or ID.

    Args:
        name_or_id (str): The name or ID of the agent health notification settings to be edited.

    Returns:
        None
    """
    ctx = cfg.get_current_context()
    params = {
        "name_or_uid_contains": name_or_id,
    }
    agent_health_notification_settings, _ = (
        get_agent_health_notification_settings_list(
            *ctx.get_api_data(), **params
        )
    )
    if len(agent_health_notification_settings) > 1:
        cli.err_exit(
            f"Agent health notification settings '{name_or_id}' is ambiguous, use full UID."
        )
    if not agent_health_notification_settings:
        cli.err_exit(
            f"No agent health notification settings matching '{name_or_id}'."
        )
    agent_health_notification_data = agent_health_notification_settings[0]
    agent_health_notification = r.agent_health.data_to_yaml(
        agent_health_notification_data
    )
    resource_yaml = cli.make_yaml(agent_health_notification)
    edit_resource(
        resource_yaml,
        agent_health_notification[lib.METADATA_FIELD][lib.METADATA_UID_FIELD],
        lib.AGENT_HEALTH_NOTIFICATION_RESOURCE.name,
        schemas.KIND_TO_SCHEMA[lib.AGENT_HEALTH_NOTIFICATION_KIND],
        apply_agent_health_notification_edits,
    )


def handle_edit_custom_flag(name_or_id):
    """
    Handle the editing of a custom flag based on the given name or ID.

    Args:
        name_or_id (str): The name or ID of the custom flag to be edited.

    Returns:
        None
    """
    ctx = cfg.get_current_context()
    params = {
        "name_or_uid_contains": name_or_id,
    }
    custom_flags, _ = get_custom_flags(*ctx.get_api_data(), **params)
    if len(custom_flags) > 1:
        cli.err_exit(f"Custom flag '{name_or_id}' is ambiguous, use full UID.")
    if not custom_flags:
        cli.err_exit(f"No custom flags matching '{name_or_id}'.")
    custom_flag_data = custom_flags[0]
    custom_flag = r.custom_flags.data_to_yaml(custom_flag_data)
    resource_yaml = cli.make_yaml(custom_flag)
    edit_resource(
        resource_yaml,
        custom_flag[lib.METADATA_FIELD][lib.METADATA_UID_FIELD],
        lib.CUSTOM_FLAG_RESOURCE.name,
        schemas.KIND_TO_SCHEMA[lib.CUSTOM_FLAG_KIND],
        apply_custom_flag_edits,
    )


def handle_edit_notif_tgt(name_or_id):
    """
    Handle the editing of a notification target based on the given name or ID.

    Args:
        name_or_id (str): The name or ID of the notification target to be
            edited.

    Returns:
        None
    """
    ctx = cfg.get_current_context()
    params = {
        "name_or_uid_contains": name_or_id,
        "include_target_data": True,
    }
    targets, _ = get_notification_targets(*ctx.get_api_data(), **params)
    if len(targets) > 1:
        cli.err_exit(
            f"Notification target '{name_or_id}' is ambiguous, use full UID."
        )
    if not targets:
        cli.err_exit(f"No notification targets matching '{name_or_id}'.")
    target_data = targets[0]
    target = r.notification_targets.data_to_yaml(target_data)
    resource_yaml = cli.make_yaml(target)
    edit_resource(
        resource_yaml,
        target[lib.METADATA_FIELD][lib.METADATA_UID_FIELD],
        lib.NOTIFICATION_TARGETS_RESOURCE.name,
        schemas.KIND_TO_SCHEMA[lib.TARGET_KIND],
        apply_tgt_edits,
    )


def handle_edit_notif_tmpl(name_or_id):
    """
    Handle the editing of a notification template based on the given name or ID.

    Args:
        name_or_id (str): The name or ID of the notification template to be
            edited.

    Returns:
        None
    """
    ctx = cfg.get_current_context()
    params = {
        "name_or_uid_contains": name_or_id,
    }
    templates, _ = get_notification_templates(*ctx.get_api_data(), **params)
    if len(templates) > 1:
        cli.err_exit(
            f"Notification template '{name_or_id}' is ambiguous, use full UID."
        )
    if not templates:
        cli.err_exit(f"No notification templates matching '{name_or_id}'.")
    template_data = templates[0]
    template = r.notification_templates.data_to_yaml(template_data)
    resource_yaml = cli.make_yaml(template)
    edit_resource(
        resource_yaml,
        template[lib.METADATA_FIELD][lib.METADATA_UID_FIELD],
        lib.NOTIFICATION_TEMPLATES_RESOURCE.name,
        schemas.KIND_TO_SCHEMA[lib.TEMPLATE_KIND],
        apply_tmpl_edits,
    )


def handle_edit_saved_query(name_or_id):
    """
    Handle the editing of a saved query based on the given name or ID.

    Args:
        name_or_id (str): The name or ID of the saved query to be edited.

    Returns:
        None
    """
    ctx = cfg.get_current_context()
    params = {
        "name_or_uid_contains": name_or_id,
    }
    saved_queries, _ = get_saved_queries(*ctx.get_api_data(), **params)
    if len(saved_queries) > 1:
        cli.err_exit(f"Saved query '{name_or_id}' is ambiguous, use full UID.")
    if not saved_queries:
        cli.err_exit(f"No saved queries matching '{name_or_id}'.")
    saved_query_data = saved_queries[0]
    saved_query = r.saved_queries.data_to_yaml(saved_query_data)
    resource_yaml = cli.make_yaml(saved_query)
    edit_resource(
        resource_yaml,
        saved_query[lib.METADATA_FIELD][lib.METADATA_UID_FIELD],
        lib.SAVED_QUERY_RESOURCE.name,
        schemas.KIND_TO_SCHEMA[lib.SAVED_QUERY_KIND],
        apply_saved_query_edits,
    )


def edit_resource(
    resource_yaml: str,
    resource_id: str,
    resource_type,
    validator: Callable,
    apply_func: Callable,
):
    """
    Edit a resource using a YAML file.

    Args:
        resource_yaml (str): The YAML content of the resource.
        resource_id (str): The ID of the resource.
        resource_type: The type of the resource.
        validator (Callable): A function that validates the edited YAML
            content.
        apply_func (Callable): A function that applies the edited YAML content.

    Returns:
        None
    """
    temp_file = None
    while True:
        if not temp_file:
            edit_yaml = click.edit(
                __add_edit_prompt(resource_yaml), extension=".yaml"
            )
        else:
            try:
                with open(temp_file, "r", encoding="UTF-8") as f:
                    tmp_yaml = f.read()
                edit_yaml = click.edit(tmp_yaml, extension=".yaml")
            except Exception as e:
                cli.err_exit(str(e))
        if not edit_yaml or __strip_comments(edit_yaml) == resource_yaml:
            cli.try_log("Edit cancelled, no changes made.")
            exit(0)
        try:
            edit_dict = yaml.load(edit_yaml, lib.UniqueKeyLoader)
            error = None
            validator(**edit_dict)
        except Exception as e:
            error = str(e)
        if error and temp_file:
            edit_yaml = __add_error_comments(
                resource_type,
                edit_yaml,
                error,
                resource_id,
            )
            with open(temp_file, "w", encoding="UTF-8") as f:
                f.write(edit_yaml)
            cli.try_log(f"Edit failed, edits saved to {temp_file}")
            exit(1)
        if error:
            edit_yaml = __add_error_comments(
                resource_type,
                edit_yaml,
                error,
                resource_id,
            )
            temp_file = tempfile.NamedTemporaryFile(
                "w", delete=False, prefix="spyctl-edit-", suffix=".yaml"
            )
            temp_file.write(edit_yaml)
            cli.try_log(f"Edit failed, edits saved to {temp_file.name}")
            temp_file.close()
            temp_file = temp_file.name
            continue
        else:
            apply_func(edit_dict, resource_id)
            break


def apply_tgt_edits(edit_dict: Dict, target_id: str):
    """
    Apply edits to a notification target identified by target_id.

    Args:
        edit_dict (Dict): A dictionary containing the edited target resource.
        target_id (str): The ID of the target to be edited.

    Raises:
        ValueError: If the target with the specified ID is not found.

    """
    edit_dict[lib.METADATA_FIELD][lib.METADATA_UID_FIELD] = target_id
    handle_apply_notification_target(edit_dict, from_edit=True)


def apply_tmpl_edits(edit_dict: Dict, template_id: str):
    """
    Apply edits to a notification template identified by template_id.

    Args:
        edit_dict (Dict): A dictionary containing the edited template resource.
        template_id (str): The ID of the template to be edited.
    """
    edit_dict[lib.METADATA_FIELD][lib.METADATA_UID_FIELD] = template_id
    handle_apply_notification_template(edit_dict, from_edit=True)


def apply_policy_edits(edit_dict: Dict, policy_id: str):
    """
    Apply edits to a policy identified by policy_id.

    Args:
        edit_dict (Dict): A dictionary containing the edited policy resource.
        policy_id (str): The ID of the policy to be edited.
    """
    ctx = cfg.get_current_context()
    pol_type = edit_dict[lib.METADATA_FIELD][lib.METADATA_TYPE_FIELD]
    # Ensure the user didn't manipulate the uid
    edit_dict[lib.METADATA_FIELD][lib.METADATA_UID_FIELD] = policy_id
    put_policy_update(*ctx.get_api_data(), edit_dict)
    cli.try_log(
        f"Successfully edited {__pol_resrc_name(pol_type)} '{policy_id}'"
    )


def apply_ruleset_edits(edit_dict: Dict, ruleset_id: str):
    ctx = cfg.get_current_context()
    edit_dict[lib.METADATA_FIELD][lib.METADATA_UID_FIELD] = ruleset_id
    put_ruleset_update(*ctx.get_api_data(), edit_dict)
    cli.try_log(f"Successfully edited Ruleset '{ruleset_id}'")


def apply_agent_health_notification_edits(
    edit_dict: Dict, agent_health_notification_id: str
):
    """
    Apply edits to an agent health notification settings identified by agent_health_notification_id.

    Args:
        edit_dict (Dict): A dictionary containing the edited agent health
            notification settings resource.
        agent_health_notification_id (str): The ID of the agent health
            notification settings to be edited.

    Returns:
        None
    """
    edit_dict[lib.METADATA_FIELD][
        lib.METADATA_UID_FIELD
    ] = agent_health_notification_id
    handle_apply_agent_health_notification(edit_dict, from_edit=True)


def apply_custom_flag_edits(edit_dict: Dict, custom_flag_id: str):
    """
    Applies the given edits to a custom flag.

    Args:
        edit_dict (Dict): A dictionary containing the edits to be applied.
        custom_flag_id (str): The ID of the custom flag to be edited.

    Returns:
        None
    """
    edit_dict[lib.METADATA_FIELD][lib.METADATA_UID_FIELD] = custom_flag_id
    handle_apply_custom_flag(edit_dict, from_edit=True)


def apply_saved_query_edits(edit_dict: Dict, saved_query_id: str):
    """
    Apply edits to a saved query identified by saved_query_id.

    Args
        edit_dict (Dict): A dictionary containing the edited saved query
            resource.
        saved_query_id (str): The
    """
    edit_dict[lib.METADATA_FIELD][lib.METADATA_UID_FIELD] = saved_query_id
    put_saved_query_from_yaml(saved_query_id, edit_dict)
    cli.try_log(f"Successfully edited Saved Query '{saved_query_id}'")


def apply_file_edits(resource, file: IO):
    """
    Apply edits to a file based on the given resource.

    Args:
        resource: The resource containing the edits.
        file (IO): The file to apply the edits to.

    """
    extension = ".json" if file.name.endswith(".json") else ".yaml"
    try:
        file.close()
        with open(file.name, "w", encoding="UTF-8") as f:
            if extension == ".json":
                f.write(json.dumps(resource, sort_keys=False, indent=2))
            else:
                f.write(cli.make_yaml(resource))
    except Exception as e:
        cli.err_exit(f"Unable to write output to {file.name}", exception=e)
    cli.try_log(f"Successfully edited resource file '{file.name}'")


def __strip_comments(yaml_string: str) -> str:
    lines = []
    for line in yaml_string.split("\n"):
        if line.strip().startswith("#"):
            continue
        lines.append(line)
    return "\n".join(lines)


def __add_edit_prompt(yaml_string: str):
    return EDIT_PROMPT + yaml_string


def __add_error_comments(
    resource: str, yaml_string: str, error: str, name: str = None
):
    if isinstance(name, TextIOWrapper):
        name = f' "{name.name}" '
    else:
        name = f' "{name}" ' if name else ""
    yaml_string = __strip_comments(yaml_string)
    error_prompt = f"# {resource}{name}was not valid:\n"
    error = error.split("\n")
    error = ["# " + line for line in error]
    error = "\n".join(error)
    error_prompt += error + "\n#\n"
    rv = EDIT_PROMPT + error_prompt + yaml_string
    return rv


POL_TYPE_TO_RESOURCE_NAME: Dict[str, str] = {
    lib.POL_TYPE_TRACE: lib.TRACE_SUPPRESSION_POLICY_RESOURCE.name,
    lib.POL_TYPE_SVC: lib.LINUX_SVC_POL_RESOURCE.name,
    lib.POL_TYPE_CONT: lib.CONTAINER_POL_RESOURCE.name,
}


def __pol_resrc_name(policy_type: str) -> str:
    return POL_TYPE_TO_RESOURCE_NAME.get(
        policy_type, lib.POLICIES_RESOURCE.name
    )
