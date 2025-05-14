"""Handles the apply subcommand for the spyctl."""

import json
import sys
import time
from typing import Dict, Optional

import click

import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.custom_flags import (
    get_custom_flag,
    get_custom_flags,
    post_new_custom_flag,
    put_custom_flag_update,
    put_disable_custom_flag,
    put_enable_custom_flag,
)
from spyctl.api.policies import (
    get_policies,
    post_new_policy,
    put_policy_update,
)
from spyctl.api.rulesets import post_new_ruleset, put_ruleset_update
from spyctl.api.saved_queries import (
    get_saved_queries,
    get_saved_query,
    get_saved_query_dependents,
    post_new_saved_query,
    put_saved_query_update,
)
from spyctl.commands.apply_cmd.agent_health import (
    handle_apply_agent_health_notification,
)
from spyctl.commands.apply_cmd.notification_target import (
    handle_apply_notification_target,
)
from spyctl.commands.apply_cmd.notification_template import (
    handle_apply_notification_template,
)

# import spyctl.commands.merge as m

# ----------------------------------------------------------------- #
#                         Apply Subcommand                          #
# ----------------------------------------------------------------- #


@click.command("apply", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True, is_eager=True)
@click.option(
    "-f",
    "--filename",
    # help="Filename containing Spyderbat resource.",
    metavar="",
    type=click.File(),
    required=True,
)
def apply(filename):
    """Apply a configuration to a resource by file name."""
    handle_apply(filename)


# ----------------------------------------------------------------- #
#                          Apply Handlers                           #
# ----------------------------------------------------------------- #

APPLY_PRIORITY = {
    lib.RULESET_KIND: 100,
    lib.POL_KIND: 50,
}


def handle_apply(filename):
    """
    Apply new resources or update existing resources.

    Args:
        filename (str): The path to the resource file.

    Returns:
        None
    """
    resrc_data = lib.load_resource_file(filename)
    if lib.ITEMS_FIELD in resrc_data:
        for resrc in resrc_data[lib.ITEMS_FIELD]:
            # Sort resource items by priority
            resrc_data[lib.ITEMS_FIELD].sort(key=__apply_priority, reverse=True)
            handle_apply_data(resrc)
    else:
        handle_apply_data(resrc_data)


def handle_apply_data(resrc_data: Dict):
    kind = resrc_data.get(lib.KIND_FIELD)
    if kind == lib.POL_KIND:
        handle_apply_policy(resrc_data)
    elif kind == lib.TARGET_KIND:
        handle_apply_notification_target(resrc_data)
    elif kind == lib.TEMPLATE_KIND:
        handle_apply_notification_template(resrc_data)
    elif kind == lib.RULESET_KIND:
        handle_apply_ruleset(resrc_data)
    elif kind == lib.SAVED_QUERY_KIND:
        handle_apply_saved_query(resrc_data)
    elif kind == lib.CUSTOM_FLAG_KIND:
        handle_apply_custom_flag(resrc_data)
    elif kind == lib.AGENT_HEALTH_NOTIFICATION_KIND:
        handle_apply_agent_health_notification(resrc_data)
    else:
        cli.err_exit(f"The 'apply' command is not supported for {kind}")


def handle_apply_policy(policy: Dict):
    """
    Apply a policy to the current context.

    Args:
        policy (Dict): The policy to be applied.

    Returns:
        None
    """
    ctx = cfg.get_current_context()
    pol_type = policy[lib.METADATA_FIELD][lib.METADATA_TYPE_FIELD]
    if pol_type == lib.POL_TYPE_TRACE:
        policy = __check_duplicate_sel_hashes(policy)
        if not policy:
            return
    sub_type = _r.policies.get_policy_subtype(pol_type)
    uid = policy[lib.METADATA_FIELD].get(lib.METADATA_UID_FIELD)
    if uid:
        resp = put_policy_update(*ctx.get_api_data(), policy)
        if resp.status_code == 200:
            cli.try_log(f"Successfully updated policy {uid}")
    else:
        resp = post_new_policy(*ctx.get_api_data(), policy)
        if resp and resp.text:
            uid = json.loads(resp.text).get("uid", "")
            cli.try_log(
                f"Successfully applied new {pol_type} {sub_type} policy with uid: {uid}"
            )


def __check_duplicate_sel_hashes(policy: Dict):
    sel_hash = _r.suppression_policies.get_selector_hash(policy)
    ctx = cfg.get_current_context()
    matching_policies = get_policies(
        *ctx.get_api_data(),
        params={
            "selector_hash_equals": sel_hash,
            "type": lib.POL_TYPE_TRACE,
        },
    )
    if not matching_policies:
        return policy
    matching_pol = matching_policies[0]
    if cli.query_yes_no(
        "A policy matching this scope already exists. Would you like to merge"
        " this policy into the existing one?"
    ):
        pol, should_update = _r.suppression_policies.merge_allowed_flags(
            matching_pol, policy
        )
        if should_update:
            return pol
        cli.try_log(
            "No changes detected in the policy. Skipping update.",
            is_warning=True,
        )
    return None


def handle_apply_ruleset(ruleset: Dict):
    """
    Apply a ruleset to the current context.

    Args:
        ruleset (Dict): The ruleset to be applied.

    Returns:
        None
    """
    ctx = cfg.get_current_context()
    rs_type = ruleset[lib.METADATA_FIELD][lib.METADATA_TYPE_FIELD]
    uid = ruleset[lib.METADATA_FIELD].get(lib.METADATA_UID_FIELD)
    if uid:
        resp = put_ruleset_update(*ctx.get_api_data(), ruleset)
        if resp.status_code == 200:
            cli.try_log(f"Successfully updated ruleset {uid}")
    else:
        resp = post_new_ruleset(*ctx.get_api_data(), ruleset)
        if resp and resp.json():
            uid = resp.json().get("uid", "")
            cli.try_log(f"Successfully applied new {rs_type} ruleset with uid: {uid}")


def handle_apply_saved_query(saved_query: Dict):
    """
    Apply a saved query to the current context.

    Args:
        saved_query (Dict): The saved query to be applied.

    Returns:
        None
    """
    ctx = cfg.get_current_context()
    spec = saved_query[lib.SPEC_FIELD]
    schema = spec.get(lib.QUERY_SCHEMA_FIELD)
    query = spec.get(lib.QUERY_FIELD)
    uid = saved_query[lib.METADATA_FIELD].get(lib.METADATA_UID_FIELD)
    if not uid:
        # Check if a saved query with the same schema and query already exists
        matching_queries, _total_pages = get_saved_queries(
            *ctx.get_api_data(),
            **{
                "schema_equals": schema,
                "query_equals": query,
            },
        )
        if matching_queries and not cli.query_yes_no(
            "A Saved Query with this Schema and Query already exists."
            " Do you still want to create this saved query?",
            default="no",
        ):
            cli.try_log("Operation cancelled.")
            sys.exit(0)
        uid = post_saved_query_from_yaml(saved_query)
        cli.try_log(f"Successfully applied new saved query with uid: {uid}")
    else:
        put_saved_query_from_yaml(uid, saved_query)
        cli.try_log(f"Successfully updated saved query with uid: {uid}")
    return uid


def post_saved_query_from_yaml(saved_query: Dict) -> str:
    """
    Post a saved query to the current context.

    Args:
        saved_query (Dict): The saved query to be posted.

    Returns:
        None
    """
    ctx = cfg.get_current_context()
    metadata = saved_query[lib.METADATA_FIELD]
    spec: dict = saved_query[lib.SPEC_FIELD]
    req_body = {
        "name": metadata[lib.METADATA_NAME_FIELD],
        "schema": spec[lib.QUERY_SCHEMA_FIELD],
        "query": spec[lib.QUERY_FIELD],
        "additional_settings": spec.get(lib.ADDITIONAL_SETTINGS_FIELD),
    }
    description = spec.get(lib.QUERY_DESCRIPTION_FIELD)
    if description:
        req_body["description"] = description
    uid = post_new_saved_query(*ctx.get_api_data(), **req_body)
    return uid


def put_saved_query_from_yaml(uid: str, saved_query: Dict) -> str:
    """
    Put a saved query to the current context.

    Args:
        saved_query (Dict): The saved query to be put.

    Returns:
        None
    """
    ctx = cfg.get_current_context()
    metadata = saved_query[lib.METADATA_FIELD]
    spec = saved_query[lib.SPEC_FIELD]
    req_body = {
        "name": metadata[lib.METADATA_NAME_FIELD],
        "notification_settings": saved_query[lib.SPEC_FIELD].get(
            lib.NOTIFICATION_SETTINGS_FIELD
        ),
        "additional_settings": spec.get(lib.ADDITIONAL_SETTINGS_FIELD),
    }
    description = spec.get(lib.QUERY_DESCRIPTION_FIELD)
    if description:
        req_body["description"] = description
    query = spec.get(lib.QUERY_FIELD)
    if query:
        req_body["query"] = query
    deps = get_saved_query_dependents(*ctx.get_api_data(), uid)
    if deps:
        if not cli.query_yes_no(
            "Saved query has dependents. Updating this query will affect the"
            " following resources:\n"
            f"{json.dumps(deps, indent=2)}\n"
            "Do you want to continue?"
        ):
            cli.try_log("Operation cancelled.")
            sys.exit(0)
    put_saved_query_update(*ctx.get_api_data(), uid, **req_body)
    return uid


def handle_apply_custom_flag(
    custom_flag: Dict, sq_name: Optional[str] = None, from_edit: bool = False
) -> str:
    """
    Handles the application of a custom flag.

    Args:
        custom_flag (Dict): The custom flag to be applied.
        sq_name (Optional[str]): The name of the saved query
            if a new one needs to be created.

    Returns:
        str: The UID of the applied custom flag.
    """
    ctx = cfg.get_current_context()
    uid = custom_flag[lib.METADATA_FIELD].get(lib.METADATA_UID_FIELD)
    query = custom_flag[lib.SPEC_FIELD][lib.QUERY_FIELD]
    if not uid:
        sq_uid = custom_flag[lib.METADATA_FIELD].get(lib.SAVED_QUERY_UID)
        schema = custom_flag[lib.METADATA_FIELD][lib.QUERY_SCHEMA_FIELD]
        if not sq_uid:
            sq_uid = __handle_missing_saved_query(
                schema,
                query,
                lib.CUSTOM_FLAG_KIND,
                custom_flag[lib.METADATA_FIELD][lib.METADATA_NAME_FIELD],
                sq_name,
            )
            custom_flag[lib.METADATA_FIELD][lib.SAVED_QUERY_UID] = sq_uid
    else:
        # Always grab the real saved query uid if available.
        # Using the edit command, someone could have changed the query uid
        # in the yaml which otherwise might lead to unintended consequences.
        cf_data = get_custom_flag(*ctx.get_api_data(), uid)
        sq_uid = cf_data["saved_query_uid"]
    # See if we need to update the saved query
    sq = get_saved_query(*ctx.get_api_data(), sq_uid)
    if sq["query"] != query:
        if cli.query_yes_no(
            "The custom flag query does not match the existing saved query."
            " Do you want to update the saved query?"
        ):
            sq["query"] = query
            put_saved_query_from_yaml(sq_uid, _r.saved_queries.data_to_yaml(sq))
        elif not cli.query_yes_no(
            "Do you want to continue applying the custom flag without updating"
            " the saved query?"
        ):
            cli.try_log("Operation cancelled.")
            sys.exit(0)
    if not uid:
        # Check if a custom flag with the same query and schema already exists
        matching_flags, _total_pages = get_custom_flags(
            *ctx.get_api_data(),
            **{
                "query_equals": sq["query"],
                "schema_equals": sq["schema"],
            },
        )
        if matching_flags and not cli.query_yes_no(
            "A Custom Flag with this Query and Schema already exists."
            " Do you still want to create this custom flag?",
            default="no",
        ):
            cli.try_log("Operation cancelled.")
            sys.exit(0)
        uid = post_custom_flag_from_yaml(custom_flag)
        cli.try_log(f"Successfully applied new custom flag with uid: {uid}")
    else:
        put_custom_flag_from_yaml(uid, custom_flag)
        if from_edit:
            cli.try_log(f"Successfully edited custom flag with uid: {uid}")
        else:
            cli.try_log(f"Successfully updated custom flag with uid: {uid}")
    return uid


def __handle_missing_saved_query(
    schema: str,
    query: str,
    dependent_resrc_kind: str,
    dependent_resrc_name: str,
    sq_name: Optional[str] = None,
) -> str:
    # Check for existing saved query with the same schema and query
    potential_saved_query_uid, q_name = check_for_duplicate_query(schema, query)
    if potential_saved_query_uid:
        if cli.query_yes_no(
            "Duplicate query found. Use existing saved query?"
            f" '{q_name} -- {potential_saved_query_uid}'"
        ):
            return potential_saved_query_uid
    # Create a new saved query
    if not cli.query_yes_no(
        f"Create a new saved query for this {dependent_resrc_kind}?"
    ):
        cli.try_log("Aborted.")
        sys.exit(0)
    sq = _r.saved_queries.data_to_yaml(
        {
            "name": sq_name
            or __generate_sq_name(dependent_resrc_kind, dependent_resrc_name),
            "schema": schema,
            "query": query,
            "description": f"Saved query for {dependent_resrc_kind}"
            f" {dependent_resrc_name} created by spyctl command on"
            f" {lib.epoch_to_zulu(time.time())}",
        }
    )
    return post_saved_query_from_yaml(sq)


def post_custom_flag_from_yaml(custom_flag: Dict) -> str:
    """
    Posts a new custom flag using the provided data.

    Args:
        custom_flag (Dict): The dictionary containing the custom flag data.

    Returns:
        str: The unique identifier of the newly created custom flag.
    """
    ctx = cfg.get_current_context()
    flag_settings = custom_flag[lib.SPEC_FIELD][lib.FLAG_SETTINGS_FIELD]
    req_body = {
        "name": custom_flag[lib.METADATA_FIELD][lib.METADATA_NAME_FIELD],
        "description": flag_settings[lib.FLAG_DESCRIPTION],
        "saved_query_uid": custom_flag[lib.METADATA_FIELD][lib.SAVED_QUERY_UID],
        "severity": flag_settings[lib.FLAG_SEVERITY],
        "type": flag_settings[lib.TYPE_FIELD],
    }
    if lib.METADATA_TAGS_FIELD in custom_flag[lib.METADATA_FIELD]:
        req_body["tags"] = custom_flag[lib.METADATA_FIELD][lib.METADATA_TAGS_FIELD]
    if lib.FLAG_IMPACT in flag_settings:
        req_body["impact"] = flag_settings[lib.FLAG_IMPACT]
    if lib.FLAG_CONTENT in flag_settings:
        req_body["content"] = flag_settings[lib.FLAG_CONTENT]
    if not custom_flag[lib.SPEC_FIELD][lib.ENABLED_FIELD]:
        req_body["is_disabled"] = True
    uid = post_new_custom_flag(*ctx.get_api_data(), **req_body)
    return uid


def put_custom_flag_from_yaml(uid: str, custom_flag: Dict) -> str:
    """
    Update a custom flag with the provided data.

    Args:
        uid (str): The unique identifier of the custom flag.
        custom_flag (Dict): The data to update the custom flag with.

    Returns:
        str: The unique identifier of the updated custom flag.
    """
    ctx = cfg.get_current_context()
    cf_data = get_custom_flag(*ctx.get_api_data(), uid)
    is_enabled = cf_data["is_enabled"]
    flag_settings = custom_flag[lib.SPEC_FIELD][lib.FLAG_SETTINGS_FIELD]
    req_body = {
        "name": custom_flag[lib.METADATA_FIELD][lib.METADATA_NAME_FIELD],
        "description": flag_settings[lib.FLAG_DESCRIPTION],
        "saved_query_uid": custom_flag[lib.METADATA_FIELD][lib.SAVED_QUERY_UID],
        "severity": flag_settings[lib.FLAG_SEVERITY],
        "type": flag_settings[lib.TYPE_FIELD],
        "notification_settings": custom_flag[lib.SPEC_FIELD].get(
            lib.NOTIFICATION_SETTINGS_FIELD
        ),
    }
    if lib.METADATA_TAGS_FIELD in custom_flag[lib.METADATA_FIELD]:
        req_body["tags"] = custom_flag[lib.METADATA_FIELD][lib.METADATA_TAGS_FIELD]
    if lib.FLAG_IMPACT in flag_settings:
        req_body["impact"] = flag_settings[lib.FLAG_IMPACT]
    if lib.FLAG_CONTENT in flag_settings:
        req_body["content"] = flag_settings[lib.FLAG_CONTENT]
    put_custom_flag_update(*ctx.get_api_data(), uid, **req_body)
    new_enabled = custom_flag[lib.SPEC_FIELD][lib.ENABLED_FIELD]
    if new_enabled != is_enabled and new_enabled:
        put_enable_custom_flag(*ctx.get_api_data(), uid)
    elif new_enabled != is_enabled and not new_enabled:
        put_disable_custom_flag(*ctx.get_api_data(), uid)
    return uid


# ----------------------------------------------------------------- #
#                          Helper Functions                         #
# ----------------------------------------------------------------- #


def __apply_priority(resrc: Dict) -> int:
    kind = resrc.get(lib.KIND_FIELD)
    return APPLY_PRIORITY.get(kind, 0)


def __generate_sq_name(dependent_resrc_kind, dependent_resrc_name: str) -> str:
    rv = f"Saved Query for {dependent_resrc_kind} {dependent_resrc_name}"
    rv = rv[:128]
    return rv


def check_for_duplicate_query(schema: str, query: str) -> Optional[str]:
    """
    Check if there is a duplicate query in the saved queries.

    Args:
        schema (str): The schema to check for duplicates.
        query (str): The query to check for duplicates.

    Returns:
        Optional[str]: The UID of the duplicate query if found, None otherwise.
    """
    ctx = cfg.get_current_context()
    query_params = {
        "schema_equals": schema,
        "query_equals": query,
        "page_size": 1,
    }
    saved_queries, _ = get_saved_queries(*ctx.get_api_data(), **query_params)
    if saved_queries:
        return saved_queries[0]["uid"], saved_queries[0]["name"]
    return None, None


# def __handle_matching_policies(
#     policy: Dict, matching_policies: Dict[str, Dict]
# ):
#     uid = policy[lib.METADATA_FIELD].get(lib.METADATA_UID_FIELD)
#     if uid:
#         return _r.suppression_policies.TraceSuppressionPolicy(policy)
#     query = (
#         "There already exists a policy matching this scope. Would you like"
#         " to merge this policy into the existing one?"
#     )
#     if not cli.query_yes_no(query):
#         return _r.suppression_policies.TraceSuppressionPolicy(policy)
#     ret_pol = policy
#     for uid, m_policy in matching_policies.items():
#         merged = m.merge_resource(ret_pol, "", m_policy)
#         if merged:
#             ret_pol = merged.get_obj_data()
#     ret_pol[lib.METADATA_FIELD][lib.METADATA_UID_FIELD] = uid
#     return _r.suppression_policies.TraceSuppressionPolicy(ret_pol)
