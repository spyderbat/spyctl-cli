from typing import Dict, List

import spyctl.config.configs as cfg
import spyctl.resources.api_filters as _af
import spyctl.spyctl_lib as lib
from spyctl.api.source_query_resources import get_deviations, get_fingerprints


def handle_input_data(
    data: Dict, ctx: cfg.Context = None, deviation_src=None
) -> List[Dict]:
    obj_kind = data.get(lib.KIND_FIELD)
    schema = data.get(lib.SCHEMA_FIELD)
    rv = []
    if obj_kind == lib.POL_KIND:
        rv.append(data)
    elif obj_kind == lib.BASELINE_KIND:
        rv.append(data)
    elif obj_kind == lib.FPRINT_KIND:
        rv.append(data)
    elif obj_kind == lib.DEVIATION_KIND or (
        schema and schema.startswith(lib.EVENT_DEVIATION_PREFIX)
    ):
        if obj_kind is None:
            rv.append(data["deviation"])
        else:
            rv.append(data)
    elif obj_kind == lib.FPRINT_GROUP_KIND:
        rv.extend(__handle_fprint_group_input(data))
    elif obj_kind == lib.UID_LIST_KIND:
        rv.extend(__handle_uid_list_input(data, ctx, deviation_src=deviation_src))
    elif lib.ITEMS_FIELD in data:
        rv.extend(__handle_spyctl_items_input(data))
    return rv


def __handle_fprint_group_input(data: Dict):
    return data[lib.DATA_FIELD][lib.FPRINT_GRP_FINGERPRINTS_FIELD]


def __handle_uid_list_input(data: Dict, ctx: cfg.Context = None, deviation_src=None):
    if not ctx:
        ctx = cfg.get_current_context()
    time = (
        data[lib.METADATA_FIELD][lib.METADATA_START_TIME_FIELD],
        data[lib.METADATA_FIELD][lib.METADATA_END_TIME_FIELD],
    )
    src = ctx.global_source
    fprint_uids = [
        uid for uid in data[lib.DATA_FIELD][lib.UIDS_FIELD] if uid.startswith("fprint")
    ]
    fprints = []
    if fprint_uids:
        fprint_pipeline = _af.UID_List.generate_pipeline(fprint_uids)
        fprints = list(
            get_fingerprints(*ctx.get_api_data(), [src], time, pipeline=fprint_pipeline)
        )
    deviation_uids = [
        uid
        for uid in data[lib.DATA_FIELD][lib.UIDS_FIELD]
        if not uid.startswith("fprint")
    ]
    deviations = []
    if deviation_uids:
        dev_src = deviation_src or src
        dev_pipeline = _af.UID_List.generate_pipeline(deviation_uids)
        for deviation in get_deviations(
            *ctx.get_api_data(), [dev_src], time, pipeline=dev_pipeline
        ):
            deviations.append(deviation["deviation"])
    return fprints + deviations


def __handle_spyctl_items_input(data: Dict):
    rv = []
    for item in data[lib.ITEMS_FIELD]:
        rv.extend(handle_input_data(item))
    return rv
