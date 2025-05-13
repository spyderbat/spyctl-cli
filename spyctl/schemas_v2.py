"""Contains the schemas for the various objects managed by spyctl"""

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring,no-self-argument
# pylint: disable=raise-missing-from, too-few-public-methods
# pylint: disable=super-init-not-called


from __future__ import annotations

import ipaddress
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Dict, Iterator, List, Optional, Set, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    IPvAnyNetwork,
    ValidationError,
    ValidationInfo,
    field_validator,
    model_validator,
)
from typing_extensions import Annotated, Literal

import spyctl.spyctl_lib as lib

_proc_id_ctx = ContextVar("_proc_id_ctx", default=None)


@contextmanager
def init_proc_id_context(value: Dict[str, Any]) -> Iterator[None]:
    """This allows for objects to use dynamic validation
    data. Such as ensuring a set of process ids is unique
    within a policy
    """
    token = _proc_id_ctx.set(value)
    try:
        yield
    finally:
        _proc_id_ctx.reset(token)


def valid_object(
    data: Dict, verbose=True, allow_obj_list=True, interactive=False
) -> bool:
    kind = data.get(lib.KIND_FIELD)
    if kind not in KIND_TO_SCHEMA:
        if lib.ITEMS_FIELD not in data:
            lib.err_exit(
                f"Unable to validate {kind!r}, no schema exists for objects of"
                " that type."
            )
        elif not allow_obj_list:
            lib.err_exit("Nested item lists are not allowed.")
        try:
            GuardianObjectListModel(**data)
        except ValidationError as e:
            if verbose:
                if interactive:
                    return str(e)
                else:
                    lib.try_log(str(e), is_warning=True)
            return False
        for item in data[lib.ITEMS_FIELD]:
            if not valid_object(item, allow_obj_list=False):
                return False
        return True
    # Some validations depend on the type of the object in addition to the kind
    tmp_kind = (
        kind,
        data.get(lib.METADATA_FIELD, {}).get(lib.METADATA_TYPE_FIELD),
    )
    if tmp_kind in KIND_TO_SCHEMA:
        kind = tmp_kind
    try:
        KIND_TO_SCHEMA[kind](**data)
    except ValidationError as e:
        if verbose:
            if interactive:
                return str(e)
            else:
                lib.try_log(str(e), is_warning=True)
        return False
    return True


def valid_context(context_data: Dict, verbose=True):
    try:
        ContextsModel(**context_data)
    except ValidationError as e:
        if verbose:
            lib.try_log(str(e), is_warning=True)
        return False
    return True


def handle_show_schema(kind: str) -> str:
    obj = KIND_TO_SCHEMA.get(kind)
    return obj.model_json_schema(by_alias=True)


# -----------------------------------------------------------------------------
# Selectors -------------------------------------------------------------------
# -----------------------------------------------------------------------------

EXPR_SYNTAX = "{key: <key>, operator: <operator>, values: [<value1>, <value2>, ...]}"


class SelectorExpression(BaseModel):
    key: str = Field(alias=lib.KEY_FIELD)
    operator: Literal["In", "NotIn", "Exists", "DoesNotExist"] = Field(
        alias=lib.OPERATOR_FIELD
    )
    values: Optional[List[str]] = Field(None, alias=lib.VALUES_FIELD)

    @model_validator(mode="after")
    def ensure_values(self):
        if self.operator in ["Exists", "DoesNotExist"]:
            if self.values:
                raise ValueError(
                    f"'{self.operator}' operator does not accept"
                    f" values. Found '{self.values}'"
                )
        else:
            if not self.values:
                raise ValueError(f"'{self.operator}' operator requires values.")
        return self


def encode_expr(key, operator, values=None) -> str:
    if operator in ["Exists", "DoesNotExist"]:
        if values:
            raise ValueError(
                f"'{operator}' operator does not accept values. Found '{values}'"  # noqa
            )
    else:
        if not values:
            raise ValueError(f"'{operator}' operator requires values.")
    values_ = "[" + ", ".join(f"{ns}" for ns in values) + "]"
    expr = "{ " + f"key: {key}, operator: {operator}, values: {values_}" + " }"  # noqa
    return expr


class MatchLabelsModel(BaseModel):
    match_labels: Optional[Dict[str, str]] = Field(None, alias=lib.MATCH_LABELS_FIELD)
    model_config = ConfigDict(extra="forbid")


class MatchExpressionModel(BaseModel):
    match_expressions: Optional[List[SelectorExpression]] = Field(
        None, alias=lib.MATCH_EXPRESSIONS_FIELD, min_length=1
    )
    model_config = ConfigDict(extra="forbid")


class LabelsMatchModel(MatchLabelsModel, MatchExpressionModel):
    @model_validator(mode="after")
    def ensure_one_field(self):
        values = self.model_dump(by_alias=True, exclude_unset=True)
        if not any(value for value in values.values()):
            raise ValueError("Need matchLabels or matchExpressions")
        return self

    model_config = ConfigDict(extra="forbid")


class MatchFieldsModel(BaseModel):
    match_fields: Optional[Dict[str, str]] = Field(None, alias=lib.MATCH_FIELDS_FIELD)

    @classmethod
    def get_valid_fields(cls):
        return tuple()

    @field_validator("match_fields")
    @classmethod
    def ensure_valid_fields(cls, values):
        if values is None:
            return values
        valid_fields = cls.get_valid_fields()
        for field in values:
            if field not in valid_fields:
                raise ValueError(
                    f"Invalid field '{field}'. Valid fields are {valid_fields}"
                )
        return values

    model_config = ConfigDict(extra="forbid")


class MatchFieldsExpressionsModel(MatchFieldsModel):
    match_fields_expressions: Optional[List[SelectorExpression]] = Field(
        None, alias=lib.MATCH_FIELDS_EXPRESSIONS_FIELD, min_length=1
    )

    @field_validator("match_fields_expressions")
    @classmethod
    def ensure_valid_field_expressions(cls, values: Dict):
        if values is None:
            return values
        valid_fields = cls.get_valid_fields()
        exprs: List[SelectorExpression] = values
        for expr in exprs:
            if expr.key not in valid_fields:
                raise ValueError(
                    f"Invalid key in expr '{expr.key}'. Valid fields are {valid_fields}"  # noqa
                )
        return values

    model_config = ConfigDict(extra="forbid")


CONTAINER_VALID_FIELDS = (
    "image",
    "imageID",
    "containerName",
    "containerID",
)


class ContainerMatchModel(MatchFieldsExpressionsModel):
    # This is a hack to ensure that the valid fields show up in show-schemas
    valid_fields: Optional[Literal[CONTAINER_VALID_FIELDS]] = Field(  # type: ignore
        default=None
    )

    @classmethod
    def get_valid_fields(cls):
        return CONTAINER_VALID_FIELDS

    model_config = ConfigDict(extra="forbid")


CLUSTER_VALID_FIELDS = (
    "name",
    "uid",
)


class ClusterMatchModel(MatchFieldsExpressionsModel):
    # This is a hack to ensure that the valid fields show up in show-schemas
    valid_fields: Optional[Literal[CLUSTER_VALID_FIELDS]] = Field(default=None)  # type: ignore

    @classmethod
    def get_valid_fields(cls):
        return CLUSTER_VALID_FIELDS


SERVICE_VALID_FIELDS = (
    "cgroup",
    "name",
)


class ServiceMatchModel(MatchFieldsExpressionsModel):
    # This is a hack to ensure that the valid fields show up in show-schemas
    valid_fields: Optional[Literal[SERVICE_VALID_FIELDS]] = Field(default=None)  # type: ignore

    @classmethod
    def get_valid_fields(cls):
        return SERVICE_VALID_FIELDS


MACHINE_VALID_FIELDS = (
    "hostname",
    "sourceName",
    "uid",
)


class MachineMatchModel(MatchFieldsExpressionsModel):
    # This is a hack to ensure that the valid fields show up in show-schemas
    valid_fields: Optional[Literal[MACHINE_VALID_FIELDS]] = Field(default=None)  # type: ignore

    @classmethod
    def get_valid_fields(cls):
        return MACHINE_VALID_FIELDS


TRACE_VALID_FIELDS = (
    "triggerClass",
    "triggerAncestors",
)


class TraceMatchModel(MatchFieldsExpressionsModel):
    # This is a hack to ensure that the valid fields show up in show-schemas
    valid_fields: Optional[Literal[TRACE_VALID_FIELDS]] = Field(default=None)  # type: ignore

    @classmethod
    def get_valid_fields(cls):
        return TRACE_VALID_FIELDS


USER_VALID_FIELDS = ("user",)


class UserMatchModel(MatchFieldsExpressionsModel):
    # This is a hack to ensure that the valid fields show up in show-schemas
    valid_fields: Optional[Literal[USER_VALID_FIELDS]] = Field(default=None)  # type: ignore

    @classmethod
    def get_valid_fields(cls):
        return USER_VALID_FIELDS


PROCESS_VALID_FIELDS = (
    "name",
    "exe",
    "euser",
)


class ProcessMatchModel(MatchFieldsExpressionsModel):
    # This is a hack to ensure that the valid fields show up in show-schemas
    valid_fields: Optional[Literal[PROCESS_VALID_FIELDS]] = Field(default=None)  # type: ignore

    @classmethod
    def get_valid_fields(cls):
        return PROCESS_VALID_FIELDS


class ContainerSelectorModel(ContainerMatchModel):
    image: Optional[str] = Field(None, alias=lib.IMAGE_FIELD)
    image_id: Optional[str] = Field(None, alias=lib.IMAGEID_FIELD)
    container_name: Optional[str] = Field(None, alias=lib.CONTAINER_NAME_FIELD)
    container_id: Optional[str] = Field(None, alias=lib.CONTAINER_ID_FIELD)

    model_config = ConfigDict(extra="forbid")


class ClusterSelectorModel(ClusterMatchModel):
    model_config = ConfigDict(extra="forbid")


class ServiceSelectorModel(ServiceMatchModel):
    cgroup: Optional[str] = Field(None, alias=lib.CGROUP_FIELD)
    model_config = ConfigDict(extra="forbid")


class MachineSelectorModel(MachineMatchModel):
    hostname: Optional[Union[str, List[str]]] = Field(None, alias=lib.HOSTNAME_FIELD)
    machine_uid: Optional[Union[str, List[str]]] = Field(
        None, alias=lib.MACHINE_UID_FIELD
    )

    model_config = ConfigDict(extra="forbid")


class NamespaceSelectorModel(LabelsMatchModel):
    pass


class PodSelectorModel(LabelsMatchModel):
    pass


class TraceSelectorModel(TraceMatchModel):
    trigger_class: Optional[List[str]] = Field(None, alias=lib.TRIGGER_CLASS_FIELD)
    trigger_ancestor: Optional[List[str]] = Field(
        None, alias=lib.TRIGGER_ANCESTORS_FIELD
    )
    model_config = ConfigDict(extra="forbid")


class UserSelectorModel(UserMatchModel):
    users: Optional[List[str]] = Field(None, alias=lib.USERS_FIELD)
    interactive_users: Optional[List[str]] = Field(
        None, alias=lib.INTERACTIVE_USERS_FIELD
    )
    non_interactive_users: Optional[List[str]] = Field(
        None, alias=lib.NON_INTERACTIVE_USERS_FIELD
    )
    model_config = ConfigDict(extra="forbid")


class ProcessSelectorModel(ProcessMatchModel):
    name: Optional[List[str]] = Field(None, alias=lib.NAME_FIELD, min_length=1)
    exe: Optional[List[str]] = Field(None, alias=lib.EXE_FIELD, min_length=1)
    euser: Optional[List[str]] = Field(None, alias=lib.EUSER_FIELD, min_length=1)

    @model_validator(mode="after")
    def ensure_one_field(
        self,
    ):
        values = self.model_dump(by_alias=True, exclude_unset=True)
        set_count = 0
        for v in values.values():
            if v is not None:
                set_count += 1
        if set_count == 0:
            raise ValueError("At least one key, value pair expected")
        return self

    model_config = ConfigDict(extra="forbid")


# -----------------------------------------------------------------------------
# Ruleset Models --------------------------------------------------------------
# -----------------------------------------------------------------------------


class RuleModel(BaseModel):
    target: str = Field(alias=lib.RULE_TARGET_FIELD)  # type: ignore
    verb: Literal[tuple(lib.RULE_VERBS)] = Field(  # type: ignore
        alias=lib.RULE_VERB_FIELD,
    )
    values: List[str] = Field(alias=lib.RULE_VALUES_FIELD)


class ContainerRule(RuleModel):
    cluster_selector: Optional[ClusterSelectorModel] = Field(
        None, alias=lib.CLUS_SELECTOR_FIELD
    )
    namespace_selector: Optional[NamespaceSelectorModel] = Field(
        None, alias=lib.NAMESPACE_SELECTOR_FIELD
    )
    pod_selector: Optional[PodSelectorModel] = Field(None, alias=lib.POD_SELECTOR_FIELD)
    container_selector: Optional[ContainerSelectorModel] = Field(
        None, alias=lib.CONT_SELECTOR_FIELD
    )
    target: Literal[tuple(lib.CONTAINER_RULE_TARGETS)] = Field(  # type: ignore
        alias=lib.RULE_TARGET_FIELD
    )


class ProcessRule(RuleModel):
    cluster_selector: Optional[ClusterSelectorModel] = Field(
        None, alias=lib.CLUS_SELECTOR_FIELD
    )
    namespace_selector: Optional[NamespaceSelectorModel] = Field(
        None, alias=lib.NAMESPACE_SELECTOR_FIELD
    )
    pod_selector: Optional[PodSelectorModel] = Field(None, alias=lib.POD_SELECTOR_FIELD)
    container_selector: Optional[ContainerSelectorModel] = Field(
        None, alias=lib.CONT_SELECTOR_FIELD
    )
    process_selector: Optional[ProcessSelectorModel] = Field(
        None, alias=lib.PROCESS_SELECTOR_FIELD
    )
    target: Literal[tuple(lib.PROCESS_RULE_TARGETS)] = Field(  # type: ignore
        alias=lib.RULE_TARGET_FIELD
    )


class RulesetMetadataModel(BaseModel):
    name: str = Field(alias=lib.METADATA_NAME_FIELD)
    type: Literal[tuple(lib.RULESET_TYPES)] = Field(  # type: ignore
        alias=lib.METADATA_TYPE_FIELD
    )
    create_time: Optional[Union[int, float]] = Field(
        None, alias=lib.METADATA_CREATE_TIME
    )
    created_by: Optional[str] = Field(None, alias=lib.METADATA_CREATED_BY)
    last_updated: Optional[Union[int, float]] = Field(
        None, alias=lib.METADATA_LAST_UPDATE_TIME
    )
    last_updated_by: Optional[str] = Field(None, alias=lib.METADATA_LAST_UPDATED_BY)
    version: Optional[int] = Field(None, alias=lib.METADATA_VERSION_FIELD)
    uid: Optional[str] = Field(None, alias=lib.METADATA_UID_FIELD)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if " " in v:
            raise ValueError("Name cannot contain spaces.")
        if len(v) > 64:
            raise ValueError("Name must be less than 64 characters.")
        return v


class RulesetPolicySpecModel(BaseModel):
    rules: List[
        Annotated[
            Union[ContainerRule, ProcessRule],
            Field(discriminator=lib.RULE_TARGET_FIELD),
        ]
    ] = Field(
        alias=lib.RULES_FIELD,
    )


class RulesetModel(BaseModel):
    api_version: str = Field(alias=lib.API_FIELD)
    kind: Literal[lib.RULESET_KIND] = Field(alias=lib.KIND_FIELD)  # type: ignore  # noqa: E501
    metadata: RulesetMetadataModel = Field(alias=lib.METADATA_FIELD)
    spec: RulesetPolicySpecModel = Field(alias=lib.SPEC_FIELD)
    model_config = ConfigDict(extra="ignore")


# -----------------------------------------------------------------------------
# Guardian Models -------------------------------------------------------------
# -----------------------------------------------------------------------------


# This is a reused validator ensuring that the objects have a required selector
def validate_selectors(model: GuardianObjectModel):
    values = model.model_dump(by_alias=True, exclude_unset=True)
    pol_type = values["metadata"]["type"]
    if pol_type == lib.POL_TYPE_CONT:
        s_val = values["spec"].get(lib.CONT_SELECTOR_FIELD)
        if not s_val:
            raise ValueError(
                f"Type is '{lib.POL_TYPE_CONT}' and no "
                f"'{lib.CONT_SELECTOR_FIELD}' found in {lib.SPEC_FIELD}"
            )
    elif pol_type == lib.POL_TYPE_SVC:
        s_val = values["spec"].get(lib.SVC_SELECTOR_FIELD)
        if not s_val:
            raise ValueError(
                f"Type is '{lib.POL_TYPE_SVC}' and no "
                f"'{lib.SVC_SELECTOR_FIELD}' found in {lib.SPEC_FIELD}"
            )
    elif pol_type == lib.POL_TYPE_CLUS:
        s_val = values["spec"].get(lib.CLUS_SELECTOR_FIELD)
        if not s_val:
            raise ValueError(
                f"Type is '{lib.POL_TYPE_CLUS}' and no "
                f"'{lib.CLUS_SELECTOR_FIELD}' found in {lib.SPEC_FIELD}"
            )
    return model


class GuardianSelectorsModel(BaseModel):
    container_selector: Optional[ContainerSelectorModel] = Field(
        None, alias=lib.CONT_SELECTOR_FIELD
    )
    service_selector: Optional[ServiceSelectorModel] = Field(
        None, alias=lib.SVC_SELECTOR_FIELD
    )
    cluster_selector: Optional[ClusterSelectorModel] = Field(
        None, alias=lib.CLUS_SELECTOR_FIELD
    )
    machine_selector: Optional[MachineSelectorModel] = Field(
        None, alias=lib.MACHINE_SELECTOR_FIELD
    )
    namespace_selector: Optional[NamespaceSelectorModel] = Field(
        None, alias=lib.NAMESPACE_SELECTOR_FIELD
    )
    pod_selector: Optional[PodSelectorModel] = Field(None, alias=lib.POD_SELECTOR_FIELD)
    model_config = ConfigDict(extra="forbid")


class ClusterPolicySelectorsModel(BaseModel):
    cluster_selector: ClusterSelectorModel = Field(alias=lib.CLUS_SELECTOR_FIELD)
    model_config = ConfigDict(extra="forbid")


class ActionSelectorsModel(BaseModel):
    cluster_selector: Optional[ClusterSelectorModel] = Field(
        None, alias=lib.CLUS_SELECTOR_FIELD
    )
    container_selector: Optional[ContainerSelectorModel] = Field(
        None, alias=lib.CONT_SELECTOR_FIELD
    )
    machine_selector: Optional[MachineSelectorModel] = Field(
        None, alias=lib.MACHINE_SELECTOR_FIELD
    )
    namespace_selector: Optional[NamespaceSelectorModel] = Field(
        None, alias=lib.NAMESPACE_SELECTOR_FIELD
    )
    pod_selector: Optional[PodSelectorModel] = Field(None, alias=lib.POD_SELECTOR_FIELD)
    process_selector: Optional[ProcessSelectorModel] = Field(
        None, alias=lib.PROCESS_SELECTOR_FIELD
    )
    model_config = ConfigDict(extra="forbid")


class GuardianSpecOptionsModel(BaseModel):
    disable_processes: Optional[
        Literal[tuple(lib.DISABLE_PROCS_STRINGS)]  # type: ignore
    ] = Field(None, alias=lib.DISABLE_PROCS_FIELD)
    disable_connections: Optional[
        Literal[tuple(lib.DISABLE_CONNS_STRINGS)]  # type: ignore
    ] = Field(None, alias=lib.DISABLE_CONNS_FIELD)
    disable_private_conns: Optional[
        Literal[tuple(lib.DISABLE_CONNS_STRINGS)]  # type: ignore
    ] = Field(None, alias=lib.DISABLE_PR_CONNS_FIELD)
    disable_public_conns: Optional[
        Literal[tuple(lib.DISABLE_CONNS_STRINGS)]  # type: ignore
    ] = Field(None, alias=lib.DISABLE_PU_CONNS_FIELD)


# Network Models --------------------------------------------------------------


class DnsBlockModel(BaseModel):
    dns_selector: List[str] = Field(alias=lib.DNS_SELECTOR_FIELD)
    model_config = ConfigDict(extra="forbid")


class CIDRModel(BaseModel):
    cidr: IPvAnyNetwork = Field(alias=lib.CIDR_FIELD)
    except_cidr: Optional[List[IPvAnyNetwork]] = Field(
        None, alias=lib.EXCEPT_FIELD, max_length=10
    )

    @model_validator(mode="after")
    def validate_except_within_cidr(self):
        values = self.model_dump(by_alias=True, exclude_unset=True)
        cidr = values["cidr"]
        try:
            cidr_net = ipaddress.IPv4Network(cidr)
        except ipaddress.AddressValueError:
            cidr_net = ipaddress.IPv6Network(cidr)
        net_type = type(cidr_net)
        if "except_cidr" in values and values["except_cidr"]:
            for e_cidr in values["except_cidr"]:
                try:
                    e_net = ipaddress.IPv4Network(e_cidr)
                except ipaddress.AddressValueError:
                    e_net = ipaddress.IPv6Network(e_cidr)
                if net_type != type(e_net):
                    raise ValueError("Network types are not the same")
                if not cidr_net.supernet_of(e_net):
                    raise ValueError(f"'{e_net}' is not a subnet of '{cidr_net}'")
        return self

    model_config = ConfigDict(extra="forbid")


class IpBlockModel(BaseModel):
    ip_block: CIDRModel = Field(alias=lib.IP_BLOCK_FIELD)
    model_config = ConfigDict(extra="forbid")


class PortsModel(BaseModel):
    port: int = Field(alias=lib.PORT_FIELD, ge=0, le=65535)
    proto: Literal["UDP", "TCP"] = Field(alias=lib.PROTO_FIELD)
    endport: Optional[int] = Field(None, alias=lib.ENDPORT_FIELD, ge=0, le=66535)

    @model_validator(mode="after")
    def endport_ge_port(self):
        values = self.model_dump(by_alias=True, exclude_unset=True)
        endport = values.get("endport")
        if endport is not None and endport < values["port"]:
            raise ValueError(
                f"{lib.ENDPORT_FIELD} must be greater than or equal to"
                f" {lib.PORT_FIELD}"
            )
        return self

    model_config = ConfigDict(extra="forbid")


class IngressNodeModel(BaseModel):
    from_field: List[Union[DnsBlockModel, IpBlockModel]] = Field(
        alias=lib.FROM_FIELD, min_length=1
    )
    processes: Optional[List[str]] = Field(
        None, alias=lib.PROCESSES_FIELD, min_length=1
    )
    ports: List[PortsModel] = Field(alias=lib.PORTS_FIELD, min_length=1)

    def __init__(self, /, **data):
        self.__pydantic_validator__.validate_python(
            data, self_instance=self, context=_proc_id_ctx.get()
        )

    @field_validator("processes")
    @classmethod
    def validate_proc_ids(cls, v: str, info: ValidationInfo):
        if not v:
            return v
        bad = []
        if isinstance(info.context, set):
            for proc_id in v:
                if proc_id not in info.context:
                    bad.append(proc_id)
        if bad:
            raise ValueError(f"No process found with id(s) '{bad}'.")
        return v

    model_config = ConfigDict(extra="forbid")


class EgressNodeModel(BaseModel):
    to: List[Union[DnsBlockModel, IpBlockModel]] = Field(
        alias=lib.TO_FIELD, min_length=1
    )
    processes: Optional[List[str]] = Field(
        None, alias=lib.PROCESSES_FIELD, min_length=1
    )
    ports: List[PortsModel] = Field(alias=lib.PORTS_FIELD, min_length=1)

    def __init__(self, /, **data):
        self.__pydantic_validator__.validate_python(
            data, self_instance=self, context=_proc_id_ctx.get()
        )

    @field_validator("processes")
    @classmethod
    def validate_proc_ids(cls, v: str, info: ValidationInfo):
        if not v:
            return v
        bad = []
        if isinstance(info.context, set):
            for proc_id in v:
                if proc_id not in info.context:
                    bad.append(proc_id)
        if bad:
            raise ValueError(f"No process found with id(s) '{bad}'.")
        return v

    model_config = ConfigDict(extra="forbid")


class NetworkPolicyModel(BaseModel):
    ingress: List[IngressNodeModel] = Field(alias=lib.INGRESS_FIELD)
    egress: List[EgressNodeModel] = Field(alias=lib.EGRESS_FIELD)


class DeviationNetworkPolicyModel(BaseModel):
    ingress: Optional[List[IngressNodeModel]] = Field(None, alias=lib.INGRESS_FIELD)
    egress: Optional[List[EgressNodeModel]] = Field(None, alias=lib.EGRESS_FIELD)


# Process Models --------------------------------------------------------------


class SimpleProcessNodeModel(BaseModel):
    name: str = Field(alias=lib.NAME_FIELD)
    exe: List[str] = Field(alias=lib.EXE_FIELD)
    euser: Optional[List[str]] = Field(None, alias=lib.EUSER_FIELD)


class ProcessNodeModel(SimpleProcessNodeModel):
    id: str = Field(alias=lib.ID_FIELD)
    listening_sockets: Optional[List[PortsModel]] = Field(
        None, alias=lib.LISTENING_SOCKETS
    )
    children: Optional[List[ProcessNodeModel]] = Field(None, alias=lib.CHILDREN_FIELD)

    def __init__(self, /, **data):
        self.__pydantic_validator__.validate_python(
            data, self_instance=self, context=_proc_id_ctx.get()
        )

    @field_validator("id")
    @classmethod
    def validate_no_duplicate_ids(cls, v: str, info: ValidationInfo):
        if isinstance(info.context, set):
            proc_ids: Set = info.context
            if v in proc_ids:
                raise ValueError(f"Duplicate id '{v}' detected.")
            proc_ids.add(v)
        return v

    model_config = ConfigDict(extra="forbid")


class GuardDeviationProcessNodeModel(BaseModel):
    id: str = Field(alias=lib.ID_FIELD)
    children: Optional[List[ProcessNodeModel]] = Field(None, alias=lib.CHILDREN_FIELD)
    model_config = ConfigDict(extra="forbid")

    def __init__(self, /, **data):
        self.__pydantic_validator__.validate_python(
            data, self_instance=self, context=_proc_id_ctx.get()
        )

    @field_validator("id")
    @classmethod
    def validate_no_duplicate_ids(cls, v: str, info: ValidationInfo):
        if isinstance(info.context, set):
            proc_ids: Set = info.context
            if v in proc_ids:
                raise ValueError(f"Duplicate id '{v}' detected.")
            proc_ids.add(v)
        return v


class GuardDeviationNodeModel(BaseModel):
    policy_node: GuardDeviationProcessNodeModel = Field(alias="policyNode")
    model_config = ConfigDict(extra="forbid")


# Actions Models --------------------------------------------------------------


class SharedDefaultActionFieldsModel(BaseModel):
    enabled: Optional[bool] = Field(None, alias=lib.ENABLED_FIELD)
    model_config = ConfigDict(extra="forbid")


class SharedActionFieldsModel(ActionSelectorsModel):
    enabled: Optional[bool] = Field(None, alias=lib.ENABLED_FIELD)

    @model_validator(mode="after")
    def validate_has_selector(self):
        values = self.model_dump(by_alias=True, exclude_unset=True)
        count = 0
        values_count = 0
        for key, value in values.items():
            if key.endswith("Selector"):
                count += 1
            if isinstance(value, dict) and any(v for v in value.values()):
                values_count += 1
        if count == 0:
            raise ValueError("At least one selector required for non-default actions.")
        if values_count != count:
            raise ValueError("All selectors must have values.")
        return self

    model_config = ConfigDict(extra="forbid")


class DefaultMakeRedflagModel(SharedDefaultActionFieldsModel):
    content: Optional[str] = Field(None, alias=lib.FLAG_CONTENT, max_length=350)
    impact: Optional[str] = Field(None, alias=lib.FLAG_IMPACT, max_length=100)
    severity: Literal[tuple(lib.ALLOWED_SEVERITIES)] = Field(  # type: ignore
        alias=lib.FLAG_SEVERITY
    )
    model_config = ConfigDict(extra="forbid")


class MakeRedflagModel(SharedActionFieldsModel, DefaultMakeRedflagModel):
    pass


class DefaultAgentReniceProcessModel(SharedDefaultActionFieldsModel):
    priority: str = Field(alias=lib.PROC_PRIORITY)
    model_config = ConfigDict(extra="forbid")


class AgentReniceProcessModel(SharedActionFieldsModel, DefaultAgentReniceProcessModel):
    pass


class DefaultMakeOpsflagModel(BaseModel):
    content: Optional[str] = Field(None, alias=lib.FLAG_CONTENT, max_length=350)
    description: Optional[str] = Field(None, alias=lib.FLAG_DESCRIPTION, max_length=350)
    severity: Literal[tuple(lib.ALLOWED_SEVERITIES)] = Field(  # type: ignore
        alias=lib.FLAG_SEVERITY
    )
    model_config = ConfigDict(extra="forbid")


class MakeOpsflagModel(SharedActionFieldsModel, DefaultMakeOpsflagModel):
    pass


class DefaultActionsModel(BaseModel):
    make_redflag: Optional[DefaultMakeRedflagModel] = Field(
        None, alias=lib.ACTION_MAKE_REDFLAG
    )
    make_opsflag: Optional[DefaultMakeOpsflagModel] = Field(
        None, alias=lib.ACTION_MAKE_OPSFLAG
    )
    agent_kill_pod: Optional[SharedDefaultActionFieldsModel] = Field(
        None, alias=lib.ACTION_KILL_POD
    )
    agent_kill_proc: Optional[SharedDefaultActionFieldsModel] = Field(
        None, alias=lib.ACTION_KILL_PROC
    )
    agent_kill_proc_group: Optional[SharedDefaultActionFieldsModel] = Field(
        None, alias=lib.ACTION_KILL_PROC_GRP
    )
    agent_kill_proc_tree: Optional[SharedDefaultActionFieldsModel] = Field(
        None, alias=lib.ACTION_KILL_PROC_TREE
    )
    agent_renice_proc: Optional[DefaultAgentReniceProcessModel] = Field(
        None, alias=lib.ACTION_RENICE_PROC
    )

    @model_validator(mode="after")
    def validate_only_one_action(self):
        values = self.model_dump(by_alias=True, exclude_unset=True)
        actions_count = len(values)
        if actions_count > 1:
            raise ValueError(
                "Detected multiple action definitions in one action. Each"
                " action definition must be a separate entry in the list."
            )
        return self

    model_config = ConfigDict(extra="forbid")


class ResponseActionsModel(BaseModel):
    make_redflag: Optional[MakeRedflagModel] = Field(
        None, alias=lib.ACTION_MAKE_REDFLAG
    )
    make_opsflag: Optional[MakeOpsflagModel] = Field(
        None, alias=lib.ACTION_MAKE_OPSFLAG
    )
    agent_kill_pod: Optional[SharedActionFieldsModel] = Field(
        None, alias=lib.ACTION_KILL_POD
    )
    agent_kill_proc: Optional[SharedActionFieldsModel] = Field(
        None, alias=lib.ACTION_KILL_PROC
    )
    agent_kill_proc_group: Optional[SharedActionFieldsModel] = Field(
        None, alias=lib.ACTION_KILL_PROC_GRP
    )
    agent_kill_proc_tree: Optional[SharedActionFieldsModel] = Field(
        None, alias=lib.ACTION_KILL_PROC_TREE
    )
    agent_renice_proc: Optional[AgentReniceProcessModel] = Field(
        None, alias=lib.ACTION_RENICE_PROC
    )

    @model_validator(mode="after")
    def validate_only_one_action(self):
        values = self.model_dump(by_alias=True, exclude_unset=True)
        actions_count = len(values)
        if actions_count > 1:
            raise ValueError(
                "Detected multiple action definitions in one action. Each"
                " action definition must be a separate entry in the list."
            )
        return self

    @model_validator(mode="after")
    def validated_not_none_if_set(self):
        values = self.model_dump(by_alias=True, exclude_unset=True)
        value = next(iter(values.values()))
        if value is None:
            raise ValueError("Non-default actions must have a selector")
        return self

    model_config = ConfigDict(extra="forbid")


class GuardianResponseModel(BaseModel):
    default_field: List[DefaultActionsModel] = Field(alias=lib.RESP_DEFAULT_FIELD)
    response_field: List[ResponseActionsModel] = Field(alias=lib.RESP_ACTIONS_FIELD)


# Metadata Models -------------------------------------------------------------


class GuardianMetadataModel(BaseModel):
    name: str = Field(alias=lib.METADATA_NAME_FIELD)
    type: Literal[tuple(lib.GUARDIAN_POL_TYPES)] = Field(  # type: ignore
        alias=lib.METADATA_TYPE_FIELD
    )
    create_time: Optional[Union[int, float, str]] = Field(
        None, alias=lib.METADATA_CREATE_TIME
    )
    first_timestamp: Optional[Union[int, float, str]] = Field(
        None, alias=lib.FIRST_TIMESTAMP_FIELD
    )
    latest_timestamp: Optional[Union[int, float, str]] = Field(
        None, alias=lib.LATEST_TIMESTAMP_FIELD
    )
    uid: Optional[str] = Field(None, alias=lib.METADATA_UID_FIELD)
    checksum: Optional[str] = Field(None, alias=lib.METADATA_S_CHECKSUM_FIELD)


class GuardianFingerprintGroupMetadataModel(BaseModel):
    image: Optional[str] = Field(None, alias=lib.IMAGE_FIELD)
    image_id: Optional[str] = Field(None, alias=lib.IMAGEID_FIELD)
    cgroup: Optional[str] = Field(None, alias=lib.CGROUP_FIELD)
    first_timestamp: Optional[Union[int, float]] = Field(
        None, alias=lib.FIRST_TIMESTAMP_FIELD
    )
    latest_timestamp: Optional[Union[int, float]] = Field(
        None, alias=lib.LATEST_TIMESTAMP_FIELD
    )


class GuardianDeviationMetadataModel(BaseModel):
    type: str = Field(alias=lib.METADATA_TYPE_FIELD)
    policy_uid: str = Field(alias="policy_uid")
    checksum: str = Field(alias=lib.CHECKSUM_FIELD)
    uid: str = Field(alias=lib.METADATA_UID_FIELD)


# Spec Models -----------------------------------------------------------------


class GuardianPolicySpecFieldsModel(BaseModel):
    enabled: Optional[bool] = Field(None, alias=lib.ENABLED_FIELD)
    mode: Literal[tuple(lib.POL_MODES)] = Field(  # type: ignore
        alias=lib.POL_MODE_FIELD
    )


class GuardianPolicySpecModel(
    GuardianSelectorsModel,
    GuardianSpecOptionsModel,
    GuardianPolicySpecFieldsModel,
):
    process_policy: List[ProcessNodeModel] = Field(alias=lib.PROC_POLICY_FIELD)
    network_policy: NetworkPolicyModel = Field(alias=lib.NET_POLICY_FIELD)
    response: GuardianResponseModel = Field(alias=lib.RESPONSE_FIELD)
    model_config = ConfigDict(extra="forbid")

    def __init__(self, **data: Any):
        with init_proc_id_context(set()):
            super().__init__(**data)


class GuardianBaselineSpecModel(GuardianSelectorsModel, GuardianSpecOptionsModel):
    process_policy: List[ProcessNodeModel] = Field(alias=lib.PROC_POLICY_FIELD)
    network_policy: NetworkPolicyModel = Field(alias=lib.NET_POLICY_FIELD)
    model_config = ConfigDict(extra="forbid")

    def __init__(self, **data: Any):
        with init_proc_id_context(set()):
            super().__init__(**data)


class GuardianDeviationSpecModel(GuardianSelectorsModel, GuardianSpecOptionsModel):
    process_policy: Optional[
        List[Union[ProcessNodeModel, GuardDeviationNodeModel]]
    ] = Field(None, alias=lib.PROC_POLICY_FIELD)
    network_policy: Optional[DeviationNetworkPolicyModel] = Field(
        None, alias=lib.NET_POLICY_FIELD
    )
    rules: Optional[List[ContainerRule]] = Field(
        None,
        alias=lib.RULES_FIELD,
        # discriminator=lib.RULE_TARGET_FIELD,
    )
    matches: Optional[Dict] = Field(None, alias=lib.RULE_MATCHES_FIELD)
    model_config = ConfigDict(extra="forbid")

    def __init__(self, **data: Any):
        with init_proc_id_context(set()):
            super().__init__(**data)


class ClusterPolicySpecModel(
    ClusterPolicySelectorsModel, GuardianPolicySpecFieldsModel
):
    rulesets: List[str] = Field(alias=lib.RULESETS_FIELD)
    response: GuardianResponseModel = Field(alias=lib.RESPONSE_FIELD)

    @classmethod
    def get_valid_actions(cls):
        return (
            lib.ACTION_KILL_POD,
            lib.ACTION_MAKE_REDFLAG,
            lib.ACTION_MAKE_OPSFLAG,
        )

    model_config = ConfigDict(extra="forbid")


# Top-level Models ------------------------------------------------------------


class GuardianFingerprintModel(BaseModel):
    api_version: str = Field(alias=lib.API_FIELD)
    kind: Literal[lib.FPRINT_KIND] = Field(alias=lib.KIND_FIELD)  # type: ignore
    metadata: GuardianMetadataModel = Field(alias=lib.METADATA_FIELD)
    spec: GuardianBaselineSpecModel = Field(alias=lib.SPEC_FIELD)

    _selector_validator = model_validator(mode="after")(validate_selectors)

    model_config = ConfigDict(extra="forbid")


class FingerprintGroupDataModel(BaseModel):
    fingerprints: List[GuardianFingerprintModel] = Field(
        alias=lib.FPRINT_GRP_FINGERPRINTS_FIELD
    )
    cont_names: Optional[List[str]] = Field(None, alias=lib.FPRINT_GRP_CONT_NAMES_FIELD)
    cont_ids: Optional[List[str]] = Field(None, alias=lib.FPRINT_GRP_CONT_IDS_FIELD)
    machines: Optional[List[str]] = Field(None, alias=lib.FPRINT_GRP_MACHINES_FIELD)
    model_config = ConfigDict(extra="forbid")


class GuardianFingerprintGroupModel(BaseModel):
    api_version: str = Field(alias=lib.API_FIELD)
    kind: Literal[lib.FPRINT_GROUP_KIND] = Field(alias=lib.KIND_FIELD)  # type: ignore
    metadata: GuardianFingerprintGroupMetadataModel = Field(alias=lib.METADATA_FIELD)
    data: FingerprintGroupDataModel
    model_config = ConfigDict(extra="ignore")


class GuardianDeviationModel(BaseModel):
    api_version: str = Field(alias=lib.API_FIELD)
    kind: Literal[lib.DEVIATION_KIND] = Field(alias=lib.KIND_FIELD)  # type: ignore
    metadata: GuardianDeviationMetadataModel = Field(alias=lib.METADATA_FIELD)
    spec: GuardianDeviationSpecModel = Field(alias=lib.SPEC_FIELD)


class GuardianBaselineModel(BaseModel):
    api_version: str = Field(alias=lib.API_FIELD)
    kind: Literal[lib.BASELINE_KIND] = Field(alias=lib.KIND_FIELD)  # type: ignore
    metadata: GuardianMetadataModel = Field(alias=lib.METADATA_FIELD)
    spec: GuardianBaselineSpecModel = Field(alias=lib.SPEC_FIELD)

    _selector_validator = model_validator(mode="after")(validate_selectors)

    model_config = ConfigDict(extra="ignore")


class ClusterPolicyModel(BaseModel):
    api_version: str = Field(alias=lib.API_FIELD)
    kind: Literal[lib.POL_KIND] = Field(alias=lib.KIND_FIELD)  # type: ignore
    metadata: GuardianMetadataModel = Field(alias=lib.METADATA_FIELD)
    spec: ClusterPolicySpecModel = Field(alias=lib.SPEC_FIELD)
    _selector_validator = model_validator(mode="after")(validate_selectors)
    model_config = ConfigDict(extra="forbid")


class GuardianPolicyModel(BaseModel):
    api_version: str = Field(alias=lib.API_FIELD)
    kind: Literal[lib.POL_KIND] = Field(alias=lib.KIND_FIELD)  # type: ignore
    metadata: GuardianMetadataModel = Field(alias=lib.METADATA_FIELD)
    spec: GuardianPolicySpecModel = Field(alias=lib.SPEC_FIELD)
    _selector_validator = model_validator(mode="after")(validate_selectors)
    model_config = ConfigDict(extra="forbid")


class GuardianObjectModel(BaseModel):
    api_version: str = Field(alias=lib.API_FIELD)
    kind: str = Field(alias=lib.KIND_FIELD)
    metadata: Dict[str, str] = Field(alias=lib.METADATA_FIELD)
    spec: Dict = Field(alias=lib.SPEC_FIELD)
    model_config = ConfigDict(extra="ignore")


class GuardianObjectListModel(BaseModel):
    api_version: str = Field(alias=lib.API_FIELD)
    items: List[Union[GuardianObjectModel, GuardianFingerprintGroupModel]] = Field(
        alias=lib.ITEMS_FIELD
    )


# -----------------------------------------------------------------------------
# Notification Models ---------------------------------------------------------
# -----------------------------------------------------------------------------


class NotificationSettingsModel(BaseModel):
    uid: Union[str, None] = Field(None, alias=lib.METADATA_UID_FIELD)
    aggregate: Union[bool, None] = Field(False, alias=lib.NOTIF_AGGREGATE_FIELD)
    aggregate_by: Union[List[str], None] = Field(
        None, alias=lib.NOTIF_AGGREGATE_BY_FIELD
    )
    aggregate_seconds: Union[int, None] = Field(
        None, alias=lib.NOTIF_AGGREGATE_SECONDS_FIELD
    )
    is_enabled: bool = Field(alias=lib.NOTIF_IS_ENABLED_FIELD)
    cooldown: Union[int, None] = Field(None, alias=lib.NOTIF_COOLDOWN_FIELD)
    cooldown_by: Union[List[str], None] = Field(None, alias=lib.NOTIF_COOLDOWN_BY_FIELD)
    target_map: Union[Dict[str, str], None] = Field(
        None, alias=lib.NOTIF_TARGET_MAP_FIELD
    )


class EmailTargetSpecModel(BaseModel):
    emails: List[str] = Field(alias=lib.TGT_EMAILS_FIELD)


class SlackTargetSpecModel(BaseModel):
    url: str = Field(alias=lib.TGT_SLACK_URL)


class PagerDutyTargetSpecModel(BaseModel):
    routing_key: str = Field(alias=lib.TGT_ROUTING_KEY_FIELD)


class WebhookTargetSpecModel(BaseModel):
    url: str = Field(alias=lib.TGT_WEBHOOK_URL)


def validate_tgt_spec(model: NotificationTgtResourceModel):
    tgt_type = model.metadata.tgt_type
    spec = model.spec
    if spec is None:
        return
    try:
        if tgt_type == lib.TGT_TYPE_EMAIL:
            EmailTargetSpecModel.model_validate(spec)
        elif tgt_type == lib.TGT_TYPE_SLACK:
            SlackTargetSpecModel.model_validate(spec)
        elif tgt_type == lib.TGT_TYPE_PAGERDUTY:
            PagerDutyTargetSpecModel.model_validate(spec)
        elif tgt_type == lib.TGT_TYPE_WEBHOOK:
            WebhookTargetSpecModel.model_validate(spec)
        else:
            raise ValueError(f"Invalid target type: {tgt_type}")
    except ValidationError as e:
        raise ValueError(f"Invalid target spec: {e}") from e


class NotifTgtMetadataModel(BaseModel):
    name: str = Field(alias=lib.METADATA_NAME_FIELD)
    description: Optional[str] = Field(None, alias=lib.TGT_DESCRIPTION_FIELD)
    tgt_type: Literal[tuple(lib.TGT_TYPES)] = Field(  # type: ignore
        alias=lib.METADATA_TYPE_FIELD
    )
    uid: Optional[str] = Field(None, alias=lib.METADATA_UID_FIELD)
    create_time: Optional[Union[float, int]] = Field(
        None, alias=lib.METADATA_CREATE_TIME
    )
    update_time: Optional[Union[float, int]] = Field(None, alias=lib.NOTIF_LAST_UPDATED)
    last_updated_by: Optional[str] = Field(None, alias=lib.METADATA_LAST_UPDATED_BY)
    created_by: Optional[str] = Field(None, alias=lib.METADATA_CREATED_BY)
    version: Optional[int] = Field(None, alias=lib.VERSION_FIELD)
    tags: Optional[List[str]] = Field(None, alias=lib.METADATA_TAGS_FIELD)


class NotificationTgtResourceModel(BaseModel):
    api_version: str = Field(alias=lib.API_FIELD)
    kind: Literal[lib.TARGET_KIND] = Field(alias=lib.KIND_FIELD)  # type: ignore
    metadata: NotifTgtMetadataModel = Field(alias=lib.METADATA_FIELD)
    spec: Optional[Dict] = Field(None, alias=lib.SPEC_FIELD)
    _spec_validator = model_validator(mode="after")(validate_tgt_spec)
    model_config = ConfigDict(extra="forbid")


class EmailTemplateSpecModel(BaseModel):
    subject: str = Field(alias=lib.TMPL_EMAIL_SUBJECT_FIELD)
    body_text: Optional[str] = Field(default=None, alias=lib.TMPL_EMAIL_BODY_TEXT_FIELD)
    body_html: Optional[str] = Field(default=None, alias=lib.TMPL_EMAIL_BODY_HTML_FIELD)


class PagerDutyTemplateSpecModel(BaseModel):
    summary: str = Field(alias=lib.TMPL_PD_SUMMARY_FIELD)
    severity: str = Field(alias=lib.TMPL_PD_SEVERITY_FIELD)
    source: str = Field(alias=lib.TMPL_PD_SOURCE_FIELD)
    component: Optional[str] = Field(default=None, alias=lib.TMPL_PD_COMPONENT_FIELD)
    group: Optional[str] = Field(default=None, alias=lib.TMPL_PD_GROUP_FIELD)
    class_field: Optional[str] = Field(default=None, alias=lib.TMPL_PD_CLASS_FIELD)
    custom_details: Optional[Dict] = Field(
        default=None, alias=lib.TMPL_PD_CUSTOM_DETAILS_FIELD
    )
    dedup_key: Optional[str] = Field(default=None, alias=lib.TMPL_PD_DEDUP_KEY_FIELD)


class WebhookTemplateSpecModel(BaseModel):
    payload: Optional[Dict] = Field(default=None, alias=lib.TMPL_WEBHOOK_PAYLOAD_FIELD)
    entire_object: Optional[bool] = Field(
        default=False, alias=lib.TMPL_WEBHOOK_ENTIRE_OBJECT_FIELD
    )


class SlackTemplateSpecModel(BaseModel):
    text: str = Field(alias=lib.TMPL_SLACK_TEXT_FIELD)
    blocks: Optional[List[Dict]] = Field(
        default=None, alias=lib.TMPL_SLACK_BLOCKS_FIELD
    )


def validate_tmpl_spec(model: NotificationTemplateModel):
    tmpl_type = model.metadata.tmpl_type
    spec = model.spec
    try:
        if tmpl_type == lib.TMPL_TYPE_EMAIL:
            EmailTemplateSpecModel.model_validate(spec)
        elif tmpl_type == lib.TMPL_TYPE_SLACK:
            SlackTemplateSpecModel.model_validate(spec)
        elif tmpl_type == lib.TMPL_TYPE_PD:
            PagerDutyTemplateSpecModel.model_validate(spec)
        elif tmpl_type == lib.TMPL_TYPE_WEBHOOK:
            WebhookTemplateSpecModel.model_validate(spec)
        else:
            raise ValueError(f"Invalid template type: {tmpl_type}")
    except ValidationError as e:
        raise ValueError(f"Invalid template spec: {e}") from e


class NotificationTemplateMetadataModel(BaseModel):
    name: str = Field(alias=lib.METADATA_NAME_FIELD)
    description: Optional[str] = Field(None, alias=lib.TMPL_DESCRIPTION_FIELD)
    tmpl_type: Literal[tuple(lib.TMPL_TYPES)] = Field(  # type: ignore
        alias=lib.METADATA_TYPE_FIELD
    )
    uid: Optional[str] = Field(None, alias=lib.METADATA_UID_FIELD)
    create_time: Optional[Union[float, int]] = Field(
        None, alias=lib.METADATA_CREATE_TIME
    )
    update_time: Optional[Union[float, int]] = Field(None, alias=lib.NOTIF_LAST_UPDATED)
    last_updated_by: Optional[str] = Field(None, alias=lib.METADATA_LAST_UPDATED_BY)
    created_by: Optional[str] = Field(None, alias=lib.METADATA_CREATED_BY)
    version: Optional[int] = Field(None, alias=lib.VERSION_FIELD)
    tags: Optional[List[str]] = Field(None, alias=lib.METADATA_TAGS_FIELD)


class NotificationTemplateModel(BaseModel):
    api_version: str = Field(alias=lib.API_FIELD)
    kind: Literal[lib.TEMPLATE_KIND] = Field(alias=lib.KIND_FIELD)  # type: ignore
    metadata: NotificationTemplateMetadataModel = Field(alias=lib.METADATA_FIELD)
    spec: Dict = Field(alias=lib.SPEC_FIELD)
    _spec_validator = model_validator(mode="after")(validate_tmpl_spec)
    model_config = ConfigDict(extra="forbid")


class AgentHealthNotificationMetadataModel(BaseModel):
    name: str = Field(alias=lib.METADATA_NAME_FIELD)
    description: Optional[str] = Field(None, alias=lib.TGT_DESCRIPTION_FIELD)
    uid: Optional[str] = Field(None, alias=lib.METADATA_UID_FIELD)
    create_time: Optional[Union[float, int]] = Field(
        None, alias=lib.METADATA_CREATE_TIME
    )
    created_by: Optional[str] = Field(None, alias=lib.METADATA_CREATED_BY)
    last_updated_by: Optional[str] = Field(None, alias=lib.METADATA_LAST_UPDATED_BY)
    last_updated: Optional[Union[float, int]] = Field(
        None, alias=lib.METADATA_LAST_UPDATE_TIME
    )
    version: Optional[int] = Field(None, alias=lib.VERSION_FIELD)
    action_taken: Optional[str] = Field(None, alias=lib.METADATA_ACTION_TAKEN)


class AgentHealthNotificationsSettingsModel(BaseModel):
    agent_healthy: Optional[NotificationSettingsModel] = Field(
        None, alias=lib.NOTIF_TRIGGER_AHE
    )
    agent_unhealthy: Optional[NotificationSettingsModel] = Field(
        None, alias=lib.NOTIF_TRIGGER_AUN
    )
    agent_offline: Optional[NotificationSettingsModel] = Field(
        None, alias=lib.NOTIF_TRIGGER_AOFF
    )
    agent_online: Optional[NotificationSettingsModel] = Field(
        None, alias=lib.NOTIF_TRIGGER_AON
    )


class AgentHealthNotificationSpecModel(BaseModel):
    scope_query: Optional[str] = Field(None, alias=lib.AH_NOTIF_SCOPE_QUERY_FIELD)
    notification_settings: Optional[AgentHealthNotificationsSettingsModel] = Field(
        None, alias=lib.NOTIFICATION_SETTINGS_FIELD
    )


class AgentHealthNotificationModel(BaseModel):
    api_version: str = Field(alias=lib.API_FIELD)
    kind: Literal[lib.AGENT_HEALTH_NOTIFICATION_KIND] = (  # type: ignore
        Field(alias=lib.KIND_FIELD)
    )
    metadata: AgentHealthNotificationMetadataModel = Field(alias=lib.METADATA_FIELD)
    spec: AgentHealthNotificationSpecModel = Field(alias=lib.SPEC_FIELD)


# -----------------------------------------------------------------------------
# Suppression Models ----------------------------------------------------------
# -----------------------------------------------------------------------------


class SuppressionPolicySelectorsModel(BaseModel):
    trace_selector: Optional[TraceSelectorModel] = Field(
        None, alias=lib.TRACE_SELECTOR_FIELD
    )
    user_selector: Optional[UserSelectorModel] = Field(
        None, alias=lib.USER_SELECTOR_FIELD
    )
    cluster_selector: Optional[ClusterSelectorModel] = Field(
        None, alias=lib.CLUS_SELECTOR_FIELD
    )
    machine_selector: Optional[MachineSelectorModel] = Field(
        None, alias=lib.MACHINE_SELECTOR_FIELD
    )
    namespace_selector: Optional[NamespaceSelectorModel] = Field(
        None, alias=lib.NAMESPACE_SELECTOR_FIELD
    )
    pod_selector: Optional[PodSelectorModel] = Field(None, alias=lib.POD_SELECTOR_FIELD)
    container_selector: Optional[ContainerSelectorModel] = Field(
        None, alias=lib.CONT_SELECTOR_FIELD
    )
    service_selector: Optional[ServiceSelectorModel] = Field(
        None, alias=lib.SVC_SELECTOR_FIELD
    )

    @model_validator(mode="after")
    def ensure_one_field(self):
        values = self.model_dump(by_alias=True, exclude_unset=True)
        if not any(
            value for field, value in values.items() if field.endswith("Selector")
        ):
            raise ValueError("Selectors must have values.")
        return self

    model_config = ConfigDict(extra="forbid")


# Metadata Models -------------------------------------------------------------


class SuppressionPolicyMetadataModel(BaseModel):
    name: str = Field(alias=lib.METADATA_NAME_FIELD)
    type: Literal[tuple(lib.SUPPRESSION_POL_TYPES)] = Field(  # type: ignore
        alias=lib.METADATA_TYPE_FIELD
    )
    create_time: Optional[Union[int, float, str]] = Field(
        None, alias=lib.METADATA_CREATE_TIME
    )
    first_timestamp: Optional[Union[int, float]] = Field(
        None, alias=lib.FIRST_TIMESTAMP_FIELD
    )
    latest_timestamp: Optional[Union[int, float]] = Field(
        None, alias=lib.LATEST_TIMESTAMP_FIELD
    )
    uid: Optional[str] = Field(None, alias=lib.METADATA_UID_FIELD)
    checksum: Optional[str] = Field(None, alias=lib.METADATA_S_CHECKSUM_FIELD)


# Spec Models -----------------------------------------------------------------


class AllowedFlagsModel(BaseModel):
    class_field: str = Field(alias=lib.FLAG_CLASS)


class SuppressionPolicySpecModel(SuppressionPolicySelectorsModel):
    enabled: Optional[bool] = Field(None, alias=lib.ENABLED_FIELD)
    mode: Literal[tuple(lib.POL_MODES)] = Field(  # type: ignore
        alias=lib.POL_MODE_FIELD
    )
    allowed_flags: List[AllowedFlagsModel] = Field(alias=lib.ALLOWED_FLAGS_FIELD)
    model_config = ConfigDict(extra="forbid")


# Top-level Models ------------------------------------------------------------


class SuppressionPolicyModel(BaseModel):
    api_version: str = Field(alias=lib.API_FIELD)
    kind: Literal[lib.POL_KIND] = Field(alias=lib.KIND_FIELD)  # type: ignore
    metadata: SuppressionPolicyMetadataModel = Field(alias=lib.METADATA_FIELD)
    spec: SuppressionPolicySpecModel = Field(alias=lib.SPEC_FIELD)
    model_config = ConfigDict(extra="forbid")


# -----------------------------------------------------------------------------
# Saved Query Models ----------------------------------------------------------
# -----------------------------------------------------------------------------


class SavedQueryMetadataModel(BaseModel):
    name: str = Field(alias=lib.METADATA_NAME_FIELD)
    create_time: Optional[Union[float, int]] = Field(
        None, alias=lib.METADATA_CREATE_TIME
    )
    created_by: Optional[str] = Field(None, alias=lib.METADATA_CREATED_BY)
    uid: Optional[str] = Field(None, alias=lib.METADATA_UID_FIELD)
    last_used: Optional[Union[float, int]] = Field(None, alias=lib.METADATA_LAST_USED)


class SavedQuerySpecModel(BaseModel):
    query_schema: str = Field(alias=lib.QUERY_SCHEMA_FIELD)
    query: str = Field(alias=lib.QUERY_FIELD)
    description: Optional[str] = Field(None, alias=lib.QUERY_DESCRIPTION_FIELD)
    notification_settings: Optional[NotificationSettingsModel] = Field(
        None, alias=lib.NOTIFICATION_SETTINGS_FIELD
    )
    additional_settings: Optional[Dict] = Field(
        None, alias=lib.ADDITIONAL_SETTINGS_FIELD
    )


class SavedQueryModel(BaseModel):
    api_version: str = Field(alias=lib.API_FIELD)
    kind: Literal[lib.SAVED_QUERY_KIND] = Field(alias=lib.KIND_FIELD)  # type: ignore
    metadata: SavedQueryMetadataModel = Field(alias=lib.METADATA_FIELD)
    spec: SavedQuerySpecModel = Field(alias=lib.SPEC_FIELD)
    model_config = ConfigDict(extra="forbid")


# -----------------------------------------------------------------------------
# Custom Flag Models ----------------------------------------------------------
# -----------------------------------------------------------------------------


class CustomFlagMetadataModel(BaseModel):
    name: str = Field(alias=lib.METADATA_NAME_FIELD)
    create_time: Optional[Union[float, int]] = Field(
        None, alias=lib.METADATA_CREATE_TIME
    )
    uid: Optional[str] = Field(None, alias=lib.METADATA_UID_FIELD)
    created_by: Optional[str] = Field(None, alias=lib.METADATA_CREATED_BY)
    last_updated: Optional[Union[float, int]] = Field(
        None, alias=lib.METADATA_LAST_UPDATE_TIME
    )
    last_updated_by: Optional[str] = Field(None, alias=lib.METADATA_LAST_UPDATED_BY)
    version: Optional[int] = Field(None, alias=lib.VERSION_FIELD)
    tags: Optional[List[str]] = Field(None, alias=lib.METADATA_TAGS_FIELD)
    action_taken: Optional[str] = Field(None, alias=lib.METADATA_ACTION_TAKEN)
    saved_query_uid: Optional[str] = Field(None, alias=lib.SAVED_QUERY_UID)
    query_schema: str = Field(None, alias=lib.QUERY_SCHEMA_FIELD)


class FlagSettingsField(BaseModel):
    flag_type: Literal[tuple(lib.FLAG_TYPES)] = Field(  # type: ignore
        None,
        alias=lib.TYPE_FIELD,
    )
    description: str = Field(None, alias=lib.FLAG_DESCRIPTION)
    severity: Literal[tuple(lib.ALLOWED_SEVERITIES)] = Field(  # type: ignore
        None,
        alias=lib.FLAG_SEVERITY,
    )
    impact: Optional[str] = Field(None, alias=lib.FLAG_IMPACT)
    content: Optional[str] = Field(None, alias=lib.FLAG_CONTENT)


class CustomFlagSpecModel(BaseModel):
    enabled: bool = Field(None, alias=lib.ENABLED_FIELD)
    query: str = Field(None, alias=lib.QUERY_FIELD)
    flag_settings: Optional[FlagSettingsField] = Field(
        None, alias=lib.FLAG_SETTINGS_FIELD
    )
    notification_settings: Optional[NotificationSettingsModel] = Field(
        None, alias=lib.NOTIFICATION_SETTINGS_FIELD
    )


class CustomFlagModel(BaseModel):
    api_version: str = Field(alias=lib.API_FIELD)
    kind: Literal[lib.CUSTOM_FLAG_KIND] = Field(alias=lib.KIND_FIELD)  # type: ignore
    metadata: CustomFlagMetadataModel = Field(alias=lib.METADATA_FIELD)
    spec: CustomFlagSpecModel = Field(alias=lib.SPEC_FIELD)

    model_config = ConfigDict(extra="forbid")


# -----------------------------------------------------------------------------
# Config Models ----------------------------------------------------------
# -----------------------------------------------------------------------------


class ContextModel(BaseModel):
    org: str = Field(alias=lib.ORG_FIELD)
    cgroups: Optional[Union[str, List[str]]] = Field(None, alias=lib.CGROUP_FIELD)
    cluster: Optional[Union[str, List[str]]] = Field(None, alias=lib.CLUSTER_FIELD)
    container_ids: Optional[Union[str, List[str]]] = Field(
        None, alias=lib.CONTAINER_ID_FIELD
    )
    container_names: Optional[Union[str, List[str]]] = Field(
        None, alias=lib.CONTAINER_NAME_FIELD
    )
    image_ids: Optional[Union[str, List[str]]] = Field(None, alias=lib.IMAGEID_FIELD)
    images: Optional[Union[str, List[str]]] = Field(None, alias=lib.IMAGE_FIELD)
    machines: Optional[Union[str, List[str]]] = Field(None, alias=lib.MACHINES_FIELD)
    namespace: Optional[Union[str, List[str]]] = Field(None, alias=lib.NAMESPACE_FIELD)
    pods: Optional[Union[str, List[str]]] = Field(None, alias=lib.POD_FIELD)
    model_config = ConfigDict(extra="forbid")


# Metadata Models -------------------------------------------------------------


class SecretMetadataModel(BaseModel):
    name: str = Field(alias=lib.METADATA_NAME_FIELD)
    create_time: Optional[Union[float, int]] = Field(
        None, alias=lib.METADATA_CREATE_TIME
    )


# Top-level Models ------------------------------------------------------------


class SecretModel(BaseModel):
    api_version: str = Field(alias=lib.API_FIELD)
    kind: Literal[lib.SECRET_KIND] = Field(alias=lib.KIND_FIELD)  # type: ignore
    metadata: SecretMetadataModel = Field(alias=lib.METADATA_FIELD)
    data: Optional[Dict[str, str]] = Field(None, alias=lib.DATA_FIELD)
    string_data: Optional[Dict[str, str]] = Field(None, alias=lib.STRING_DATA_FIELD)
    model_config = ConfigDict(extra="forbid")


class ContextsModel(BaseModel):
    context_name: str = Field(alias=lib.CONTEXT_NAME_FIELD)
    secret: str = Field(alias=lib.SECRET_FIELD)
    context: ContextModel = Field(alias=lib.CONTEXT_FIELD)
    model_config = ConfigDict(extra="forbid")


class ConfigModel(BaseModel):
    api_version: str = Field(alias=lib.API_FIELD)
    kind: Literal[lib.CONFIG_KIND] = Field(alias=lib.KIND_FIELD)  # type: ignore
    contexts: List[ContextsModel] = Field(alias=lib.CONTEXTS_FIELD)
    current_context: str = Field(alias=lib.CURR_CONTEXT_FIELD)
    model_config = ConfigDict(extra="forbid")


# -----------------------------------------------------------------------------
# Misc Models -----------------------------------------------------------------
# -----------------------------------------------------------------------------


class UidListMetadataModel(BaseModel):
    start_time: Union[int, float] = Field(alias=lib.METADATA_START_TIME_FIELD)
    end_time: Union[int, float] = Field(alias=lib.METADATA_END_TIME_FIELD)

    @model_validator(mode="after")
    def valid_end_time(self):
        if self.end_time <= self.start_time:
            raise ValueError(
                f"'{lib.METADATA_END_TIME_FIELD}' must be greater than"
                f" '{lib.METADATA_START_TIME_FIELD}'"
            )
        return self


class UidListDataModel(BaseModel):
    uids: List[str] = Field(alias=lib.UIDS_FIELD)
    model_config = ConfigDict(extra="forbid")


class UidListModel(BaseModel):
    api_version: str = Field(alias=lib.API_FIELD)
    kind: Literal[lib.UID_LIST_KIND] = Field(alias=lib.KIND_FIELD)  # type: ignore
    metadata: UidListMetadataModel = Field(alias=lib.METADATA_FIELD)
    data: UidListDataModel = Field(alias=lib.DATA_FIELD)
    model_config = ConfigDict(extra="forbid")


class SpyderbatObject(BaseModel):
    api_version: Literal[lib.API_VERSION] = Field(alias=lib.API_FIELD)  # type: ignore
    kind: str = Field(alias=lib.KIND_FIELD)

    @field_validator("kind")
    @classmethod
    def valid_kind(cls, v):
        if v not in KIND_TO_SCHEMA:
            raise ValueError(f"Kind '{v}' not in {list(KIND_TO_SCHEMA)}")
        return v

    model_config = ConfigDict(extra="allow")


KIND_TO_SCHEMA: Dict[str, BaseModel] = {
    lib.BASELINE_KIND: GuardianBaselineModel,
    lib.CONFIG_KIND: ConfigModel,
    lib.FPRINT_GROUP_KIND: GuardianFingerprintGroupModel,
    lib.FPRINT_KIND: GuardianFingerprintModel,
    lib.POL_KIND: GuardianPolicyModel,
    (lib.POL_KIND, lib.POL_TYPE_TRACE): SuppressionPolicyModel,
    (lib.POL_KIND, lib.POL_TYPE_CLUS): ClusterPolicyModel,
    lib.SECRET_KIND: SecretModel,
    lib.UID_LIST_KIND: UidListModel,
    lib.DEVIATION_KIND: GuardianDeviationModel,
    lib.TARGET_KIND: NotificationTgtResourceModel,
    lib.TEMPLATE_KIND: NotificationTemplateModel,
    lib.CLUSTER_RULESET_RESOURCE.kind: RulesetModel,
    lib.SAVED_QUERY_RESOURCE.kind: SavedQueryModel,
    lib.CUSTOM_FLAG_RESOURCE.kind: CustomFlagModel,
    lib.AGENT_HEALTH_NOTIFICATION_RESOURCE.kind: AgentHealthNotificationModel,
}


def get_validation_ctx_data(kind: str) -> Dict:
    if kind == lib.POL_KIND:
        return {"proc_ids": set()}
    return {}
