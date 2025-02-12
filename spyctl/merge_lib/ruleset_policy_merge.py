"""Module containing the code to merge ruleset deviations into a policy"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Tuple, Union

import spyctl.rules_lib.rule as _r
import spyctl.rules_lib.scope as _scp
import spyctl.spyctl_lib as lib

if TYPE_CHECKING:
    from spyctl.merge_lib.merge_object import MergeObject
    from spyctl.merge_lib.ruleset_merge_object import RulesetPolicyMergeObject

DENY_TYPE_DEFAULT = "default"
DENY_TYPE_GLOBAL = "global"
DENY_TYPE_SCOPED = "scoped"
DENY_TYPES = {}


@dataclass
class RulesTracker:
    """Tracks information about rules across all rulesets in a single policy"""

    ruleset: str
    rules_map: Dict[_r.BaseRule, Dict]  # built_rule -> rule_data


@dataclass
class PolicyMatchTracker:
    """Aggregates match information across all rulesets"""

    deny_type: str = DENY_TYPE_DEFAULT
    # The first allow rule we find that matches the scope
    # of the deviation
    first_in_scope_allow: Tuple[_r.BaseRule, List[int]] = None
    scoped_denies: Dict[str, Dict[_r.BaseRule, List[int]]] = field(default_factory=dict)
    global_denies: Dict[str, Dict[_r.BaseRule, List[int]]] = field(default_factory=dict)

    def add_in_scope_allow(self, rule: _r.BaseRule, indexes: List[int]):
        """In this case there is already an allow rule that
        matches the scope of the deviation. It just needs the
        value added to it.
        """
        add_in_scope_allow(self, rule, indexes)


@dataclass
class MatchTracker:
    """Tracks information about a rule match"""

    first_in_scope_allow: Tuple[_r.BaseRule, List[int]] = None
    # Each set contains the rules that matched and the indexes
    # of the value(s) it matched on.
    scoped_allows: Dict[_r.BaseRule, List[int]] = field(default_factory=dict)
    scoped_denies: Dict[_r.BaseRule, List[int]] = field(default_factory=dict)
    global_allows: Dict[_r.BaseRule, List[int]] = field(default_factory=dict)
    global_denies: Dict[_r.BaseRule, List[int]] = field(default_factory=dict)

    def add_in_scope_allow(self, rule: _r.BaseRule, indexes: List[int]):
        """Determines which rule can be updated with the deviation value
        to add it to the ruleset.
        """
        add_in_scope_allow(self, rule, indexes)


def add_in_scope_allow(
    tracker: Union[PolicyMatchTracker, MatchTracker],
    rule: _r.BaseRule,
    indexes: List[int],
):
    if not tracker.first_in_scope_allow or (
        not tracker.first_in_scope_allow[0].is_scoped and rule.is_scoped
    ):
        # We set the new rule as the first in scope allow
        # if there isn't one already or if the existing one
        # is not scoped and the new one is.
        tracker.first_in_scope_allow = (rule, indexes)
    elif tracker.first_in_scope_allow[0].is_scoped == rule.is_scoped:
        # If the existing rule and the new rule have the same scope
        # level, but the new one has matching values and the existing
        # one doesn't
        if len(tracker.first_in_scope_allow[1]) == 0 and len(indexes) > 0:
            tracker.first_in_scope_allow = (rule, indexes)


def merge_rulesets(mo: RulesetPolicyMergeObject, new: Dict):
    if not mo.rulesets:
        lib.try_log("No existing rulesets to merge into")
        return
    new_kind = new[lib.KIND_FIELD]
    if new_kind == lib.DEVIATION_KIND:
        return merge_deviation_rules(mo, new)
    lib.err_exit(f"Ruleset merge not implemented yet for {new_kind}")


def merge_deviation_rules(mo: RulesetPolicyMergeObject, deviation: Dict) -> bool:
    changed = False
    scopes = deviation[lib.METADATA_FIELD][lib.METADATA_SCOPES_FIELD]
    built_scopes = _scp.build_scopes(scopes)
    deviation_rules = deviation[lib.SPEC_FIELD][lib.RULES_FIELD]
    if not deviation_rules:
        lib.try_log("No new rules to merge")
        return
    for rule in deviation_rules:
        if merge_deviation_rule(mo, rule, built_scopes):
            changed = True
    for rs_name, rules_tracker in mo.ruleset_trackers.items():
        rs = mo.rulesets[rs_name]
        rs.obj_data[lib.SPEC_FIELD][lib.RULES_FIELD] = list(
            rules_tracker.rules_map.values()
        )
    mo.sort_ruleset_rules(orig_obj=False)
    return changed


def merge_deviation_rule(
    mo: RulesetPolicyMergeObject,
    rule: Dict,
    built_scopes: Dict[str, _scp.BaseScope],
) -> bool:
    values = rule[lib.RULE_VALUES_FIELD]
    target = rule[lib.RULE_TARGET_FIELD]
    changed = False
    for value in values:
        pmt = evaluate_deviation_value(
            mo.targets_to_rs, mo.ruleset_trackers, built_scopes, target, value
        )
        fa_rule, fa_ind = (
            pmt.first_in_scope_allow
            if pmt.first_in_scope_allow
            else (
                None,
                None,
            )
        )
        deny_type = pmt.deny_type
        # Add in the deviation value
        if not fa_rule:
            changed = True
            rs_name, rt = mo.get_default_rules_tracker(target)
            if pmt.deny_type == DENY_TYPE_SCOPED:
                # We need to add a new scope rule
                rs_scope_denies = next(iter(pmt.scoped_denies.values()))
                rs_scope_deny = next(iter(rs_scope_denies))
                selectors = rs_scope_deny.selectors_data
            else:
                # We need to add a new rule
                selectors = None
            new_rule = _r.new_rule(target, _r.VERB_ALLOW, [value], selectors)
            new_built_rule = _r.build_rule(new_rule, rs_name)
            rt.rules_map[new_built_rule] = new_rule
            # Update targets_to_rs
            mo.targets_to_rs[target][rs_name] = True
        elif len(fa_ind) == 0:
            changed = True
            rt = mo.ruleset_trackers[fa_rule.rs_name]
            if not fa_rule.is_scoped and deny_type == DENY_TYPE_SCOPED:
                # We need to add a new scoped rule
                rs_scope_denies = next(iter(pmt.scoped_denies.values()))
                rs_scope_deny = next(iter(rs_scope_denies))
                selectors = rs_scope_deny.selectors_data
                new_rule = _r.new_rule(target, _r.VERB_ALLOW, [value], selectors)
                new_built_rule = _r.build_rule(new_rule, fa_rule.rs_name)
                rt.rules_map[new_built_rule] = new_rule
            else:
                # We need to add the value to the existing rule
                # We pop off the old one and add the updated one
                rule_data_cp = deepcopy(rt.rules_map.pop(fa_rule))
                rule_data_cp[lib.RULE_VALUES_FIELD].append(value)
                new_built_rule = _r.build_rule(rule_data_cp, fa_rule.rs_name)
                rt.rules_map[new_built_rule] = rule_data_cp
        else:
            rt = mo.ruleset_trackers[fa_rule.rs_name]
            if not fa_rule.is_scoped and deny_type == DENY_TYPE_SCOPED:
                # We need to add a new scoped rule
                changed = True
                rs_scope_denies = next(iter(pmt.scoped_denies.values()))
                rs_scope_deny = next(iter(rs_scope_denies))
                selectors = rs_scope_deny.selectors_data
                new_rule = _r.new_rule(target, _r.VERB_ALLOW, [value], selectors)
                new_built_rule = _r.build_rule(new_rule, fa_rule.rs_name)
                rt.rules_map[new_built_rule] = new_rule
            else:
                # The allow rule already exists so don't need to do anything
                pass
        # Clear any deny rule values that were matched
        if pmt.scoped_denies:
            # Clear any scoped denies, but leave global ones
            for rs_name, rs_scope_denies in pmt.scoped_denies.items():
                rt = mo.ruleset_trackers[rs_name]
                for deny_rule, matched_indexes in rs_scope_denies.items():
                    deny_rule_cp = deepcopy(rt.rules_map.pop(deny_rule))
                    if matched_indexes:
                        changed = True
                        for mi in reversed(matched_indexes):
                            deny_rule_cp[lib.RULE_VALUES_FIELD].pop(mi)
                    if len(deny_rule_cp[lib.RULE_VALUES_FIELD]) > 0:
                        # The rule still has values so we can keep it
                        new_built_deny = _r.build_rule(deny_rule_cp, rs_name)
                        rt.rules_map[new_built_deny] = deny_rule_cp
                    else:
                        # The rule has no values so we can remove it
                        pass
        elif pmt.global_denies:
            # Clear global denies
            for rs_name, rs_global_denies in pmt.global_denies.items():
                rt = mo.ruleset_trackers[rs_name]
                for deny_rule, matched_indexes in rs_global_denies.items():
                    deny_rule_cp = deepcopy(rt.rules_map.pop(deny_rule))
                    if matched_indexes:
                        changed = True
                        for mi in reversed(matched_indexes):
                            deny_rule_cp[lib.RULE_VALUES_FIELD].pop(mi)
                    if len(deny_rule_cp[lib.RULE_VALUES_FIELD]) > 0:
                        # The rule still has values so we can keep it
                        new_built_deny = _r.build_rule(deny_rule_cp, rs_name)
                        rt.rules_map[new_built_deny] = deny_rule_cp
                    else:
                        # The rule has no values so we can remove it
                        pass
    return changed


def evaluate_deviation_value(
    targets_to_rs: Dict[str, Dict[str, bool]],
    ruleset_trackers: Dict[str, RulesTracker],
    built_scopes: Dict[str, _scp.BaseScope],
    target: str,
    value: str,
) -> PolicyMatchTracker:
    rv = PolicyMatchTracker()
    rulesets_with_tgt = targets_to_rs.get(target)
    if not rulesets_with_tgt:
        # No rulesets with this target, a new rule
        # will have to be added
        return rv
    for rs_name in rulesets_with_tgt:
        match_tracker = evaluate_in_rs_rules(
            built_scopes, target, value, ruleset_trackers[rs_name]
        )
        __update_pol_tracker_denies(rv, match_tracker, rs_name)
        __update_pol_tacker_allows(rv, match_tracker)
    return rv


def __update_pol_tracker_denies(
    pmt: PolicyMatchTracker, mt: MatchTracker, rs_name: str
):
    if mt.scoped_denies:
        pmt.deny_type = DENY_TYPE_SCOPED
        pmt.scoped_denies[rs_name] = mt.scoped_denies
    elif mt.global_denies:
        if pmt.deny_type == DENY_TYPE_DEFAULT:
            pmt.deny_type = DENY_TYPE_GLOBAL
        pmt.global_denies[rs_name] = mt.global_denies


def __update_pol_tacker_allows(pmt: PolicyMatchTracker, mt: MatchTracker):
    if mt.first_in_scope_allow:
        pmt.add_in_scope_allow(*mt.first_in_scope_allow)


def evaluate_in_rs_rules(
    built_scopes: Dict[str, _scp.BaseScope],
    target: str,
    value: str,
    tracker: RulesTracker,
) -> MatchTracker:
    """Builds a match tracker for a single ruleset"""
    rv = MatchTracker()
    for built_rule in tracker.rules_map:
        if built_rule.target != target:
            continue
        evaluate_in_rs_rule(rv, built_scopes, built_rule, value)
    return rv


def evaluate_in_rs_rule(
    mt: MatchTracker,
    built_scopes: Dict[str, _scp.BaseScope],
    built_rule: _r.BaseRule,
    value: str,
):
    """Evaluates a single value against a single rule
    in a ruleset. And adds the result to the ruleset's
    match tracker.
    """
    if not built_rule.in_scope(built_scopes):
        return
    explicit_ind, glob_ind = built_rule.in_values(value)
    if explicit_ind or glob_ind:
        if built_rule.is_scoped:
            if built_rule.verb == _r.VERB_ALLOW:
                mt.add_in_scope_allow(built_rule, explicit_ind)
                mt.scoped_allows[built_rule] = explicit_ind
            else:
                mt.scoped_denies[built_rule] = explicit_ind
        else:
            if built_rule.verb == _r.VERB_ALLOW:
                mt.add_in_scope_allow(built_rule, explicit_ind)
                mt.global_allows[built_rule] = explicit_ind
            else:
                mt.global_denies[built_rule] = explicit_ind
    else:
        if built_rule.verb == _r.VERB_ALLOW:
            mt.add_in_scope_allow(built_rule, explicit_ind)


def build_rules_by_rs(mo: RulesetPolicyMergeObject):
    for rs_mo in mo.rulesets.values():
        rs_name = rs_mo.original_obj[lib.METADATA_FIELD][lib.METADATA_NAME_FIELD]
        rules = rs_mo.original_obj[lib.SPEC_FIELD].get(lib.RULES_FIELD, [])
        rules_map = {}
        for rule in rules:
            built_rule = _r.build_rule(rule, rs_name)
            mo.targets_to_rs[rule[lib.RULE_TARGET_FIELD]][rs_name] = True
            rules_map[built_rule] = rule
        mo.ruleset_trackers[rs_name] = RulesTracker(rs_name, rules_map)


def merge_rules(mo: MergeObject, base_value: List[Dict], new_value: List[Dict], _):
    is_ruleset_merge = mo.current_other[lib.KIND_FIELD] == lib.RULESET_KIND
    if not is_ruleset_merge:
        return __merge_deviation_rules(mo, base_value, new_value, _)
    lib.err_exit("Ruleset merge not implemented yet.")


def __merge_deviation_rules(
    mo: MergeObject, base_value: List[Dict], new_value: List[Dict], _
):
    scopes = mo.current_other[lib.METADATA_FIELD][lib.METADATA_SCOPES_FIELD]
    built_scopes = _scp.build_scopes(scopes)
    built_rules = getattr(mo, "built_rules", None)
    if built_rules is None:
        built_rules = _r.build_rules(base_value)
        setattr(mo, "built_rules", built_rules)
    rv = []
    new_built_rules = []
    # Loop through each rule in the deviation and compare
    # it to each rule in the existing ruleset.
    # If the deviation rule is in scope with the existing rule
    # Then we need to perform some checks:
    # 1. If the existing rule is an allow rule we need to make sure
    #    the deviation value is in the rule
    # 2. If the existing rule is a deny rule we need to make sure
    #    the deviation value is not in the rule so that the deviation
    #    won't be generated again.
    # We could also find no matching rules in which case we need to
    # add the deviation rule to the return value.
    for rule in new_value:
        allow_found = False
        value = next(iter(rule[lib.RULE_VALUES_FIELD]))
        for orig_rule, built_rule in zip(base_value, built_rules):
            if rule[lib.RULE_TARGET_FIELD] != built_rule.target:
                continue
            if not built_rule.in_scope(built_scopes):
                rv.append(orig_rule)
                new_built_rules.append(built_rule)
                continue
            value_indexes = built_rule.in_values(value)
            if value_indexes:
                # Scope matches and a matching value is in the rule
                if built_rule.verb == _r.VERB_ALLOW:
                    # We found an allow rule, so we won't need to add the value
                    # later
                    allow_found = True
                    rv.append(orig_rule)
                    new_built_rules.append(built_rule)
                else:
                    # This is a deny rule, so we need to remove the value(s)
                    # otherwise the value will stay denied
                    for vi in reversed(value_indexes):
                        orig_rule[lib.RULE_VALUES_FIELD].pop(vi)
                    if len(orig_rule[lib.RULE_VALUES_FIELD]) > 0:
                        # We still have other values so this rule can
                        # stick around
                        rv.append(orig_rule)
                        new_built_rules.append(_r.build_rule(orig_rule))
                    else:
                        # No more values so we can remove the rule
                        # by not adding it to the return value
                        continue
            else:
                # Scope matches but the value is not in the rule
                if built_rule.verb == _r.VERB_ALLOW:
                    # We found an allow rule, add the value to the rule
                    # if we haven't already done so elsewhere
                    if not allow_found:
                        orig_rule[lib.RULE_VALUES_FIELD].append(value)
                        orig_rule[lib.RULE_VALUES_FIELD].sort()
                        allow_found = True
                    rv.append(orig_rule)
                    new_built_rules.append(_r.build_rule(orig_rule))
                else:
                    # We found a deny rule with no matching value, do nothing
                    rv.append(orig_rule)
                    new_built_rules.append(built_rule)
        if not allow_found:
            # No matching rules found, add the deviation rule
            rv.append(rule)
            new_built_rules.append(_r.build_rule(rule))
    setattr(mo, "built_rules", new_built_rules)
    return rv
