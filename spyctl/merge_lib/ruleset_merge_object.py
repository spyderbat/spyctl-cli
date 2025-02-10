from collections import defaultdict
from typing import Callable, Dict, List, Optional, Tuple, Union

import spyctl.config.configs as cfg
import spyctl.merge_lib.merge_schema as _ms
import spyctl.merge_lib.ruleset_policy_merge as _rpm
import spyctl.schemas_v2 as schemas
import spyctl.spyctl_lib as lib
from spyctl.merge_lib.merge_object import MergeObject
from spyctl.api.rulesets import get_rulesets


class RulesetPolicyMergeObject(MergeObject):
    def __init__(
        self,
        obj_data: Dict,
        merge_schemas: List[_ms.MergeSchema],
        validation_fn: Callable,
        merge_network: bool = True,
        disable_procs: str = None,
        disable_conns: str = None,
    ) -> None:
        super().__init__(
            obj_data,
            merge_schemas,
            validation_fn,
            merge_network,
            disable_procs,
            disable_conns,
        )
        self.rulesets: Dict[str, MergeObject] = []
        # rs_name -> RulesTracker
        self.ruleset_trackers: Dict[str, _rpm.RulesTracker] = {}
        self.targets_to_rs: Dict[str, Dict[str, bool]] = defaultdict(dict)
        self.load_rulesets()

    def asymmetric_merge(self, other: Dict, check_irrelevant=False):
        other_kind = other[lib.KIND_FIELD]
        if other_kind in [
            lib.RULESET_KIND,
            lib.DEVIATION_KIND,
        ]:
            changed = _rpm.merge_rulesets(self, other)
            checksum_or_id = self.get_checksum_or_id(other)
            if not changed:
                self.irrelevant_objects.setdefault(other_kind, set()).add(
                    checksum_or_id
                )
            else:
                self.relevant_objects.setdefault(other_kind, set()).add(
                    checksum_or_id
                )

        return super().asymmetric_merge(other, check_irrelevant)

    def load_rulesets(self, ctx: cfg.Context = None):
        """
        Load rulesets for the merge object.

        Args:
            src_cmd (str): The source command.
            ctx (cfg.Context, optional): The context. Defaults to None.

        Returns:
            None
        """
        pol_uid = self.original_obj[lib.METADATA_FIELD][lib.METADATA_UID_FIELD]
        if not ctx:
            ctx = cfg.get_current_context()
        rs_data = get_rulesets(
            *ctx.get_api_data(), params={"in_policy": pol_uid}
        )
        self.rulesets = {
            rs_dict[lib.METADATA_FIELD][lib.METADATA_NAME_FIELD]: MergeObject(
                rs_dict, _ms.RULESET_MERGE_SCHEMAS, schemas.valid_object
            )
            for rs_dict in rs_data
        }
        self.sort_ruleset_rules()
        _rpm.build_rules_by_rs(self)

    def sort_ruleset_rules(self, orig_obj=True):
        """Sort the rulesets by their order."""

        def sort_key(rule: Dict) -> Tuple:
            return (
                rule[lib.RULE_TARGET_FIELD],
                rule[lib.RULE_VERB_FIELD],
                next(iter(rule[lib.RULE_VALUES_FIELD]), None),
            )

        for rs in self.rulesets.values():
            if orig_obj:
                rules: List[Dict] = rs.original_obj[lib.SPEC_FIELD][
                    lib.RULES_FIELD
                ]
            else:
                rules: List[Dict] = rs.obj_data[lib.SPEC_FIELD][
                    lib.RULES_FIELD
                ]
            for rule in rules:
                self.sort_rule_values(rule)
            rules.sort(key=sort_key)

    def sort_rule_values(self, rule: Dict) -> Dict:
        """Sort the values of a rule."""
        values: List[str] = rule[lib.RULE_VALUES_FIELD]
        values.sort()

    def get_default_rules_tracker(
        self, target: str
    ) -> Tuple[str, _rpm.RulesTracker]:
        """Retrieve ruleset rules tracker for the default ruleset.
        The default ruleset is the one that gets any new rules
        that don't have a pre-determined ruleset.
        """
        rs_names = self.targets_to_rs.get(target)
        if not rs_names:
            return next(iter(self.ruleset_trackers.items()))
        rs_name = next(iter(rs_names))
        return rs_name, self.ruleset_trackers[rs_name]

    def get_diff(
        self, full_diff=False, diff_object=False, only_rulesets=True
    ) -> Optional[Union[str, Dict]]:
        if only_rulesets:
            rv = []
            pol_name = self.original_obj[lib.METADATA_FIELD][
                lib.METADATA_NAME_FIELD
            ]
            rv.append(f'Diff for rulesets in policy "{pol_name}"')
            for rs_name, rs in self.rulesets.items():
                rv.append("--------------------------------")
                rv.append(f'Ruleset "{rs_name}":')
                rv.append("================================")
                rv.append(rs.get_diff(full_diff, diff_object))
            return "\n".join(rv)
        return super().get_diff(full_diff, diff_object)
