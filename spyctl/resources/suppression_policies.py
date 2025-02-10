import json
from typing import Dict, Tuple

import spyctl.config.configs as cfg
import spyctl.schemas_v2 as schemas
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.objects import get_objects


def build_trace_suppression_policy(
    trace_id,
    include_users,
    mode,
    name: str = None,
) -> Dict:
    """
    Build a trace suppression policy.

    Args:
        trace_id: The ID of the trace.
        include_users: A list of users to include in the suppression policy.
        mode: The suppression mode.
        name: The name of the suppression policy (optional).
        ctx: The context (optional).
        **selectors: Additional selectors for the suppression policy.

    Returns:
        The created trace suppression policy.

    Raises:
        ValueError: If the trace or trace summary cannot be found.
    """
    ctx = cfg.get_current_context()
    if trace_id:
        trace = get_objects(*ctx.get_api_data(), [trace_id])
        if not trace:
            cli.err_exit(f"Unable to find a Trace with UID {trace_id}")
        trace = trace[0]
        summary_uid = trace.get(lib.TRACE_SUMMARY_FIELD)
        if not summary_uid:
            cli.err_exit(
                f"Unable to find a Trace Summary for Trace {trace_id}"
            )
        t_sum = get_objects(*ctx.get_api_data(), [summary_uid])
        if not t_sum:
            cli.err_exit(
                f"Unable to find a Trace Summary with UID {summary_uid}"
            )
        t_sum = t_sum[0]
        pol = __build_trace_suppression_policy(
            t_sum, include_users, mode=mode, name=name
        )
    else:
        pol = __build_trace_suppression_policy(mode=mode, name=name)
    return pol


def __build_trace_suppression_policy(
    trace_summary: Dict = None,
    include_users: bool = False,
    mode: str = lib.POL_MODE_ENFORCE,
    name: str = None,
):
    if not trace_summary:
        return build_custom_trace_policy(mode, name)
    metadata = schemas.SuppressionPolicyMetadataModel(
        name=build_name(name, trace_summary.get("trigger_ancestors")),
        type=lib.POL_TYPE_TRACE,
    )
    trigger_ancestors = trace_summary.get("trigger_ancestors")
    trigger_class = trace_summary.get("trigger_class")
    t_sel = schemas.TraceSelectorModel(
        matchFields={
            lib.TRIGGER_ANCESTORS_FIELD: trigger_ancestors,
            lib.TRIGGER_CLASS_FIELD: trigger_class,
        }
    )
    u_sel = None
    if include_users:
        u_sel = schemas.UserSelectorModel(
            **trace_summary[lib.SPEC_FIELD][lib.USER_SELECTOR_FIELD]
        )
    allowed_flags = trace_summary[lib.SPEC_FIELD][lib.FLAG_SUMMARY_FIELD][
        lib.FLAGS_FIELD
    ]
    spec = schemas.SuppressionPolicySpecModel(
        traceSelector=t_sel,
        userSelector=u_sel,
        mode=mode,
        enabled=True,
        allowedFlags=allowed_flags,
    )
    return schemas.SuppressionPolicyModel(
        apiVersion=lib.API_VERSION,
        kind=lib.POL_KIND,
        metadata=metadata,
        spec=spec,
    ).model_dump(by_alias=True, exclude_unset=True, exclude_none=True)


def build_custom_trace_policy(
    mode: str = lib.POL_MODE_ENFORCE,
    name: str = None,
) -> Dict:
    metadata = schemas.SuppressionPolicyMetadataModel(
        name=build_name(name),
        type=lib.POL_TYPE_TRACE,
    )
    spec = schemas.SuppressionPolicySpecModel(
        mode=mode,
        enabled=True,
        allowedFlags=[],
    )
    return schemas.SuppressionPolicyModel(
        api=lib.API_VERSION,
        kind=lib.POL_KIND,
        metadata=metadata,
        spec=spec,
    ).model_dump(by_alias=True, exclude_unset=True)


def build_name(name, trigger_ancestors: str = None):
    if name:
        return name
    if not trigger_ancestors:
        name = "Custom Trace Suppression Policy"
    else:
        name = f"Trace Suppression Policy for {trigger_ancestors}"
    return name


def get_selector_hash(policy: Dict) -> str:
    """
    Returns a hash of the selector for a suppression policy.

    Args:
        policy: The suppression policy.

    Returns:
        The hash of the selector.
    """
    selectors = {}
    for field, value in policy["spec"].items():
        if field.endswith("Selector"):
            selectors[field] = value
    return lib.make_checksum(selectors)


def merge_allowed_flags(old_pol, new_pol) -> Tuple[Dict, bool]:
    """
    Merges the allowed flags of two suppression policies.

    Args:
        old_pol: The old suppression policy.
        new_pol: The new suppression policy.

    Returns:
        The merged suppression policy.
    """
    old_flags = old_pol["spec"]["allowedFlags"]
    old_flags_json = {json.dumps(flag) for flag in old_flags}
    new_flags = new_pol["spec"]["allowedFlags"]
    new_flags_json = {json.dumps(flag) for flag in new_flags}
    old_flags_json_cp = old_flags_json.copy()
    old_flags_json.update(new_flags_json)
    if old_flags_json_cp == old_flags_json:
        # No new flags so don't update
        return old_pol, False
    merged_flags = [json.loads(flag) for flag in old_flags_json]
    merged_flags.sort(key=lambda x: x[lib.FLAG_CLASS])
    old_pol["spec"]["allowedFlags"] = merged_flags
    return old_pol, True
