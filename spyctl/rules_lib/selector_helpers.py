"""
Library that contains helper functions for building selectors and expression
group objects.
"""

from typing import Dict, List

import spyctl.rules_lib.scope as _scp
import spyctl.rules_lib.selectors as sel


# -------------------------------------------------------------
def exprs_from_spec(spec: dict) -> Dict[str, sel.ExpressionGroup]:
    """Builds a dictionary of expression groups from a policy spec
    or other dictionary that uses selectors such as response actions.

    Args:
        spec (dict): The dictionary with selectors.

    Returns:
        dict[str, ExpressionGroup]: The dictionary of selector field to
            expression group.
    """
    rv = {}
    for field_name, func in SEL_FIELD_TO_HELPER.items():
        if field_name in spec:
            rv[field_name] = func(spec[field_name])
    return rv


# -------------------------------------------------------------
def exprs_from_ns_sel_dict(
    ns_sel_dict: dict,
) -> sel.ExpressionGroup:
    """Builds a list of expressions from a namespace selector
    dictionary.

    Args:
        ns_sel_dict (dict): The namespace selector dictionary.

    Returns:
        ExpressionGroup: Group of expressions for a single selector.
    """
    rv = sel.ExpressionGroup()
    labels_expr_grp = sel.ExpressionGroup(_scp.LABELS_ATTR)
    if sel.MATCH_LABELS in ns_sel_dict:
        for expr in exprs_from_labels(ns_sel_dict[sel.MATCH_LABELS]):
            labels_expr_grp.add_expression(expr)
    if sel.MATCH_EXPRESSIONS in ns_sel_dict:
        for expr in __build_expressions_from_dicts(
            ns_sel_dict[sel.MATCH_EXPRESSIONS]
        ):
            labels_expr_grp.add_expression(expr)
    if labels_expr_grp.expressions:
        rv.add_expression(labels_expr_grp)
    return rv


# -------------------------------------------------------------
def exprs_from_pod_sel_dict(
    pod_sel_dict: dict,
) -> sel.ExpressionGroup:
    """Builds a list of expressions from a pod selector dictionary.

    Args:
        pod_sel_dict (dict): The pod selector dictionary.

    Returns:
        ExpressionGroup: Group of expressions for a single selector.
    """
    rv = sel.ExpressionGroup()
    labels_expr_grp = sel.ExpressionGroup(_scp.LABELS_ATTR)
    if sel.MATCH_LABELS in pod_sel_dict:
        for expr in exprs_from_labels(pod_sel_dict[sel.MATCH_LABELS]):
            labels_expr_grp.add_expression(expr)
    if sel.MATCH_EXPRESSIONS in pod_sel_dict:
        for expr in __build_expressions_from_dicts(
            pod_sel_dict[sel.MATCH_EXPRESSIONS]
        ):
            labels_expr_grp.add_expression(expr)
    if labels_expr_grp.expressions:
        rv.add_expression(labels_expr_grp)
    return rv


# -------------------------------------------------------------
def exprs_from_clus_sel_dict(
    clus_sel_dict: dict,
) -> sel.ExpressionGroup:
    """Builds a list of expressions from a cluster selector dictionary.

    Args:
        clus_sel_dict (dict): The cluster selector dictionary.

    Returns:
        ExpressionGroup: Group of expressions for a single selector.
    """
    rv = sel.ExpressionGroup()
    fields = clus_sel_dict.get(sel.MATCH_FIELDS, {})
    if fields:
        for yaml_key, value in fields.items():
            key = _scp.clus_yaml_to_attr(yaml_key)
            rv.add_expression(sel.Expression(key, sel.OP_IN, [value]))
    if sel.MATCH_FIELDS_EXPRESSIONS in clus_sel_dict:
        for expr in __build_fields_expressions_from_dicts(
            clus_sel_dict[sel.MATCH_FIELDS_EXPRESSIONS], _scp.clus_yaml_to_attr
        ):
            rv.add_expression(expr)
    return rv


# -------------------------------------------------------------
def exprs_from_mach_sel_dict(
    mach_sel_dict: dict,
) -> sel.ExpressionGroup:
    """Builds a list of expressions from a machine selector dictionary.

    Args:
        mach_sel_dict (dict): The machine selector dictionary.

    Returns:
        ExpressionGroup: Group of expressions for a single selector.
    """
    rv = sel.ExpressionGroup()
    fields = mach_sel_dict.get(sel.MATCH_FIELDS, {})
    if fields:
        for yaml_key, value in fields.items():
            key = _scp.mach_yaml_to_attr(yaml_key)
            rv.add_expression(sel.Expression(key, sel.OP_IN, [value]))
    if sel.MATCH_FIELDS_EXPRESSIONS in mach_sel_dict:
        for expr in __build_fields_expressions_from_dicts(
            mach_sel_dict[sel.MATCH_FIELDS_EXPRESSIONS], _scp.mach_yaml_to_attr
        ):
            rv.add_expression(expr)
    # Support for old format
    for expr in __support_old_mach_selector_format(mach_sel_dict):
        rv.add_expression(expr)
    return rv


# -------------------------------------------------------------
def exprs_from_cont_sel_dict(
    cont_sel_dict: dict,
) -> sel.ExpressionGroup:
    """Builds a list of expressions from a container selector dictionary.

    Args:
        cont_sel_dict (dict): The container selector dictionary.

    Returns:
        ExpressionGroup: Group of expressions for a single selector.
    """
    rv = sel.ExpressionGroup()
    fields = cont_sel_dict.get(sel.MATCH_FIELDS, {})
    if fields:
        for yaml_key, value in fields.items():
            key = _scp.cont_yaml_to_attr(yaml_key)
            rv.add_expression(sel.Expression(key, sel.OP_IN, [value]))
    if sel.MATCH_FIELDS_EXPRESSIONS in cont_sel_dict:
        for expr in __build_fields_expressions_from_dicts(
            cont_sel_dict[sel.MATCH_FIELDS_EXPRESSIONS], _scp.cont_yaml_to_attr
        ):
            rv.add_expression(expr)
    # Support for old format
    for expr in __support_old_cont_selector_format(cont_sel_dict):
        rv.add_expression(expr)
    return rv


# -------------------------------------------------------------
def exprs_from_l_svc_sel_dict(
    l_svc_sel_dict: dict,
) -> sel.ExpressionGroup:
    """Builds a list of expressions from a linux service selector dictionary.

    Args:
        l_svc_sel_dict (dict): The load balancer service selector dictionary.

    Returns:
        ExpressionGroup: Group of expressions for a single selector.
    """
    rv = sel.ExpressionGroup()
    fields = l_svc_sel_dict.get(sel.MATCH_FIELDS, {})
    if fields:
        for yaml_key, value in fields.items():
            key = _scp.linux_svc_yaml_to_attr(yaml_key)
            rv.add_expression(sel.Expression(key, sel.OP_IN, [value]))
    if sel.MATCH_FIELDS_EXPRESSIONS in l_svc_sel_dict:
        for expr in __build_fields_expressions_from_dicts(
            l_svc_sel_dict[sel.MATCH_FIELDS_EXPRESSIONS],
            _scp.linux_svc_yaml_to_attr,
        ):
            rv.add_expression(expr)
    # Support for old format
    for expr in __support_old_l_svc_selector_format(l_svc_sel_dict):
        rv.add_expression(expr)
    return rv


# -------------------------------------------------------------
def exprs_from_proc_sel_dict(
    proc_sel_dict: dict,
) -> sel.ExpressionGroup:
    """Builds a list of expressions from a process selector dictionary.

    Args:
        proc_sel_dict (dict): The process selector dictionary.

    Returns:
        ExpressionGroup: Group of expressions for a single selector.
    """
    rv = sel.ExpressionGroup()
    fields = proc_sel_dict.get(sel.MATCH_FIELDS, {})
    if fields:
        for yaml_key, value in fields.items():
            key = _scp.proc_yaml_to_attr(yaml_key)
            rv.add_expression(sel.Expression(key, sel.OP_IN, [value]))
    if sel.MATCH_FIELDS_EXPRESSIONS in proc_sel_dict:
        for expr in __build_fields_expressions_from_dicts(
            proc_sel_dict[sel.MATCH_FIELDS_EXPRESSIONS],
            _scp.proc_yaml_to_attr,
        ):
            rv.add_expression(expr)
    # Support for old format
    for expr in __support_old_proc_selector_format(proc_sel_dict):
        rv.add_expression(expr)
    return rv


# -------------------------------------------------------------
def exprs_from_trace_sel_dict(
    trace_sel_dict: dict,
) -> sel.ExpressionGroup:
    """Builds a list of expressions from a trace selector dictionary.

    Args:
        trace_sel_dict (dict): The trace selector dictionary.

    Returns:
        ExpressionGroup: Group of expressions for a single selector.
    """
    rv = sel.ExpressionGroup()
    fields = trace_sel_dict.get(sel.MATCH_FIELDS, {})
    if fields:
        for yaml_key, value in fields.items():
            key = _scp.trace_yaml_to_attr(yaml_key)
            rv.add_expression(sel.Expression(key, sel.OP_IN, [value]))
    if sel.MATCH_FIELDS_EXPRESSIONS in trace_sel_dict:
        for expr in __build_fields_expressions_from_dicts(
            trace_sel_dict[sel.MATCH_FIELDS_EXPRESSIONS],
            _scp.trace_yaml_to_attr,
        ):
            rv.add_expression(expr)
    # Support for old format
    for expr in __support_old_trace_selector_format(trace_sel_dict):
        rv.add_expression(expr)
    return rv


# -------------------------------------------------------------
def exprs_from_user_sel_dict(
    user_sel_dict: dict,
) -> sel.ExpressionGroup:
    """Builds a list of expressions from a user selector dictionary.

    Args:
        user_sel_dict (dict): The user selector dictionary.

    Returns:
        ExpressionGroup: Group of expressions for a single selector.
    """
    rv = sel.ExpressionGroup()
    fields = user_sel_dict.get(sel.MATCH_FIELDS, {})
    if fields:
        for yaml_key, value in fields.items():
            key = _scp.user_yaml_to_attr(yaml_key)
            rv.add_expression(sel.Expression(key, sel.OP_IN, [value]))
    if sel.MATCH_FIELDS_EXPRESSIONS in user_sel_dict:
        for expr in __build_fields_expressions_from_dicts(
            user_sel_dict[sel.MATCH_FIELDS_EXPRESSIONS],
            _scp.user_yaml_to_attr,
        ):
            rv.add_expression(expr)
    # Support for old format
    for expr in __support_old_user_selector_format(user_sel_dict):
        rv.add_expression(expr)
    return rv


# -------------------------------------------------------------
def exprs_from_labels(labels: dict) -> List[sel.Expression]:
    """Builds an expression group from a labels dictionary.

    Args:
        labels (dict): The labels dictionary.

    Returns:
        ExpressionGroup: The ExpressionGroup object.
    """
    rv = []
    for key, value in labels.items():
        rv.append(sel.Expression(key, sel.OP_IN, [value]))
    return rv


# -------------------------------------------------------------

SEL_FIELD_TO_HELPER = {
    sel.CLUSTER_SELECTOR_FIELD: exprs_from_clus_sel_dict,
    sel.CONTAINER_SELECTOR_FIELD: exprs_from_cont_sel_dict,
    sel.MACHINE_SELECTOR_FIELD: exprs_from_mach_sel_dict,
    sel.NAMESPACE_SELECTOR_FIELD: exprs_from_ns_sel_dict,
    sel.POD_SELECTOR_FIELD: exprs_from_pod_sel_dict,
    sel.PROCESS_SELECTOR_FIELD: exprs_from_proc_sel_dict,
    sel.SERVICE_SELECTOR_FIELD: exprs_from_l_svc_sel_dict,
    sel.TRACE_SELECTOR_FIELD: exprs_from_trace_sel_dict,
    sel.USER_SELECTOR_FIELD: exprs_from_user_sel_dict,
}


# -------------------------------------------------------------
def __build_expressions_from_dicts(
    expr_dicts: List[Dict],
) -> List[sel.Expression]:
    """Builds a list of Expression objects from a list of expression
    dictionaries.

    Args:
        expr_dicts (list[dict]): The list of expression dictionaries.

    Returns:
        list[sel.Expression]: The list of Expression objects.
    """
    expressions = []
    for expr_dict in expr_dicts:
        key = expr_dict[sel.EXPR_KEY]
        operator = expr_dict[sel.EXPR_OP]
        values = expr_dict.get(sel.EXPR_VALUES)
        expressions.append(sel.Expression(key, operator, values))
    return expressions


# -------------------------------------------------------------
def __build_fields_expressions_from_dicts(
    expr_dicts: List[Dict], yaml_converter: callable
) -> List[sel.Expression]:
    """Builds a list of Expression objects from a list of expression
    dictionaries.

    Args:
        expr_dicts (list[dict]): The list of expression dictionaries.

    Returns:
        list[sel.Expression]: The list of Expression objects.
    """
    expressions = []
    for expr_dict in expr_dicts:
        yaml_key = expr_dict[sel.EXPR_KEY]
        key = yaml_converter(yaml_key)
        operator = expr_dict[sel.EXPR_OP]
        values = expr_dict.get(sel.EXPR_VALUES)
        expressions.append(sel.Expression(key, operator, values))
    return expressions


def __support_old_mach_selector_format(
    mach_sel_dict: dict,
) -> List[sel.Expression]:
    """Support for old machine selector format.

    Args:
        mach_sel_dict (dict): The machine selector dictionary.

    Returns:
        list[sel.Expression]: The list of Expression objects.
    """
    expressions = []
    for yaml_key in _scp.MACH_YAML_TO_ATTR:
        key = _scp.mach_yaml_to_attr(yaml_key)
        if yaml_key in mach_sel_dict:
            expressions.append(
                sel.Expression(key, sel.OP_IN, [mach_sel_dict[yaml_key]])
            )
    return expressions


# -------------------------------------------------------------
def __support_old_cont_selector_format(
    cont_sel_dict: dict,
) -> List[sel.Expression]:
    """Support for old container selector format.

    Args:
        cont_sel_dict (dict): The container selector dictionary.

    Returns:
        list[sel.Expression]: The list of Expression objects.
    """
    expressions = []
    for yaml_key in _scp.CONT_YAML_TO_ATTR:
        key = _scp.cont_yaml_to_attr(yaml_key)
        if yaml_key in cont_sel_dict:
            expressions.append(
                sel.Expression(key, sel.OP_IN, [cont_sel_dict[yaml_key]])
            )
    return expressions


# -------------------------------------------------------------
def __support_old_l_svc_selector_format(
    l_svc_sel_dict: dict,
) -> List[sel.Expression]:
    """Support for old linux service selector format.

    Args:
        l_svc_sel_dict (dict): The linux service selector dictionary.

    Returns:
        list[sel.Expression]: The list of Expression objects.
    """
    expressions = []
    for yaml_key in _scp.LINUX_SVC_YAML_TO_ATTR:
        key = _scp.linux_svc_yaml_to_attr(yaml_key)
        if yaml_key in l_svc_sel_dict:
            expressions.append(
                sel.Expression(key, sel.OP_IN, [l_svc_sel_dict[yaml_key]])
            )
    return expressions


# -------------------------------------------------------------
def __support_old_proc_selector_format(
    proc_sel_dict: dict,
) -> List[sel.Expression]:
    """Support for old process selector format.

    Args:
        proc_sel_dict (dict): The process selector dictionary.

    Returns:
        list[sel.Expression]: The list of Expression objects.
    """
    expressions = []
    for yaml_key in _scp.PROC_YAML_TO_ATTR:
        key = _scp.proc_yaml_to_attr(yaml_key)
        if yaml_key in proc_sel_dict:
            v = proc_sel_dict[yaml_key]
            if isinstance(v, list):
                values = v
            else:
                values = [str(v)]
            expressions.append(sel.Expression(key, sel.OP_IN, values))
    return expressions


# -------------------------------------------------------------
def __support_old_trace_selector_format(
    trace_sel_dict: dict,
) -> List[sel.Expression]:
    """Support for old trace selector format.

    Args:
        trace_sel_dict (dict): The trace selector dictionary.

    Returns:
        list[sel.Expression]: The list of Expression objects.
    """
    expressions = []
    for yaml_key in _scp.TRACE_YAML_TO_ATTR:
        key = _scp.trace_yaml_to_attr(yaml_key)
        if yaml_key in trace_sel_dict:
            v = trace_sel_dict[yaml_key]
            if isinstance(v, list):
                values = v
            else:
                values = [str(v)]
            expressions.append(sel.Expression(key, sel.OP_IN, values))
    return expressions


# -------------------------------------------------------------
def __support_old_user_selector_format(
    user_sel_dict: dict,
) -> List[sel.Expression]:
    """Support for old user selector format.

    Args:
        user_sel_dict (dict): The user selector dictionary.

    Returns:
        list[sel.Expression]: The list of Expression objects.
    """
    expressions = []
    for yaml_key in _scp.USER_YAML_TO_ATTR:
        key = _scp.user_yaml_to_attr(yaml_key)
        if yaml_key in user_sel_dict:
            v = user_sel_dict[yaml_key]
            if isinstance(v, list):
                values = v
            else:
                values = [str(v)]
            expressions.append(sel.Expression(key, sel.OP_IN, values))
    return expressions
