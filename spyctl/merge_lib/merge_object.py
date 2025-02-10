"""
Module containing the MergeObject class. Which holds the data used to
merge and diff objects.
"""

# pylint: disable=comparison-with-callable


import difflib
import time
from copy import deepcopy
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Union,
)

from pydantic import ValidationError

import spyctl.merge_lib.diff_lib as d_lib
import spyctl.merge_lib.merge_lib as m_lib
import spyctl.merge_lib.workload_merge as _wl
import spyctl.schemas_v2 as schemas
import spyctl.spyctl_lib as lib
from spyctl import cli
import spyctl.merge_lib.merge_schema as _ms


class MergeObject:
    def __init__(
        self,
        obj_data: Dict,
        merge_schemas: List[_ms.MergeSchema],
        validation_fn: Callable,
        merge_network: bool = True,
        disable_procs: str = None,
        disable_conns: str = None,
    ) -> None:
        self.original_obj = deepcopy(obj_data)
        self.obj_data = deepcopy(obj_data)
        self.schemas = merge_schemas
        self.validation_fn = validation_fn
        self.starting_yaml = cli.make_yaml(obj_data)
        self.merge_network = merge_network
        self.is_guardian = lib.is_guardian_obj(self.original_obj)
        self.current_other = None
        self.irrelevant_objects: Dict[str, Set[str]] = (
            {}
        )  # kind -> Set(checksum or id) if checksum missing
        self.relevant_objects: Dict[str, Set[str]] = (
            {}
        )  # kind -> Set(checksum or id) if checksum missing
        # guardian spec merge settings
        self.__parse_disable_procs_settings(disable_procs)
        self.__parse_disable_conns_settings(disable_conns)

    def symmetric_merge(self, other: Dict, check_irrelevant=False):
        self.current_other = other
        if (spec_cp := self.obj_data.get(lib.SPEC_FIELD)) and check_irrelevant:
            spec_cp = deepcopy(self.obj_data[lib.SPEC_FIELD])
        for schema in self.schemas:
            data = self.obj_data.get(schema.field_key)
            other_data = other.get(schema.field_key, {})
            if (
                not self.__merge_subfields(
                    data, other_data, schema, symmetric=True
                )
                and schema.field_key in self.obj_data
            ):
                del self.obj_data[schema.field_key]
        if spec_cp and check_irrelevant:
            self.check_irrelevant_obj(spec_cp, other)

    def asymmetric_merge(self, other: Dict, check_irrelevant=False):
        self.current_other = other
        if (spec_cp := self.obj_data.get(lib.SPEC_FIELD)) and check_irrelevant:
            spec_cp = deepcopy(self.obj_data[lib.SPEC_FIELD])
        for schema in self.schemas:
            data = self.obj_data.get(schema.field_key)
            other_data = other.get(schema.field_key, {})
            if (
                not self.__merge_subfields(data, other_data, schema)
                and schema.field_key in self.obj_data
            ):
                del self.obj_data[schema.field_key]
        if spec_cp and check_irrelevant:
            self.check_irrelevant_obj(spec_cp, other)

    def is_valid_obj(self) -> bool:
        try:
            self.validation_fn(self.obj_data)
            return True
        except ValidationError as e:
            cli.try_log(f"Merge created invalid object. {' '.join(e.args)}")
            return False

    def check_irrelevant_obj(self, spec_cp: Dict, other: Dict):
        checksum_or_id = self.get_checksum_or_id(other)
        other_kind = other[lib.KIND_FIELD]
        if (
            other_kind in self.relevant_objects
            and checksum_or_id in self.relevant_objects[other_kind]
        ):
            return
        if self.obj_data[lib.SPEC_FIELD] == spec_cp:
            self.irrelevant_objects.setdefault(other_kind, set())
            self.irrelevant_objects[other_kind].add(checksum_or_id)
        else:
            self.relevant_objects.setdefault(other_kind, set())
            self.relevant_objects[other_kind].add(checksum_or_id)

    def get_irrelevant_objects(self) -> Dict[str, Set[str]]:
        return {k: list(v) for k, v in self.irrelevant_objects.items()}

    def is_relevant_obj(self, other_kind: str, other: Union[Dict, str]):
        if isinstance(other, str):
            return other in self.relevant_objects.get(other_kind, set())
        checksum_or_id = self.get_checksum_or_id(other)
        return checksum_or_id in self.relevant_objects.get(other_kind, set())

    def get_checksum_or_id(self, other: Dict) -> str:
        rv = other[lib.METADATA_FIELD].get(lib.CHECKSUM_FIELD)
        if not rv:
            rv = other[lib.METADATA_FIELD].get(lib.METADATA_UID_FIELD)
        if not rv:
            rv = other[lib.METADATA_FIELD].get(
                lib.METADATA_NAME_FIELD, "unknown"
            )
        return rv

    @property
    def is_valid(self) -> bool:
        return schemas.valid_object(self.obj_data)

    def get_diff(
        self, full_diff=False, diff_object=False
    ) -> Optional[Union[str, Dict]]:
        if diff_object and self.is_guardian:
            return d_lib.guardian_object_diff(self.original_obj, self.obj_data)
        diff_lines = list(
            difflib.ndiff(
                cli.make_yaml(self.original_obj).splitlines(),
                cli.make_yaml(self.obj_data).splitlines(),
            )
        )
        diff_lines = self.__add_diff_highlights(diff_lines)
        if full_diff:
            return "\n".join(diff_lines)
        summary = []
        in_sum = set()
        found_spec = False

        def add_line_to_sum(index, sum_line):
            if index not in in_sum:
                if index != 0 and index - 1 >= 0 and index - 1 not in in_sum:
                    summary.append("...")
                summary.append(sum_line)
                in_sum.add(index)

        for i, line in enumerate(diff_lines):
            stripped = line.strip()
            if (
                line.startswith(f"{lib.ADD_COLOR}{m_lib.ADD_START}")
                or line.startswith(f"{m_lib.ADD_START}")
                or line.startswith(f"{lib.SUB_COLOR}{m_lib.SUB_START}")
                or line.startswith(f"{m_lib.SUB_START}")
                or not found_spec
                or stripped.startswith(lib.PROC_POLICY_FIELD)
                or stripped.startswith(lib.NET_POLICY_FIELD)
                or stripped.startswith(lib.INGRESS_FIELD)
                or stripped.startswith(lib.EGRESS_FIELD)
            ):
                if line.strip().startswith(lib.SPEC_FIELD):
                    found_spec = True
                for x in range(i - 5, i):
                    if x >= 0:
                        add_line_to_sum(x, diff_lines[x])
                add_line_to_sum(i, line)
                for x in range(i + 1, i + 6):
                    if x < len(diff_lines):
                        add_line_to_sum(x, diff_lines[x])
        if max(in_sum) != len(diff_lines) - 1:
            summary.append("...")
        return "\n".join(summary)

    def __add_diff_highlights(self, diff_lines: List[str]):
        for i, line in enumerate(diff_lines):
            if line.startswith(m_lib.ADD_START):
                diff_lines[i] = f"{lib.ADD_COLOR}{line}{lib.COLOR_END}"
            elif line.startswith(m_lib.SUB_START):
                diff_lines[i] = f"{lib.SUB_COLOR}{line}{lib.COLOR_END}"
        return diff_lines

    def get_obj_data(self):
        return self.obj_data

    def update_latest_timestamp(self, timestamp=None):
        meta = self.obj_data.get(lib.METADATA_FIELD)
        if meta and lib.LATEST_TIMESTAMP_FIELD in meta:
            if timestamp:
                meta[lib.LATEST_TIMESTAMP_FIELD] = timestamp
            else:
                meta[lib.LATEST_TIMESTAMP_FIELD] = time.time()

    def __merge_subfields(
        self,
        data: Optional[Dict],
        other_data: Optional[Dict],
        schema: _ms.MergeSchema,
        symmetric=False,
    ) -> bool:
        for field, func in schema.merge_functions.items():
            f_data = data.get(field) if data is not None else None
            f_other_data = (
                other_data.get(field) if other_data is not None else None
            )
            result = self.__handle_merge_functions(
                f_data, f_other_data, func, symmetric
            )
            if result is None and data and field in data:
                del data[field]
            elif result is not None:
                data[field] = result
        for field, sub_schema in schema.sub_schemas.items():
            if field != sub_schema.field_key:
                raise m_lib.InvalidMergeError(
                    "Bug Detected! Field mismatch with field in sub schema."
                )
            f_data = data.get(field) if data is not None else None
            f_other_data = (
                other_data.get(field) if other_data is not None else None
            )
            if symmetric:
                if f_data is None and f_other_data is None:
                    continue
                elif (
                    f_data is None or f_other_data is None
                ) and sub_schema.is_selector:
                    if field in data:
                        del data[field]
                    continue
                elif f_data is None:
                    data[field] = f_other_data
                elif f_other_data is None:
                    continue
                else:
                    if (
                        not self.__merge_subfields(
                            f_data, f_other_data, sub_schema, symmetric
                        )
                        and field in data
                    ):
                        del data[field]
            else:
                if f_data is None or f_other_data is None:
                    continue
                else:
                    if (
                        not self.__merge_subfields(
                            f_data, f_other_data, sub_schema, symmetric
                        )
                        and field in data
                    ):
                        del data[field]
        # Clear any fields not found in the schema
        valid_fields = set(schema.merge_functions).union(
            set(schema.sub_schemas)
        )
        if data:
            for field in set(data) - valid_fields:
                del data[field]
        if schema.values_required and not data:
            return False
        else:
            return True

    def __handle_merge_functions(
        self, data: Any, other_data: Any, func: Callable, symmetric: bool
    ):
        if not self.merge_network and func == _wl.merge_ingress_or_egress:
            return data
        if symmetric:
            if data is None or other_data is None:
                result = None
            else:
                result = func(self, data, other_data, symmetric)
        else:
            if data is None and other_data is None:
                result = None
            if data is None:
                result = None
            if other_data is None:
                result = data
            else:
                result = func(self, data, other_data, symmetric)
        return result

    def __parse_disable_procs_settings(self, s: str) -> bool:
        dpf = self.original_obj.get(lib.SPEC_FIELD, {}).get(
            lib.DISABLE_PROCS_FIELD, ""
        )
        if s == lib.DISABLE_PROCS_ALL or dpf == lib.DISABLE_PROCS_ALL:
            self.disable_procs = lib.DISABLE_PROCS_ALL
        else:
            self.disable_procs = None

    def __parse_disable_conns_settings(self, s: str) -> bool:
        dcf = self.original_obj.get(lib.SPEC_FIELD, {}).get(
            lib.DISABLE_CONNS_FIELD, ""
        )
        if s == lib.DISABLE_CONNS_ALL or dcf == lib.DISABLE_CONNS_ALL:
            self.disable_conns = lib.DISABLE_CONNS_ALL
        elif s == lib.DISABLE_CONNS_EGRESS or dcf == lib.EGRESS_FIELD:
            self.disable_conns = lib.EGRESS_FIELD
        elif s == lib.DISABLE_CONNS_INGRESS or dcf == lib.INGRESS_FIELD:
            self.disable_conns = lib.INGRESS_FIELD
        else:
            self.disable_conns = None

        dpr = self.original_obj.get(lib.SPEC_FIELD, {}).get(
            lib.DISABLE_PR_CONNS_FIELD, ""
        )
        if s == lib.DISABLE_CONNS_PRIVATE or dpr == lib.DISABLE_CONNS_ALL:
            self.disable_private_conns = lib.DISABLE_CONNS_ALL
        elif s == lib.DISABLE_CONNS_PRIVATE_E or dpr == lib.EGRESS_FIELD:
            self.disable_private_conns = lib.EGRESS_FIELD
        elif s == lib.DISABLE_CONNS_PRIVATE_I or dpr == lib.INGRESS_FIELD:
            self.disable_private_conns = lib.INGRESS_FIELD
        else:
            self.disable_private_conns = None

        dpu = self.original_obj.get(lib.SPEC_FIELD, {}).get(
            lib.DISABLE_PU_CONNS_FIELD, ""
        )
        if s == lib.DISABLE_CONNS_PUBLIC or dpu == lib.DISABLE_CONNS_ALL:
            self.disable_public_conns = lib.DISABLE_CONNS_ALL
        elif s == lib.DISABLE_CONNS_PUBLIC_E or dpu == lib.EGRESS_FIELD:
            self.disable_public_conns = lib.EGRESS_FIELD
        elif s == lib.DISABLE_CONNS_PUBLIC_I or dpu == lib.INGRESS_FIELD:
            self.disable_public_conns = lib.INGRESS_FIELD
        else:
            self.disable_public_conns = None
