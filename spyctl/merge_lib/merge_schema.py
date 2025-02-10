"""
Module containing merge schemas which tells spyctl how to merge
certain fields
"""

from dataclasses import dataclass, field
from typing import Callable, Dict

import spyctl.merge_lib.merge_lib as m_lib
import spyctl.merge_lib.ruleset_policy_merge as _rm
import spyctl.merge_lib.workload_merge as _wl
import spyctl.spyctl_lib as lib


@dataclass
class MergeSchema:
    """Class to represent a merge schema for a field in a resource"""

    field_key: str
    sub_schemas: Dict[str, "MergeSchema"] = field(default_factory=dict)
    merge_functions: Dict[str, Callable] = field(default_factory=dict)
    values_required: bool = False
    # required because selectors behave differently
    # Each item in the merge must have at least one thing
    # in common for a given selector or that selector will remain
    # deleted.
    is_selector: bool = False


NET_POLICY_MERGE_SCHEMA = MergeSchema(
    lib.NET_POLICY_FIELD,
    merge_functions={
        lib.INGRESS_FIELD: _wl.merge_ingress_or_egress,
        lib.EGRESS_FIELD: _wl.merge_ingress_or_egress,
    },
)
CONTAINER_SELECTOR_MERGE_SCHEMA = MergeSchema(
    lib.CONT_SELECTOR_FIELD,
    merge_functions={
        lib.MATCH_FIELDS_FIELD: m_lib.common_keys_merge,
        lib.MATCH_FIELDS_EXPRESSIONS_FIELD: m_lib.expression_list_merge,
        lib.IMAGE_FIELD: m_lib.wildcard_merge,
        lib.IMAGEID_FIELD: m_lib.all_eq_merge,
        lib.CONT_NAME_FIELD: m_lib.wildcard_merge,
        lib.CONT_ID_FIELD: m_lib.all_eq_merge,
    },
    values_required=True,
    is_selector=True,
)
SVC_SELECTOR_MERGE_SCHEMA = MergeSchema(
    lib.SVC_SELECTOR_FIELD,
    merge_functions={
        lib.CGROUP_FIELD: m_lib.wildcard_merge,
        lib.MATCH_FIELDS_FIELD: m_lib.common_keys_merge,
        lib.MATCH_FIELDS_EXPRESSIONS_FIELD: m_lib.expression_list_merge,
    },
    values_required=True,
    is_selector=True,
)
CLUSTER_SELECTOR_MERGE_SCHEMA = MergeSchema(
    lib.CLUS_SELECTOR_FIELD,
    merge_functions={
        lib.MATCH_FIELDS_FIELD: m_lib.common_keys_merge,
        lib.MATCH_FIELDS_EXPRESSIONS_FIELD: m_lib.expression_list_merge,
    },
    values_required=True,
    is_selector=True,
)
MACHINE_SELECTOR_MERGE_SCHEMA = MergeSchema(
    lib.MACHINE_SELECTOR_FIELD,
    merge_functions={
        lib.HOSTNAME_FIELD: m_lib.conditional_string_list_merge,
        lib.MACHINE_UID_FIELD: m_lib.conditional_string_list_merge,
        lib.MATCH_FIELDS_FIELD: m_lib.common_keys_merge,
        lib.MATCH_FIELDS_EXPRESSIONS_FIELD: m_lib.expression_list_merge,
    },
    values_required=True,
    is_selector=True,
)
POD_SELECTOR_MERGE_SCHEMA = MergeSchema(
    lib.POD_SELECTOR_FIELD,
    merge_functions={
        lib.MATCH_LABELS_FIELD: m_lib.common_keys_merge,
    },
    values_required=True,
    is_selector=True,
)
NAMESPACE_SELECTOR_MERGE_SCHEMA = MergeSchema(
    lib.NAMESPACE_SELECTOR_FIELD,
    merge_functions={
        lib.MATCH_LABELS_FIELD: m_lib.common_keys_merge,
        lib.MATCH_EXPRESSIONS_FIELD: m_lib.expression_list_merge,
    },
    values_required=True,
    is_selector=True,
)
TRACE_SELECTOR_MERGE_SCHEMA = MergeSchema(
    lib.TRACE_SELECTOR_FIELD,
    merge_functions={
        lib.TRIGGER_ANCESTORS_FIELD: m_lib.all_eq_merge,
        lib.TRIGGER_CLASS_FIELD: m_lib.all_eq_merge,
        lib.MATCH_FIELDS_FIELD: m_lib.common_keys_merge,
        lib.MATCH_FIELDS_EXPRESSIONS_FIELD: m_lib.expression_list_merge,
    },
    values_required=True,
    is_selector=True,
)
USER_SELECTOR_MERGE_SCHEMA = MergeSchema(
    lib.USER_SELECTOR_FIELD,
    merge_functions={
        lib.USERS_FIELD: m_lib.string_list_merge,
        lib.INTERACTIVE_USERS_FIELD: m_lib.string_list_merge,
        lib.NON_INTERACTIVE_USERS_FIELD: m_lib.string_list_merge,
        lib.MATCH_FIELDS_FIELD: m_lib.common_keys_merge,
        lib.MATCH_FIELDS_EXPRESSIONS_FIELD: m_lib.expression_list_merge,
    },
)
PROCESS_SELECTOR_MERGE_SCHEMA = MergeSchema(
    lib.USER_SELECTOR_FIELD,
    merge_functions={
        lib.NAME_FIELD: m_lib.string_list_merge,
        lib.EXE_FIELD: m_lib.string_list_merge,
        lib.EUSER_FIELD: m_lib.string_list_merge,
        lib.INTERACTIVE_FIELD: m_lib.keep_base_value_merge,
        lib.MATCH_FIELDS_FIELD: m_lib.common_keys_merge,
        lib.MATCH_FIELDS_EXPRESSIONS_FIELD: m_lib.expression_list_merge,
    },
)
SPEC_MERGE_SCHEMA = MergeSchema(
    lib.SPEC_FIELD,
    sub_schemas={
        lib.SVC_SELECTOR_FIELD: SVC_SELECTOR_MERGE_SCHEMA,
        lib.CONT_SELECTOR_FIELD: CONTAINER_SELECTOR_MERGE_SCHEMA,
        lib.CLUS_SELECTOR_FIELD: CLUSTER_SELECTOR_MERGE_SCHEMA,
        lib.MACHINE_SELECTOR_FIELD: MACHINE_SELECTOR_MERGE_SCHEMA,
        lib.POD_SELECTOR_FIELD: POD_SELECTOR_MERGE_SCHEMA,
        lib.NAMESPACE_SELECTOR_FIELD: NAMESPACE_SELECTOR_MERGE_SCHEMA,
        lib.NET_POLICY_FIELD: NET_POLICY_MERGE_SCHEMA,
    },
    merge_functions={
        lib.ENABLED_FIELD: m_lib.keep_base_value_merge,
        lib.PROC_POLICY_FIELD: _wl.merge_proc_policies,
        lib.RESPONSE_FIELD: m_lib.keep_base_value_merge,
        lib.DISABLE_PROCS_FIELD: m_lib.keep_base_value_merge,
        lib.DISABLE_CONNS_FIELD: m_lib.keep_base_value_merge,
        lib.DISABLE_PU_CONNS_FIELD: m_lib.keep_base_value_merge,
        lib.DISABLE_PR_CONNS_FIELD: m_lib.keep_base_value_merge,
        lib.POL_MODE_FIELD: m_lib.keep_base_value_merge,
    },
    values_required=True,
)
FPRINT_METADATA_MERGE_SCHEMA = MergeSchema(
    lib.METADATA_FIELD,
    merge_functions={
        lib.METADATA_NAME_FIELD: m_lib.wildcard_merge,
        lib.METADATA_TYPE_FIELD: m_lib.all_eq_merge,
        lib.LATEST_TIMESTAMP_FIELD: m_lib.greatest_value_merge,
    },
)
FPRINT_MERGE_SCHEMAS = [FPRINT_METADATA_MERGE_SCHEMA, SPEC_MERGE_SCHEMA]
TRACE_SUPPRESSION_SPEC_MERGE_SCHEMA = MergeSchema(
    lib.SPEC_FIELD,
    sub_schemas={
        lib.SVC_SELECTOR_FIELD: SVC_SELECTOR_MERGE_SCHEMA,
        lib.CONT_SELECTOR_FIELD: CONTAINER_SELECTOR_MERGE_SCHEMA,
        lib.CLUS_SELECTOR_FIELD: CLUSTER_SELECTOR_MERGE_SCHEMA,
        lib.MACHINE_SELECTOR_FIELD: MACHINE_SELECTOR_MERGE_SCHEMA,
        lib.POD_SELECTOR_FIELD: POD_SELECTOR_MERGE_SCHEMA,
        lib.NAMESPACE_SELECTOR_FIELD: NAMESPACE_SELECTOR_MERGE_SCHEMA,
        lib.TRACE_SELECTOR_FIELD: TRACE_SELECTOR_MERGE_SCHEMA,
        lib.USER_SELECTOR_FIELD: USER_SELECTOR_MERGE_SCHEMA,
    },
    merge_functions={
        lib.ENABLED_FIELD: m_lib.keep_base_value_merge,
        lib.ALLOWED_FLAGS_FIELD: m_lib.unique_dict_list_merge,
        lib.RESPONSE_FIELD: m_lib.keep_base_value_merge,
    },
)
POLICY_META_MERGE_SCHEMA = MergeSchema(
    lib.METADATA_FIELD,
    merge_functions={
        lib.METADATA_NAME_FIELD: m_lib.keep_base_value_merge,
        lib.METADATA_TYPE_FIELD: m_lib.keep_base_value_merge,
        lib.METADATA_UID_FIELD: m_lib.keep_base_value_merge,
        lib.METADATA_CREATE_TIME: m_lib.keep_base_value_merge,
        lib.LATEST_TIMESTAMP_FIELD: m_lib.greatest_value_merge,
    },
)
POLICY_MERGE_SCHEMAS = [POLICY_META_MERGE_SCHEMA, SPEC_MERGE_SCHEMA]
RULESET_POLICY_MERGE_SCHEMAS = []
S_POLICY_META_MERGE_SCHEMA = MergeSchema(
    lib.METADATA_FIELD,
    merge_functions={
        lib.METADATA_NAME_FIELD: m_lib.keep_base_value_merge,
        lib.METADATA_TYPE_FIELD: m_lib.all_eq_merge,
        lib.METADATA_UID_FIELD: m_lib.keep_base_value_merge,
        lib.METADATA_CREATE_TIME: m_lib.keep_base_value_merge,
        lib.LATEST_TIMESTAMP_FIELD: m_lib.greatest_value_merge,
    },
)
T_S_POLICY_MERGE_SCHEMAS = [
    S_POLICY_META_MERGE_SCHEMA,
    TRACE_SUPPRESSION_SPEC_MERGE_SCHEMA,
]

RULESET_META_MERGE_SCHEMA = MergeSchema(
    lib.METADATA_FIELD,
    merge_functions={
        lib.METADATA_NAME_FIELD: m_lib.keep_base_value_merge,
        lib.METADATA_TYPE_FIELD: m_lib.keep_base_value_merge,
        lib.METADATA_UID_FIELD: m_lib.keep_base_value_merge,
        lib.METADATA_CREATE_TIME: m_lib.keep_base_value_merge,
        lib.METADATA_CREATED_BY: m_lib.keep_base_value_merge,
        lib.METADATA_LAST_UPDATE_TIME: m_lib.keep_base_value_merge,
        lib.METADATA_LAST_UPDATED_BY: m_lib.keep_base_value_merge,
        lib.METADATA_VERSION_FIELD: m_lib.keep_base_value_merge,
    },
)

RULESET_SPEC_MERGE_SCHEMA = MergeSchema(
    lib.SPEC_FIELD,
    merge_functions={
        lib.RULES_FIELD: _rm.merge_rules,
    },
)

RULESET_MERGE_SCHEMAS = [RULESET_META_MERGE_SCHEMA, RULESET_SPEC_MERGE_SCHEMA]
