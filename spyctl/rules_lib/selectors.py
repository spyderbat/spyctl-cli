"""Library that contains the selector logic for policies."""

from __future__ import annotations

import fnmatch
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

import spyctl.rules_lib.scope as _scp

GLOB_CHARS = ["*", "?", "[", "]"]
VALID_PROTOCOLS = {"TCP", "UDP"}
IPV4_SELECTOR = 0
IPV6_SELECTOR = 1
VALID_CONN_SELECTORS = {"ipBlock", "dnsSelector"}
EXPR_KEY = "key"
EXPR_OP = "operator"
EXPR_VALUES = "values"
MATCH_FIELDS = "matchFields"
MATCH_LABELS = "matchLabels"
MATCH_EXPRESSIONS = "matchExpressions"
MATCH_FIELDS_EXPRESSIONS = "matchFieldsExpressions"
CLUSTER_NAME_FIELD = "clusterName"
CLUSTER_UID_FIELD = "clusterUID"
IMAGE_FIELD = "image"
IMAGE_ID_FIELD = "imageID"
CONT_NAME_FIELD = "containerName"
CONT_ID_FIELD = "containerID"

CLUSTER_SELECTOR_FIELD = "clusterSelector"
CONTAINER_SELECTOR_FIELD = "containerSelector"
MACHINE_SELECTOR_FIELD = "machineSelector"
NAMESPACE_SELECTOR_FIELD = "namespaceSelector"
POD_SELECTOR_FIELD = "podSelector"
PROCESS_SELECTOR_FIELD = "processSelector"
SERVICE_SELECTOR_FIELD = "serviceSelector"
TRACE_SELECTOR_FIELD = "traceSelector"
USER_SELECTOR_FIELD = "userSelector"


DEFAULT_MATCH_ITEM = "N/A"


@dataclass
class ScopeMatcher:
    expr_group: Optional[ExpressionGroup]
    match_item: str


class ScopeSelector:
    """
    Represents a selector for evaluating scopes and expressions.

    Attributes:
    - scope_matchers (list[ExpressionGroup]): List of ScopeMatchers that hold
        an ExpressionGroup and a match item. If the expression group is None or
        evaluates to True, the match item is added to the set of match items
        returned by in_scope.

    Methods:
    - add_expression_group(expr_grp, match_item): Adds an expression group to
        the selector along with a corresponding optional match_item
    - in_scope(scope): Returns a set of match items for the matching scopes.
    - in_scope_bool(scope): Checks if the given scope is in the selector's
        scope.
    """

    def __init__(self) -> None:
        self.scope_matchers: list[ScopeMatcher] = []

    def add_expression_group(
        self,
        expr_grp: ExpressionGroup = None,
        match_item: str = DEFAULT_MATCH_ITEM,
        force: bool = False,
    ):
        """
        Adds a scope to the selector. This is an isolated scope such as the
        contents of a namespaceSelector from a single policy. The match
        item is an optional string that can be used to identify the source
        of the match, such as the policy uid.

        Args:
            scope (BaseScope): The scope to be added.
            expressions (list[Expression]): List of expressions to be added.
            match_item (str, optional): The match item to be used.
                Defaults to "N/A".
            force (bool): If True, the expression group will be added even if
                it is none and the match_item is default. Defaults to False.
        """
        if not force and expr_grp is None and match_item == DEFAULT_MATCH_ITEM:
            raise ValueError("Expression group and match item not set")
        self.scope_matchers.append(ScopeMatcher(expr_grp, match_item))

    def remove_match_item(self, match_item: str):
        """
        Removes any scope matchers with the given match item.

        Args:
            match_item (str): The match item to be removed.
        """
        self.scope_matchers = [
            sm for sm in self.scope_matchers if sm.match_item != match_item
        ]

    def in_scope(
        self, scope: _scp.BaseScope | None, valid_match_items: set[str] = None
    ) -> Set[str]:
        """
        Returns a set of strings containing the match items for the matching
        scopes. If match items aren't used the set will contain "N/A".
        If no matches are found the set will be empty.

        Parameters:
        - scope: An instance of _scp.BaseScope representing the scope to
            evaluate the selector against.

        Returns:
        - A set of strings containing the match items for the scopes that
            matched the input.
        """
        rv = set()
        for sm in self.scope_matchers:
            if valid_match_items is not None and sm.match_item not in valid_match_items:
                # No reason to evaluate match_items no longer
                # applicable
                continue
            expr_grp = sm.expr_group
            if scope is None:
                # The object matching with this selector
                # does not have this scope or this scope is not applicable
                if sm.expr_group is None:
                    # The scope is not required so its a match by default
                    rv.add(sm.match_item)
                continue
            if expr_grp is None or expr_grp.evaluate(scope):
                rv.add(sm.match_item)
        return rv

    def in_scope_bool(
        self, scope: _scp.BaseScope | None, valid_match_items: set[str] = None
    ) -> bool:
        """
        Boolean version of in_scope.

        Args:
            scope (BaseScope): The scope to check.

        Returns:
            bool: True if the scope is in the selector's scope,
                False otherwise.
        """

        if len(self.in_scope(scope, valid_match_items)) > 0:
            return True
        return False


class ClusterSelector(ScopeSelector):
    """Scope Selector specific to Clusters."""

    def in_scope(
        self,
        scope: _scp.ClusterScope | None,
        valid_match_items: set[str] = None,
    ) -> Set[str]:
        if scope is not None and not isinstance(scope, _scp.ClusterScope):
            raise ValueError("Scope type mismatch")
        return super().in_scope(scope, valid_match_items)


class MachineSelector(ScopeSelector):
    """Scope Selector specific to Machines."""

    def in_scope(
        self,
        scope: _scp.MachineScope | None,
        valid_match_items: set[str] = None,
    ) -> Set[str]:
        if scope is not None and not isinstance(scope, _scp.MachineScope):
            raise ValueError("Scope type mismatch")
        return super().in_scope(scope, valid_match_items)


class ContainerSelector(ScopeSelector):
    """Scope Selector specific to Containers."""

    def in_scope(
        self,
        scope: _scp.ContainerScope | None,
        valid_match_items: set[str] = None,
    ) -> Set[str]:
        if scope is not None and not isinstance(scope, _scp.ContainerScope):
            raise ValueError("Scope type mismatch")
        return super().in_scope(scope, valid_match_items)


class NamespaceSelector(ScopeSelector):
    """Scope Selector specific to Namespaces."""

    def in_scope(
        self,
        scope: _scp.NamespaceScope | None,
        valid_match_items: set[str] = None,
    ) -> Set[str]:
        if scope is not None and not isinstance(scope, _scp.NamespaceScope):
            raise ValueError("Scope type mismatch")
        return super().in_scope(scope, valid_match_items)


class PodSelector(ScopeSelector):
    """Scope Selector specific to Pods."""

    def in_scope(
        self, scope: _scp.PodScope | None, valid_match_items: set[str] = None
    ) -> Set[str]:
        if scope is not None and not isinstance(scope, _scp.PodScope):
            raise ValueError("Scope type mismatch")
        return super().in_scope(scope, valid_match_items)


class ServiceSelector(ScopeSelector):
    """Scope Selector specific to Services."""

    def in_scope(
        self,
        scope: _scp.LinuxServiceScope | None,
        valid_match_items: set[str] = None,
    ) -> Set[str]:
        if scope is not None and not isinstance(scope, _scp.LinuxServiceScope):
            raise ValueError("Scope type mismatch")
        return super().in_scope(scope, valid_match_items)


class ProcessSelector(ScopeSelector):
    """Scope Selector specific to Processes."""

    def in_scope(
        self,
        scope: _scp.ProcessScope | None,
        valid_match_items: set[str] = None,
    ) -> Set[str]:
        if scope is not None and not isinstance(scope, _scp.ProcessScope):
            raise ValueError("Scope type mismatch")
        return super().in_scope(scope, valid_match_items)


class TraceSelector(ScopeSelector):
    """Scope Selector specific to Traces."""

    def in_scope(
        self, scope: _scp.TraceScope | None, valid_match_items: set[str] = None
    ) -> Set[str]:
        if scope is not None and not isinstance(scope, _scp.TraceScope):
            raise ValueError("Scope type mismatch")
        return super().in_scope(scope, valid_match_items)


class UserSelector(ScopeSelector):
    """Scope Selector specific to Users."""

    def in_scope(
        self, scope: _scp.UserScope | None, valid_match_items: set[str] = None
    ) -> Set[str]:
        if scope is not None and not isinstance(scope, _scp.UserScope):
            raise ValueError("Scope type mismatch")
        return super().in_scope(scope, valid_match_items)


# ----------------------------------------------------------------- #
#                             Expressions                           #
# ----------------------------------------------------------------- #

OP_IN = "In"
OP_NOT_IN = "NotIn"
OP_EXISTS = "Exists"
OP_DOES_NOT_EXIST = "DoesNotExist"
VALID_OPERATORS = [OP_IN, OP_NOT_IN, OP_EXISTS, OP_DOES_NOT_EXIST]


class Expression:
    """A class representing a selector expression."""

    def __init__(self, key, operator, values: list[str] = None):
        if operator not in VALID_OPERATORS:
            raise ValueError(f"Invalid operator: {operator}")
        self.key: str = key
        self.operator: str = operator
        self.values = StringSelectorGroup(key)
        self._values: list[str] = []
        if values:
            for value in values:
                self.add_value(value)

    def add_value(self, value: str):
        """
        Adds a value to the selector.

        Parameters:
        - value (str): The value to be added.
        - match_item (str): The match item to be associated with the value.
            Default is "N/A".

        Returns:
        None
        """
        self.values.add_selector(StringSelector(self.key, value))
        self._values.append(value)

    def get_values(self) -> list[str]:
        """
        Returns a set of the string values in the expression.

        Returns:
        set[str]: A set of strings representing the values in the expression.
        """
        return self._values

    def evaluate(self, scope: _scp.BaseScope | dict) -> bool:
        """
        Evaluates the expression against the given scope.

        Args:
            scope (BaseScope | dict): The scope to evaluate the expression
                against.

        Returns:
            bool: True if the expression evaluates to True, False otherwise.
        """
        if isinstance(scope, dict):
            return self.__dict_evaluate(scope)
        return self.__scope_evaluate(scope)

    def __scope_evaluate(self, scope: _scp.BaseScope) -> bool:
        if self.operator == OP_EXISTS:
            return hasattr(scope, self.key) and getattr(scope, self.key) is not None
        if self.operator == OP_DOES_NOT_EXIST:
            return not hasattr(scope, self.key) or getattr(scope, self.key) is None
        if self.operator == OP_IN:
            if not hasattr(scope, self.key):
                return False
            return self.values.bool_match(self.key, getattr(scope, self.key))
        if self.operator == OP_NOT_IN:
            if not hasattr(scope, self.key) or getattr(scope, self.key) is None:
                return True
            return not self.values.bool_match(self.key, getattr(scope, self.key))
        raise ValueError(f"Invalid operator: {self.operator}")

    def __dict_evaluate(self, scope_dict: dict) -> bool:
        if self.operator == OP_EXISTS:
            return self.key in scope_dict
        if self.operator == OP_DOES_NOT_EXIST:
            return self.key not in scope_dict
        if self.operator == OP_IN:
            if self.key not in scope_dict:
                return False
            return self.values.bool_match(self.key, scope_dict[self.key])
        if self.operator == OP_NOT_IN:
            if self.key not in scope_dict:
                return True
            return not self.values.bool_match(self.key, scope_dict[self.key])
        raise ValueError(f"Invalid operator: {self.operator}")


class ExpressionGroup:
    def __init__(self, key=None) -> None:
        self.key = key
        self.expressions: dict[str, list[Expression | ExpressionGroup]] = defaultdict(
            list
        )

    def add_expression(self, expression: Expression | ExpressionGroup):
        if not expression.key:
            raise ValueError("Expression key not set")
        self.expressions[expression.key].append(expression)

    def evaluate(self, scope: _scp.BaseScope | dict) -> bool:
        result = False
        # Every expression in the group must evaluate to
        # True for the group to evaluate to True
        for key in self.expressions:
            result = self.__evaluate_key(key, scope)
            if not result:
                return False
        return result

    def __evaluate_key(self, key: str, scope: _scp.BaseScope | dict) -> set[str]:
        """Every expression for a given key must match.
        We combine the match items across expressions for use later.
        """
        result = False
        exprs = self.expressions[key]
        for expr in exprs:
            if isinstance(expr, ExpressionGroup):
                if isinstance(scope, dict):
                    result = expr.evaluate(scope.get(key, {}))
                else:
                    result = expr.evaluate(getattr(scope, key, {}))
            else:
                result = expr.evaluate(scope)
            if not result:
                return False
        return result


# ----------------------------------------------------------------- #
#                           Selector Groups                         #
# ----------------------------------------------------------------- #


# -------------------------------------------------------------
class StringSelectorGroup:
    def __init__(self, key: str) -> None:
        self.key = key
        self.kw_map: Dict[str, Set] = defaultdict(set)
        self.selectors: List[Tuple[StringSelector, Any]] = []

    def add_selector(
        self, selector: StringSelector, match_item="N/A", ignore_key=False
    ):
        if not ignore_key and selector.key != self.key:
            return
        if selector.glob_evaluator is None:
            self.kw_map[selector.value].add(match_item)
        else:
            self.selectors.append((selector, match_item))

    def match(self, key: str, value: str, ignore_key=False) -> Set:
        rv = set()
        if not ignore_key and self.key != key:
            return rv
        if value in self.kw_map:
            rv.update(self.kw_map[value])
        for selector, match_item in self.selectors:
            if selector.match(value):
                rv.add(match_item)
        return rv

    def bool_match(self, key: str, value: str) -> bool:
        if len(self.match(key, value)) > 0:
            return True
        return False


# ----------------------------------------------------------------- #
#                         Selector Primitives                       #
# ----------------------------------------------------------------- #


# -------------------------------------------------------------
class StringSelector:
    def __init__(self, key, value) -> None:
        self.key = key
        self.value = value
        # Exact string match to be evaluated before
        # calling fnmatch
        self.glob_evaluator = None
        self.glob_evaluator_len = None
        if isinstance(value, str):
            if contains_glob_chars(value):
                count = 0
                for char in value:
                    if char in GLOB_CHARS:
                        break
                    count += 1
                self.glob_evaluator = value[:count]
                self.glob_evaluator_len = len(self.glob_evaluator)

    def match(self, value: str) -> bool:
        if self.glob_evaluator is None:
            return self.value == value
        # substring matches are faster so do a quick
        # substring match to see if we even need to do an fnmatch
        if self.glob_evaluator == value[: self.glob_evaluator_len]:
            return fnmatch.fnmatch(value, self.value)
        return False


# ----------------------------------------------------------------- #
#                           Helper Functions                        #
# ----------------------------------------------------------------- #


# -------------------------------------------------------------
def contains_glob_chars(value: str) -> bool:
    for char in GLOB_CHARS:
        if char in value:
            return True
    return False
