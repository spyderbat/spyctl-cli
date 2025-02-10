"""Library that contains the scope classes used to match with selectors."""

# pylint: disable=too-many-instance-attributes

from dataclasses import dataclass, fields
from typing import Dict
import spyctl.spyctl_lib as lib

CLUSTER_SCOPE = "cluster"
CONTAINER_SCOPE = "container"
LINUX_SERVICE_SCOPE = "linux_service"
MACHINE_SCOPE = "machine"
NAMESPACE_SCOPE = "namespace"
POD_SCOPE = "pod"
PROCESS_SCOPE = "process"
TRACE_SCOPE = "trace"
USER_SCOPE = "user"

# -------------------------------------------------------------


@dataclass
class BaseScope:
    """The base class for all scope classes.

    Scope classes are used to match with selectors.
    The intent is to normalize the data that is used to match with selectors.
    """

    def as_dict(self) -> dict:
        """
        Converts the scope to a dictionary.

        Returns:
            dict: The scope as a dictionary.
        """
        rv = {}
        attr_fields = get_attr_fields(type(self))
        for field in fields(self):
            value = getattr(self, field.name)
            rv[attr_fields[field.name]] = value
        return rv


# -------------------------------------------------------------

LABELS_ATTR = "labels"

NAMESPACE_YAML_TO_ATTR = {
    "matchLabels": "labels",
    "labels": "labels",
}

NAMESPACE_ATTR_TO_YAML = {v: k for k, v in NAMESPACE_YAML_TO_ATTR.items()}


@dataclass
class NamespaceScope(BaseScope):
    """Attributes that are used to match with namespace selectors."""

    labels: Dict[str, str]


POD_YAML_TO_ATTR = {
    "matchLabels": "labels",
    "labels": "labels",
}

POD_ATTR_TO_YAML = {v: k for k, v in POD_YAML_TO_ATTR.items()}


@dataclass
class PodScope(BaseScope):
    """Attributes that are used to match with pod selectors."""

    labels: Dict[str, str]


# -------------------------------------------------------------

CLUS_YAML_TO_ATTR = {
    "name": "cluster_name",
    "uid": "cluster_uid",
}

CLUS_ATTR_TO_YAML = {v: k for k, v in CLUS_YAML_TO_ATTR.items()}


def clus_yaml_to_attr(field_name: str) -> str:
    """
    Converts a field name from a YAML file to an attribute name.

    Parameters:
        field_name (str): The field name from the YAML file.

    Raises:
        KeyError: If the field name is not found in the mapping.

    Returns:
        str: The corresponding attribute name.
    """
    if field_name not in CLUS_YAML_TO_ATTR:
        raise KeyError(f"Unknown field: {field_name}. Add it to scope.py?")
    return CLUS_YAML_TO_ATTR[field_name]


@dataclass
class ClusterScope(BaseScope):
    """Attributes that are used to match with cluster selectors."""

    cluster_name: str
    cluster_uid: str


# -------------------------------------------------------------

MACH_YAML_TO_ATTR = {
    "hostname": "hostname",
    "sourceName": "source_name",
    "machineUID": "muid",
    "uid": "muid",
}

MACH_ATTR_TO_YAML = {v: k for k, v in MACH_YAML_TO_ATTR.items()}


def mach_yaml_to_attr(field_name: str) -> str:
    """
    Converts a field name from a YAML file to an attribute name.

    Parameters:
        field_name (str): The field name from the YAML file.

    Raises:
        KeyError: If the field name is not found in the mapping.

    Returns:
        str: The corresponding attribute name.
    """
    if field_name not in MACH_YAML_TO_ATTR:
        raise KeyError(f"Unknown field: {field_name}. Add it to scope.py?")
    return MACH_YAML_TO_ATTR[field_name]


@dataclass
class MachineScope(BaseScope):
    """Attributes that are used to match with machine selectors."""

    hostname: str
    muid: str
    source_name: str


# -------------------------------------------------------------

CONT_YAML_TO_ATTR = {
    "image": "container_image",
    "imageID": "container_image_id",
    "containerName": "container_name",
    "containerID": "container_id",
}

CONT_ATTR_TO_YAML = {v: k for k, v in CONT_YAML_TO_ATTR.items()}


def cont_yaml_to_attr(field_name: str) -> str:
    """
    Converts a field name from a YAML file to an attribute name.

    Parameters:
        field_name (str): The field name from the YAML file.

    Raises:
        KeyError: If the field name is not found in the mapping.

    Returns:
        str: The corresponding attribute name.
    """
    if field_name not in CONT_YAML_TO_ATTR:
        raise KeyError(f"Unknown field: {field_name}. Add it to scope.py?")
    return CONT_YAML_TO_ATTR[field_name]


@dataclass
class ContainerScope(BaseScope):
    """Attributes that are used to match with container selectors."""

    container_image: str
    container_image_id: str
    container_name: str
    container_id: str


# -------------------------------------------------------------

LINUX_SVC_YAML_TO_ATTR = {
    "cgroup": "cgroup",
    "name": "service_name",
}

LINUX_SVC_ATTR_TO_YAML = {v: k for k, v in LINUX_SVC_YAML_TO_ATTR.items()}


def linux_svc_yaml_to_attr(field_name: str) -> str:
    """
    Converts a field name from a YAML file to an attribute name.

    Parameters:
        field_name (str): The field name from the YAML file.

    Raises:
        KeyError: If the field name is not found in the mapping.

    Returns:
        str: The corresponding attribute name.
    """
    if field_name not in LINUX_SVC_YAML_TO_ATTR:
        raise KeyError(f"Unknown field: {field_name}. Add it to scope.py?")
    return LINUX_SVC_YAML_TO_ATTR[field_name]


@dataclass
class LinuxServiceScope(BaseScope):
    """Attributes that are used to match with Linux service selectors."""

    cgroup: str
    service_name: str


# -------------------------------------------------------------

PROC_YAML_TO_ATTR = {
    "name": "name",
    "exe": "exe",
    "euser": "euser",
}

PROC_ATTR_TO_YAML = {v: k for k, v in PROC_YAML_TO_ATTR.items()}


def proc_yaml_to_attr(field_name: str) -> str:
    """
    Converts a field name from a YAML file to an attribute name.

    Parameters:
        field_name (str): The field name from the YAML file.

    Raises:
        KeyError: If the field name is not found in the mapping.

    Returns:
        str: The corresponding attribute name.
    """
    if field_name not in PROC_YAML_TO_ATTR:
        raise KeyError(f"Unknown field: {field_name}. Add it to scope.py?")
    return PROC_YAML_TO_ATTR[field_name]


@dataclass
class ProcessScope(BaseScope):
    """Attributes that are used to match with process selectors."""

    name: str
    exe: str
    euser: str


# -------------------------------------------------------------

TRACE_YAML_TO_ATTR = {
    "triggerClass": "trigger_class",
    "triggerAncestors": "trigger_ancestors",
}

TRACE_ATTR_TO_YAML = {v: k for k, v in TRACE_YAML_TO_ATTR.items()}


def trace_yaml_to_attr(field_name: str) -> str:
    """
    Converts a field name from a YAML file to an attribute name.

    Parameters:
        field_name (str): The field name from the YAML file.

    Raises:
        KeyError: If the field name is not found in the mapping.

    Returns:
        str: The corresponding attribute name.
    """
    if field_name not in TRACE_YAML_TO_ATTR:
        raise KeyError(f"Unknown field: {field_name}. Add it to scope.py?")
    return TRACE_YAML_TO_ATTR[field_name]


@dataclass
class TraceScope(BaseScope):
    """Attributes that are used to match with trace selectors."""

    trigger_ancestors: str
    trigger_class: str


# -------------------------------------------------------------

USER_YAML_TO_ATTR = {
    "users": "user",
    "interactiveUsers": "user",
    "nonInteractiveUsers": "user",
    "user": "user",  # Leave this one last
}

USER_ATTR_TO_YAML = {v: k for k, v in USER_YAML_TO_ATTR.items()}


def user_yaml_to_attr(field_name: str) -> str:
    """
    Converts a field name from a YAML file to an attribute name.

    Parameters:
        field_name (str): The field name from the YAML file.

    Raises:
        KeyError: If the field name is not found in the mapping.

    Returns:
        str: The corresponding attribute name.
    """
    if field_name not in USER_YAML_TO_ATTR:
        raise KeyError(f"Unknown field: {field_name}. Add it to scope.py?")
    return USER_YAML_TO_ATTR[field_name]


@dataclass
class UserScope(BaseScope):
    """Attributes that are used to match with user selectors."""

    user: str


# -------------------------------------------------------------

SCOPE_TYPE_TO_YAML_TO_ATTR = {
    ClusterScope: CLUS_YAML_TO_ATTR,
    ContainerScope: CONT_YAML_TO_ATTR,
    LinuxServiceScope: LINUX_SVC_YAML_TO_ATTR,
    MachineScope: MACH_YAML_TO_ATTR,
    NamespaceScope: NAMESPACE_YAML_TO_ATTR,
    PodScope: POD_YAML_TO_ATTR,
    ProcessScope: PROC_YAML_TO_ATTR,
    TraceScope: TRACE_YAML_TO_ATTR,
    UserScope: USER_YAML_TO_ATTR,
}


def get_yaml_fields(scope_type: type) -> dict:
    """
    Gets the map of yaml to attribute fields for a scope type.

    Parameters:
        scope_type (type): The scope type.

    Raises:
        KeyError: If the scope type is not found in the mapping.

    Returns:
        dict: The YAML fields for the scope type.
    """
    if scope_type not in SCOPE_TYPE_TO_YAML_TO_ATTR:
        raise KeyError(
            f"Unknown scope type: {scope_type}. Add it to scope.py?"
        )
    return SCOPE_TYPE_TO_YAML_TO_ATTR[scope_type]


SCOPE_TYPE_TO_ATTR_TO_YAML = {
    ClusterScope: CLUS_ATTR_TO_YAML,
    ContainerScope: CONT_ATTR_TO_YAML,
    LinuxServiceScope: LINUX_SVC_ATTR_TO_YAML,
    MachineScope: MACH_ATTR_TO_YAML,
    NamespaceScope: NAMESPACE_ATTR_TO_YAML,
    PodScope: POD_ATTR_TO_YAML,
    ProcessScope: PROC_ATTR_TO_YAML,
    TraceScope: TRACE_ATTR_TO_YAML,
    UserScope: USER_ATTR_TO_YAML,
}


def get_attr_fields(scope_type: type) -> dict:
    """
    Gets the map of attribute to yaml fields for a scope type.

    Parameters:
        scope_type (type): The scope type.

    Raises:
        KeyError: If the scope type is not found in the mapping.

    Returns:
        dict: The attribute fields for the scope type.
    """
    if scope_type not in SCOPE_TYPE_TO_ATTR_TO_YAML:
        raise KeyError(
            f"Unknown scope type: {scope_type}. Add it to scope.py?"
        )
    return SCOPE_TYPE_TO_ATTR_TO_YAML[scope_type]


def snake_to_camel_case(snake_str: str) -> str:
    """
    Converts a snake case string to camel case.

    Parameters:
        snake_str (str): The snake case string.

    Returns:
        str: The camel case string.
    """
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


SEL_FIELD_TO_SCOPE = {
    lib.CONT_SELECTOR_FIELD: ContainerScope,
    lib.CLUS_SELECTOR_FIELD: ClusterScope,
    lib.NAMESPACE_SELECTOR_FIELD: NamespaceScope,
    lib.POD_SELECTOR_FIELD: PodScope,
    lib.MACHINE_SELECTOR_FIELD: MachineScope,
    lib.SVC_SELECTOR_FIELD: LinuxServiceScope,
    lib.PROCESS_SELECTOR_FIELD: ProcessScope,
    lib.TRACE_SELECTOR_FIELD: TraceScope,
    lib.USER_SELECTOR_FIELD: UserScope,
}


def build_scopes(scopes: Dict[str, Dict]) -> Dict[str, BaseScope]:
    """
    Builds the scope objects from the provided scope data.

    Parameters:
        scopes (dict[str, dict]): The scope data.

    Returns:
        dict: The scope objects.
    """
    rv = {}
    for field, scope_data in scopes.items():
        scope_class = SEL_FIELD_TO_SCOPE[field]
        yaml_to_attr = get_yaml_fields(scope_class)
        scope_attrs = {}
        for yaml_field, value in scope_data.items():
            attr = yaml_to_attr[yaml_field]
            scope_attrs[attr] = value
        scope = scope_class(**scope_attrs)
        rv[field] = scope
    return rv
