from typing import (
    Dict,
)

import spyctl.schemas_v2 as schemas
import spyctl.spyctl_lib as lib
from spyctl import cli
import spyctl.merge_lib.merge_schema as _ms
from spyctl.merge_lib.merge_object import MergeObject
from spyctl.merge_lib.ruleset_merge_object import RulesetPolicyMergeObject


def get_merge_object(
    resrc_kind: str, target: Dict, merge_network: bool, src_cmd: str
):
    if resrc_kind == lib.POL_KIND:
        resrc_type = target[lib.METADATA_FIELD][lib.METADATA_TYPE_FIELD]
        if resrc_type == lib.POL_TYPE_TRACE:
            merge_schemas = _ms.T_S_POLICY_MERGE_SCHEMAS
        else:
            merge_schemas = _ms.POLICY_MERGE_SCHEMAS
        has_rulesets = bool(target[lib.SPEC_FIELD].get(lib.RULESETS_FIELD))
        if has_rulesets:
            merge_schemas = _ms.RULESET_POLICY_MERGE_SCHEMAS
            merge_obj = RulesetPolicyMergeObject(
                target, merge_schemas, schemas.valid_object, merge_network
            )
        else:
            merge_obj = MergeObject(
                target, merge_schemas, schemas.valid_object, merge_network
            )
            # merge_obj.asymmetric_merge(other=merge_obj.original_obj)
            # merge_obj.original_obj = merge_obj.obj_data
    elif resrc_kind == lib.RULESET_KIND:
        merge_obj = MergeObject(
            target, _ms.RULESET_MERGE_SCHEMAS, schemas.valid_object
        )
    else:
        cli.try_log(
            f"The '{src_cmd}' command is not supported for {resrc_kind}",
            is_warning=True,
        )
    return merge_obj
