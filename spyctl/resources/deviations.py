from typing import Dict, List

import spyctl.config.configs as cfg
import spyctl.merge_lib.merge_object_helper as _m_obj_h
import spyctl.spyctl_lib as lib
from spyctl.api.athena_search import search_athena


def get_unique_deviations(uid, st, et, full_rec=False) -> List[Dict]:
    rv = {}
    ctx = cfg.get_current_context()
    query = lib.query_builder(
        "event_deviation", None, show_hint=False, **{"policy_uid_equals": uid}
    )
    for deviation in search_athena(
        *ctx.get_api_data(),
        "event_deviation",
        query,
        start_time=st,
        end_time=et,
    ):
        checksum = deviation.get(lib.CHECKSUM_FIELD)
        if not checksum:
            continue
        if checksum not in rv:
            if not full_rec:
                rv[checksum] = deviation["deviation"]
            else:
                rv[checksum] = deviation
    return list(rv.values())


def get_deviations_stream(
    ctx: cfg.Context,
    time,
    disable_pbar_on_first,
    unique=False,
    raw_data=False,
    include_irrelevant=False,
    policies=None,
    limit_mem=True,
    dev_name_or_uid=None,
):
    if policies is None:
        policies = {}
    policy_uids = {
        policy[lib.METADATA_FIELD].get(
            lib.METADATA_UID_FIELD
        ): _m_obj_h.get_merge_object(
            lib.POL_KIND, policy, True, "check_deviations"
        )
        for policy in policies
    }  # policy uid -> merge object
    emit_processed = {}  # tracks if we should emit a deviation
    unique_deviations = {}  # For unique deviations (not raw)
    dev_list = []  # For all deviations (not raw)
    query = lib.query_builder(
        "event_deviation", dev_name_or_uid, show_hint=False, **{}
    )
    for deviation in search_athena(
        *ctx.get_api_data(),
        "event_deviation",
        query,
        start_time=time[0],
        end_time=time[1],
        desc="Retrieving Deviations",
        limit_mem=limit_mem,
        disable_pbar_on_first=disable_pbar_on_first,
    ):
        __set_checksum(deviation)
        checksum = deviation.get(lib.CHECKSUM_FIELD)
        pol_uid = deviation["policy_uid"]
        key = (checksum, pol_uid)
        if unique and include_irrelevant:
            # We want all unique deviations, including irrelevant ones
            if key not in unique_deviations and key not in emit_processed:
                if raw_data:
                    emit_processed[key] = True
                    yield deviation
                else:
                    unique_deviations[key] = deviation
        elif unique:
            # We want only unique relevant deviations
            if key not in emit_processed:
                m_obj = policy_uids[pol_uid]
                m_obj.asymmetric_merge(
                    deviation[lib.DEVIATION_FIELD], check_irrelevant=True
                )
                if m_obj.is_relevant_obj(lib.DEVIATION_KIND, checksum):
                    emit_processed[key] = True
                    unique_deviations[key] = deviation
                else:
                    emit_processed[key] = False
        elif include_irrelevant:
            # We want all deviations
            if raw_data:
                yield deviation
            else:
                dev_list.append(deviation)
        else:
            # We want all relevant deviations
            if key not in emit_processed:
                m_obj = policy_uids[pol_uid]
                m_obj.asymmetric_merge(
                    deviation[lib.DEVIATION_FIELD], check_irrelevant=True
                )
                if m_obj.is_relevant_obj(lib.DEVIATION_KIND, checksum):
                    emit_processed[key] = True
                else:
                    emit_processed[key] = False
            if emit_processed[key]:
                if raw_data:
                    yield deviation
                else:
                    dev_list.append(deviation)

    # If we got to this point we want unique relevant deviations
    # or all deviations in a format suitable for merging/diffing
    if unique and unique_deviations:
        if raw_data:
            for deviation in unique_deviations.values():
                yield deviation
        else:
            yield __build_items_output(list(unique_deviations.values()))
    elif dev_list:
        yield __build_items_output(dev_list)


def __set_checksum(deviation: Dict) -> Dict:
    deviation[lib.DEVIATION_FIELD][lib.METADATA_FIELD][lib.CHECKSUM_FIELD] = (
        deviation.get(lib.CHECKSUM_FIELD)
    )


def __build_items_output(deviations: List[Dict]) -> Dict:
    if len(deviations) == 1:
        return deviations[0]["deviation"]
    elif len(deviations) > 1:
        return {
            lib.API_FIELD: lib.API_VERSION,
            lib.ITEMS_FIELD: [d["deviation"] for d in deviations],
        }
    else:
        return {}
