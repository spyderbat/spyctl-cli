"""Contains the logic specific to guardian policy rulesets."""

from typing import Dict, List

import spyctl.rules_lib.rule as _r
import spyctl.rules_lib.scope as _scp
import spyctl.spyctl_lib as lib


class BaseRuleset:
    """
    Represents a base ruleset.

    Attributes:
        uid (str): The unique identifier of the ruleset.
        org_uid (str): The unique identifier of the organization.
        name (str): The name of the ruleset.
        type: The type of the ruleset.
        rules (list[_r.BaseRule]): The list of rules in the ruleset.
    """

    supported_rule_types = {}

    def __init__(
        self, uid: str, org_uid: str, name: str, ruleset_type
    ) -> None:
        self.uid = uid
        self.org_uid = org_uid
        self.name = name
        self.type = ruleset_type
        self.rules: list[_r.BaseRule] = []

    def build_rules(self, rules: List[Dict]) -> None:
        """
        Builds the rules in the ruleset based on the provided rule data.

        Args:
            rules (list[dict]): The list of rule data.

        Raises:
            ValueError: If the rule scope is not supported by the ruleset.
        """
        for rule_data in rules:
            target = rule_data.get(_r.TARGET_FIELD)
            scope, _ = self.__parse_target(target)
            if scope not in self.supported_rule_types:
                raise ValueError(f"{self} does not support '{scope}' rules.")
            rule_class = self.supported_rule_types[scope]
            rule = rule_class(rule_data)
            self.rules.append(rule)

    def __parse_target(self, target: str) -> str:
        """
        Parses the target string into scope and attribute.

        Args:
            target (str): The target string.

        Returns:
            str: The scope and attribute separated by '::'.
        """
        scope, attribute = target.split("::")
        return scope, attribute

    def __str__(self) -> str:
        """
        Returns a string representation of the ruleset.

        Returns:
            str: The string representation of the ruleset.
        """
        return "BaseRuleset"


class ClusterRuleset(BaseRuleset):
    """Maintains the supported rule types for cluster rulesets."""

    supported_rule_types = {
        _scp.CONTAINER_SCOPE: _r.ContainerRule,
    }

    def __init__(self, uid: str, org_uid: str, name: str) -> None:
        super().__init__(uid, org_uid, name, lib.RULESET_TYPE_CLUS)

    def __str__(self) -> str:
        return "ClusterRuleset"
