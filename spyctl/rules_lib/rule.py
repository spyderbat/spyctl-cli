"""Contains the logic specific to rules that go into rulesets."""

from typing import Any, Dict, List

import spyctl.rules_lib.scope as _scp
import spyctl.rules_lib.selector_helpers as _sel_h
import spyctl.rules_lib.selectors as sel
import spyctl.spyctl_lib as lib

VERB_FIELD = "verb"
VALUES_FIELD = "values"
TARGET_FIELD = "target"
VERB_ALLOW = "allow"
VERB_DENY = "deny"
ALLOWED_VERBS = {VERB_ALLOW, VERB_DENY}


class BaseRule:
    supported_selectors = {}

    def __init__(self, rule_data: Dict[str, Any], rs_name: str = None) -> None:
        # Validate rule data
        verb = rule_data.get(VERB_FIELD)
        if verb not in ALLOWED_VERBS:
            raise ValueError(f"Invalid verb: {verb}")
        values = rule_data.get(VALUES_FIELD)
        if not values:
            raise ValueError("Rule has no values")
        # Set attributes
        self.values: list[sel.StringSelector] = [
            sel.StringSelector(None, value) for value in values
        ]
        self.rs_name = rs_name
        self.verb: str = verb
        self.selectors_hash: str = None
        self.__full_hash: str = lib.make_checksum(rule_data)
        self.selectors_data: Dict = None
        self.selectors_objs: Dict[str, sel.ScopeSelector] = {}
        self.target: str = rule_data.get(TARGET_FIELD)
        self.__set_selectors(rule_data)

    @property
    def is_scoped(self):
        """If the rule has selectors."""
        return bool(self.selectors_data)

    def __hash__(self) -> int:
        return hash(self.__full_hash)

    def in_scope(self, scopes: Dict[str, _scp.BaseScope]) -> bool:
        for field, selector in self.selectors_objs.items():
            if not selector.in_scope(scopes.get(field)):
                return False
        return True

    def in_values(self, value: str) -> List[int]:
        explicit_matches = []
        glob_matches = []
        for i, str_sel in enumerate(self.values):
            if str_sel.match(value):
                if not str_sel.glob_evaluator:
                    explicit_matches.append(i)
                else:
                    glob_matches.append(i)
        # Glob matches do not need to be removed
        # simply adding an explicit allow will override
        # the glob deny. So we treat them differently.
        return explicit_matches, glob_matches

    def __set_selectors(self, rule_data: Dict[str, Any]) -> None:
        selectors_data = {}
        for field in self.supported_selectors:
            sel_data = rule_data.get(field)
            if sel_data:
                selectors_data[field] = sel_data
        exprs = _sel_h.exprs_from_spec(selectors_data)
        selector_objs = {}
        for field, selector_class in self.supported_selectors.items():
            selector: sel.ScopeSelector = selector_class()
            if field in exprs:
                selector.add_expression_group(exprs[field])
            else:
                selector.add_expression_group(force=True)
            selector_objs[field] = selector
        self.selectors_objs = selector_objs
        self.selectors_hash = lib.make_checksum(selectors_data)
        self.selectors_data = selectors_data


class ContainerRule(BaseRule):
    supported_selectors = {
        sel.CLUSTER_SELECTOR_FIELD: sel.ClusterSelector,
        sel.MACHINE_SELECTOR_FIELD: sel.MachineSelector,
        sel.NAMESPACE_SELECTOR_FIELD: sel.NamespaceSelector,
        sel.POD_SELECTOR_FIELD: sel.PodSelector,
    }


SCOPE_TO_RULES = {
    _scp.CONTAINER_SCOPE: ContainerRule,
}


def build_rules(rules: List[Dict], rs_name: str = None) -> List[BaseRule]:
    """
    Builds the rules in the ruleset based on the provided rule data.

    Args:
        rules (list[dict]): The list of rule data.

    Raises:
        ValueError: If the rule scope is not supported by the ruleset.
    """
    rv = []
    for rule_data in rules:
        rule = build_rule(rule_data, rs_name)
        rv.append(rule)
    return rv


def build_rule(rule_data: Dict, rs_name: str = None):
    """Build an individual rule"""
    target: str = rule_data[lib.RULE_TARGET_FIELD]
    scope, _ = target.split("::")
    rule_class = SCOPE_TO_RULES.get(scope)
    if not rule_class:
        lib.err_exit(f'Unsupported rule scope "{scope}" in target "{target}".')
    rule = rule_class(rule_data, rs_name)
    return rule


def new_rule(target: str, verb: str, values: List[str], selectors: Dict = None) -> Dict:
    """Create a new rule"""
    if selectors is None:
        selectors = {}
    return {
        **selectors,
        lib.RULE_TARGET_FIELD: target,
        lib.RULE_VERB_FIELD: verb,
        lib.RULE_VALUES_FIELD: values,
    }
