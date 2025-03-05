from typing import Dict, List, Optional

import spyctl.config.configs as cfg
import spyctl.spyctl_lib as lib
from spyctl.api.objects import get_objects


def handle_input_data(data: Dict, ctx: cfg.Context = None) -> List[Dict]:
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
        rv.extend(__handle_uid_list_input(data, ctx))
    elif lib.ITEMS_FIELD in data:
        rv.extend(__handle_spyctl_items_input(data))
    return rv


def __handle_fprint_group_input(data: Dict):
    return data[lib.DATA_FIELD][lib.FPRINT_GRP_FINGERPRINTS_FIELD]


def __handle_uid_list_input(data: Dict, ctx: Optional[cfg.Context] = None):
    if not ctx:
        ctx = cfg.get_current_context()
    fprint_uids = [
        uid
        for uid in data[lib.DATA_FIELD][lib.UIDS_FIELD]
        if uid.startswith("fprint")
    ]
    fprints = []
    if fprint_uids:
        fprints = get_objects(*ctx.get_api_data(), fprint_uids, use_pbar=False)
    deviation_uids = [
        uid
        for uid in data[lib.DATA_FIELD][lib.UIDS_FIELD]
        if uid.startswith("dev")
    ]
    deviations = []
    if deviation_uids:
        deviations = get_objects(
            *ctx.get_api_data(), deviation_uids, use_pbar=False
        )
    return fprints + deviations


def __handle_spyctl_items_input(data: Dict):
    rv = []
    for item in data[lib.ITEMS_FIELD]:
        rv.extend(handle_input_data(item))
    return rv
