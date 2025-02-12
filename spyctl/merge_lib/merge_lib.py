"""Contains the logic for diffing and merging resources"""

# pylint: disable=global-statement, too-many-lines
# pylint: disable=broad-exception-caught, comparison-with-callable
# pylint: disable=broad-exception-raised

from __future__ import annotations

import fnmatch
import itertools
from difflib import SequenceMatcher
from typing import TYPE_CHECKING, Any, Dict, List, Union

import spyctl.spyctl_lib as lib
from spyctl import cli

if TYPE_CHECKING:
    from spyctl.merge_lib.merge_object import MergeObject

NODE_TYPE_EGRESS = "egress"
NODE_TYPE_INGRESS = "ingress"

BASE_NODE_LIST = None
MERGING_NODE_LIST = None

ADD_START = "+ "
SUB_START = "- "
LIST_MARKER = "- "
DEFAULT_WHITESPACE = "  "
NET_POL_FIELDS = {lib.INGRESS_FIELD, lib.EGRESS_FIELD}
OR_FIELDS = {lib.TO_FIELD, lib.FROM_FIELD}


class InvalidMergeError(Exception):
    pass


class InvalidDiffError(Exception):
    pass


def common_keys_merge(
    _mo: MergeObject, base_data: Dict, other_data: Dict, _symmetric: bool
):
    result = {}
    if base_data is None:
        base_data = {}
    if other_data is None:
        other_data = {}
    common_keys = set(base_data).intersection(set(other_data))
    for key, value in base_data.items():
        if key not in common_keys:
            continue
        if value == other_data.get(key):
            result[key] = value
    if len(result) > 0:
        return result
    return None


def wildcard_merge(_mo: MergeObject, base_str: str, other_str: str, symmetric: bool):
    "Result of the merge can be wildcarded"
    if symmetric:
        if base_str and other_str:
            if fnmatch.fnmatch(other_str, base_str):
                result = base_str
            elif fnmatch.fnmatch(base_str, other_str):
                result = other_str
            else:
                result = make_wildcard([base_str, other_str])
        else:
            result = None
    else:
        if base_str:
            if other_str and fnmatch.fnmatch(other_str, base_str):
                result = base_str
            else:
                result = None
        else:
            result = None
    return result


def all_eq_merge(_mo: MergeObject, base_str: str, other_str: str, _):
    if base_str == other_str:
        result = base_str
    else:
        result = None
    return result


def keep_base_value_merge(_mo: MergeObject, base_val: Any, _other_val: Any, _):
    return base_val


def greatest_value_merge(_mo: MergeObject, base_val, other_val, _symmetric: bool):
    if base_val is not None and other_val is None:
        result = base_val
    elif base_val is None and other_val is not None:
        result = other_val
    elif base_val is None and other_val is None:
        result = None
    elif base_val > other_val:
        result = base_val
    else:
        result = other_val
    return result


def string_list_merge(
    _mo: MergeObject,
    base_value: Union[str, List[str]],
    other_value: Union[str, List[str]],
    _,
):
    if isinstance(base_value, str):
        base_value = [base_value]
    if isinstance(other_value, str):
        other_value = [other_value]
    string_set = set(base_value).union(set(other_value))
    return sorted(string_set)


def expression_list_merge(
    _mo: MergeObject, base_value: List[Dict], other_value: List[Dict], _
):
    rv_dict = {}
    for expr in itertools.chain(base_value, other_value):
        key = (expr[lib.KEY_FIELD], expr[lib.OPERATOR_FIELD])
        if key not in rv_dict:
            rv_dict[key] = expr
        else:
            existing_values: List[str] = rv_dict[key].get(lib.VALUES_FIELD)
            new_values: List[str] = expr.get(lib.VALUES_FIELD)
            if existing_values is not None and new_values is not None:
                existing_values.extend(new_values)
                existing_values = list(set(existing_values))
                rv_dict[key][lib.VALUES_FIELD] = existing_values
    rv = list(rv_dict.values())
    rv.sort(key=lambda x: (x[lib.KEY_FIELD], x[lib.OPERATOR_FIELD]))
    return rv


def conditional_string_list_merge(
    mo: MergeObject,
    base_value: Union[str, List[str]],
    other_value: Union[str, List[str]],
    symmetric: bool,
):
    if isinstance(base_value, str) and isinstance(other_value, str):
        return wildcard_merge(mo, base_value, other_value, symmetric)
    else:
        return string_list_merge(mo, base_value, other_value, symmetric)


def unique_dict_list_merge(
    _mo: MergeObject, base_value: List[Dict], other_value: List[dict], _
):
    rv = base_value.copy()
    for item in other_value:
        if item in base_value:
            continue
        rv.append(item)
    return rv


def make_wildcard(strs: List[str]):
    if len(strs) == 1:
        return strs[0]
    cmp_str = strs[0]
    if len(set(strs)) == 1:
        return cmp_str
    # Simple string match didn't work so lets see if there is a
    # better match (takes more computation)
    original_str = sub_str = strs[0]
    first_char = original_str[0]
    last_char = original_str[-1]
    for name in strs[1:]:
        if first_char != name[0]:
            first_char = None
        if last_char != name[-1]:
            last_char = None
        name = name.strip("*")
        match = SequenceMatcher(None, sub_str, name).find_longest_match(
            0, len(sub_str), 0, len(name)
        )
        match_si = match.a
        match_ei = match.a + match.size
        sub_str = sub_str[match_si:match_ei]
        if len(sub_str) < 3:
            break
    if len(sub_str) < 3:
        ret = None
    elif not (match.b == 0 and original_str.startswith(sub_str)) and not (
        match.b + match.size == len(name) and original_str.endswith(sub_str)
    ):
        ret = "*" + sub_str + "*"
    elif not (match.b == 0 and original_str.startswith(sub_str)):
        ret = "*" + sub_str
    elif not (match.b + match.size == len(name) and original_str.endswith(sub_str)):
        ret = sub_str + "*"
    else:
        cli.err_exit(f"Bug detected in wildcard logic. Input:" f" '{strs}'.")
    return ret
