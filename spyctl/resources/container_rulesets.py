"""
Contains the logic for creating container rulesets from athena results
"""

import json
from typing import Dict, List, Optional

import spyctl.schemas_v2 as schemas
import spyctl.spyctl_lib as lib
from spyctl.resources.container_policies import (ContainerMappings, ProcModel,
                                                 build_container_mappings,
                                                 build_proc_models,
                                                 build_selectors)


def create_container_rulesets(
    procs: List[Dict],
    conns: List[Dict],
    conts: List[Dict],
    settings: Dict,
    **kwargs,
) -> List[Dict]:
    """
    Create container policies based on the provided process, connection,
    and container data.

    Args:
        procs (List[Dict]): A list of dictionaries representing process data.
        _conns (List[Dict]): A list of dictionaries representing connection
            data.
        conts (List[Dict]): A list of dictionaries representing container data.

    Returns:
        List[Dict]: A list of dictionaries representing the created container
            policies.
    """
    procs.sort(key=lambda x: x["pid"])  # sort for improved id generation
    cont_map = build_container_mappings(conts)
    build_proc_models(cont_map, procs)
    # build_conn_models(cont_map, conns)
    rulesets = assemble_rulesets(cont_map, settings, **kwargs)
    return rulesets


def assemble_rulesets(cont_map: ContainerMappings, settings: Dict, **kwargs):
    """
    Assemble the container rulesets from the provided container mappings.

    Args:
        cont_map (ContainerMappings): The container mappings.

    Returns:
        List[Dict]: A list of dictionaries representing the container rulesets.
    """
    rulesets = []
    if settings.get("include_selectors"):
        selectors = build_selectors("placeholder", **kwargs)
    else:
        selectors = {}
    for image_pat, pol_inp in cont_map.image_pat_to_pol_inputs.items():
        set_container_selector(selectors, image_pat)
        rules = []
        keys = set()
        for proc_model in pol_inp.proc_keys.values():
            key = (
                proc_model.base_model.name,
                tuple(proc_model.base_model.exe),
                tuple(proc_model.base_model.euser),
            )
            if key in keys:
                continue
            keys.add(key)
            rules.append(
                schemas.ProcessRule(
                    **selectors,
                    verb=lib.RULE_VERB_ALLOW,
                    target="process::name",
                    values=[proc_model.base_model.name],
                    processSelector=schemas.ProcessSelectorModel(
                        matchFields=__process_fields(proc_model),
                        matchFieldsExpressions=__process_fields_expressions(proc_model),
                    ),
                )
            )
        rulesets.append(
            json.loads(
                schemas.RulesetModel(
                    apiVersion=lib.API_VERSION,
                    kind=lib.RULESET_KIND,
                    metadata=schemas.RulesetMetadataModel(
                        name=f"container-ruleset-{image_pat}",
                        type=lib.RULESET_TYPE_CONT,
                    ),
                    spec=schemas.RulesetPolicySpecModel(
                        rules=rules,
                    ),
                ).model_dump_json(by_alias=True, exclude_none=True)
            )
        )
    return rulesets


def __process_fields(proc_model: ProcModel) -> Optional[Dict]:
    rv = {}
    if len(proc_model.base_model.exe) == 1:
        rv["exe"] = proc_model.base_model.exe[0]
    if len(proc_model.base_model.euser) == 1:
        rv["euser"] = proc_model.base_model.euser[0]
    if not rv:
        return None
    return rv


def __process_fields_expressions(
    proc_model: ProcModel,
) -> Optional[List[schemas.SelectorExpression]]:
    rv = []
    if len(proc_model.base_model.exe) > 1:
        rv.append(
            schemas.SelectorExpression(
                key="exe",
                operator=lib.IN_OPERATOR,
                values=proc_model.base_model.exe,
            )
        )
    if len(proc_model.base_model.euser) > 1:
        rv.append(
            schemas.SelectorExpression(
                key="euser",
                operator=lib.IN_OPERATOR,
                values=proc_model.base_model.euser,
            )
        )
    if not rv:
        return None
    return rv


def set_container_selector(selectors: Dict, image_pat: str):
    """
    Set the container selector in the provided selectors dictionary.

    Args:
        selectors (Dict): The selectors dictionary.
        image_pat (str): The image pattern to set in the container selector.
    """
    if lib.CONT_SELECTOR_FIELD not in selectors:
        cont_sel = {lib.MATCH_FIELDS_FIELD: {"image": image_pat}}
    else:
        cont_sel = selectors[lib.CONT_SELECTOR_FIELD]
        if lib.MATCH_FIELDS_FIELD not in cont_sel:
            cont_sel[lib.MATCH_FIELDS_FIELD] = {"image": image_pat}
        else:
            cont_sel[lib.MATCH_FIELDS_FIELD]["image"] = image_pat
    selectors[lib.CONT_SELECTOR_FIELD] = cont_sel
