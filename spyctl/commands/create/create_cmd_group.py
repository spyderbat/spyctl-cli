"""Handles the create subcommand group for spyctl."""

import time
from typing import IO, Dict, List, Tuple

import click

import spyctl.config.configs as cfg
import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl import cli
from spyctl.api.api_testing import (
    api_create_guardian_policy,
)
from spyctl.commands.create import (
    agent_health,
    cluster_policy,
    container_policy,
    container_ruleset,
    custom_flag,
    linux_svc_policy,
    notification_target,
    notification_template,
    saved_query,
    trace_suppression_policy,
)

# ----------------------------------------------------------------- #
#                         Create Subcommand                         #
# ----------------------------------------------------------------- #


@click.group("create", cls=lib.CustomSubGroup, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
def create():
    """Create a resource from a file."""


create.add_command(cluster_policy.create_cluster_policy)
create.add_command(container_policy.create_container_policy)
create.add_command(container_ruleset.create_container_ruleset)
create.add_command(linux_svc_policy.create_service_policy)
create.add_command(saved_query.create_saved_query)
create.add_command(trace_suppression_policy.create_trace_suppression_policy)
create.add_command(custom_flag.create_custom_flag)
create.add_command(notification_target.notification_target)
create.add_command(notification_template.notification_template)
create.add_command(agent_health.create_agent_health_notification_settings)


@create.command("notification-config", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
@click.option("-n", "--name", help="A name for the config.", metavar="", required=True)
@click.option(
    "-T",
    "--target",
    help="The name or ID of a notification target. Tells the config where to"
    " send notifications.",
    metavar="",
    required=True,
)
@click.option(
    "-P",
    "--template",
    help="The name or ID of a notification configuration template."
    " If omitted, the config will be completely custom.",
    metavar="",
    default="CUSTOM",
)
@click.option(
    "-o",
    "--output",
    default=lib.OUTPUT_DEFAULT,
    type=click.Choice(lib.OUTPUT_CHOICES, case_sensitive=False),
)
def create_notif_route(name, target, template, output):
    """Create a Notification Config resource outputted to stdout."""
    handle_create_notif_config(name, target, template, output)


@create.command("policy", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
@click.option(
    "-f",
    "--from-file",
    "filename",
    help="File that contains to merge into a SpyderbatPolicy.",
    metavar="",
    required=True,
    type=click.File(),
)
@click.option(
    "-o",
    "--output",
    default=lib.OUTPUT_DEFAULT,
    type=click.Choice(lib.OUTPUT_CHOICES, case_sensitive=False),
)
@click.option(
    "-n",
    "--name",
    help="Optional name for the SpyderbatPolicy, if not provided, a name will"
    " be generated automatically",
    metavar="",
)
@click.option(
    "-d",
    "--disable-processes",
    "disable_procs",
    type=click.Choice(lib.DISABLE_PROCS_STRINGS),
    metavar="",
    hidden=False,
    help="Disable processes detections for this policy. Disabling all "
    "processes detections effectively turns this into a network policy.",
)
@click.option(
    "-D",
    "--disable-connections",
    "disable_conns",
    type=click.Choice(lib.DISABLE_CONN_OPTIONS_STRINGS),
    metavar="",
    help="Disable detections for all, public, or private connections.",
    hidden=False,
)
@click.option(
    "--include-imageid",
    help="Include the image id in the container selector when creating the" " policy.",
    metavar="",
    is_flag=True,
)
@click.option(
    "-m",
    "--mode",
    type=click.Choice(lib.POL_MODES),
    default=lib.POL_MODE_AUDIT,
    metavar="",
    help="This determines what the policy should do when applied and enabled."
    " Default is audit mode. Audit mode will generate log messages when a"
    " violation occurs and when it would have taken an action, but it will not"
    " actually take an action or generate a violation flag. Enforce mode"
    " will take actions, generate flags, and also generate audit events.",
    hidden=False,
)
@click.option(
    "-a",
    "--api",
    "use_api",
    metavar="",
    default=False,
    hidden=True,
    is_flag=True,
)
@lib.colorization_option
def create_policy(
    filename,
    output,
    name,
    colorize,
    mode,
    disable_procs,
    disable_conns,
    use_api,
    include_imageid,
):
    """Create a Guardian Policy object from a file, outputted to stdout"""
    if not colorize:
        lib.disable_colorization()
    handle_create_guardian_policy(
        filename,
        output,
        name,
        mode,
        disable_procs,
        disable_conns,
        use_api,
        include_imageid,
    )


@create.command("cluster-ruleset", cls=lib.CustomCommand, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
@click.option(
    "-o",
    "--output",
    default=lib.OUTPUT_DEFAULT,
    type=click.Choice(lib.OUTPUT_CHOICES, case_sensitive=False),
)
@click.option(
    "-n",
    "--name",
    help="Optional name for the Cluster Ruleset, if not provided, a name will"
    " be generated automatically",
    metavar="",
)
@click.option(
    "-g",
    "--generate-rules",
    help="Generate all or some types of rules for the policy ruleset.",
    metavar="",
    is_flag=True,
)
@click.option(
    "-t",
    "--start-time",
    "st",
    help="Time to start generating statements from. Default is 1.5 hours ago.",
    default="1.5h",
    metavar="",
    type=lib.time_inp,
)
@click.option(
    "-e",
    "--end-time",
    "et",
    help="Time to stop generating statements from. Default is now.",
    default=time.time(),
    metavar="",
    type=lib.time_inp,
)
@click.option(
    "-C",
    "--cluster",
    help="Name or Spyderbat ID of Kubernetes cluster.",
    metavar="",
)
@click.option(
    "-N",
    "--namespace",
    is_flag=False,
    flag_value="__all__",
    default=None,
    metavar="",
    type=lib.ListParam(),
    help="Generate ruleset for all or some namespaces. If not provided, the"
    " ruleset will be generated for the cluster without namespace"
    " context. Supplying this option with no arguments will generate the"
    " ruleset with namespace context. If one or more namespaces are supplied,"
    " the ruleset will generate for only the namespace(s) provided.",
)
def create_policy_ruleset(output, name, generate_rules, st, et, **filters):
    """Create a Policy Rule to be used in cluster policies."""
    filters = {key: value for key, value in filters.items() if value is not None}
    handle_create_cluster_ruleset(output, name, generate_rules, (st, et), **filters)


# ----------------------------------------------------------------- #
#                         Create Handlers                           #
# ----------------------------------------------------------------- #


def handle_create_guardian_policy(
    file: IO,
    output: str,
    name: str,
    mode: str,
    disable_procs: str,
    disable_conns: str,
    do_api=False,
    include_imageid=False,
):
    """
    Handles the creation of a guardian policy.

    Args:
        file (IO): The input file containing the policy data.
        output (str): The desired output format for displaying the policy.
        name (str): The name of the policy.
        mode (str): The mode of the policy.
        disable_procs (str): The flag indicating whether to disable processes.
        disable_conns (str): The flag indicating whether to disable
            connections.
        do_api (bool, optional): Flag indicating whether to use the API for
            policy creation. Defaults to False.

    Returns:
        None
    """
    if do_api:
        ctx = cfg.get_current_context()
        resrc_data = lib.load_file_for_api_test(file)
        policy = api_create_guardian_policy(*ctx.get_api_data(), name, mode, resrc_data)
        cli.show(policy, lib.OUTPUT_RAW)
    else:
        policy = create_guardian_policy_from_file(
            file, name, mode, disable_procs, disable_conns, include_imageid
        )
        if output == lib.OUTPUT_DEFAULT:
            output = lib.OUTPUT_YAML
        cli.show(policy, output)


def create_guardian_policy_from_file(
    file: IO,
    name: str,
    mode: str,
    disable_procs: str,
    disable_conns: str,
    include_imageid: bool = False,
):
    """
    Create a Guardian policy from a file.

    Args:
        file (IO): The file object containing the resource data.
        name (str): The name of the policy.
        mode (str): The mode of the policy.
        disable_procs (str): The processes to disable.
        disable_conns (str): The connections to disable.

    Returns:
        policy: The created Guardian policy.
    """
    resrc_data = lib.load_resource_file(file)
    policy = _r.policies.create_policy(
        resrc_data,
        name=name,
        mode=mode,
        disable_procs=disable_procs,
        disable_conns=disable_conns,
        include_imageid=include_imageid,
    )
    return policy


def create_guardian_policy_from_json(
    name: str,
    mode: str,
    input_objects: List[Dict],
    ctx: cfg.Context,
    include_imageid: bool = False,
):
    """
    Create a Guardian policy from JSON.

    Args:
        name (str): The name of the policy.
        mode (str): The mode of the policy.
        input_objects (List[Dict]): A list of input objects in JSON format.
        ctx (cfg.Context): The context for the policy.

    Returns:
        The created Guardian policy.
    """
    policy = _r.policies.create_policy(
        input_objects,
        mode=mode,
        name=name,
        ctx=ctx,
        include_imageid=include_imageid,
    )
    return policy


def handle_create_cluster_ruleset(
    output: str,
    name: str,
    generate_rules: bool,
    time_tup: Tuple[float, float],
    **filters,
):
    """
    Create a cluster ruleset with the given parameters.

    Args:
        output (str): The output format for the ruleset.
        name (str): The name of the ruleset.
        generate_rules (bool): Whether to generate rules for the ruleset.
        time_tup (Tuple[float, float]): A tuple representing the time range
            for the ruleset.
        **filters: Additional filters to be applied to the ruleset.

    Returns:
        None
    """
    ruleset = _r.cluster_rulesets.create_ruleset(
        name, generate_rules, time_tup, **filters
    )
    if output == lib.OUTPUT_DEFAULT:
        output = lib.OUTPUT_YAML
    cli.show(ruleset.as_dict(), output)


def handle_create_notif_config(name: str, target: str, template: str, output: str):
    """
    Create a notification configuration.

    Args:
        name (str): The name of the configuration.
        target (str): The target of the configuration.
        template (str): The template to use for the configuration.
        output (str): The output format for displaying the configuration.

    Returns:
        None
    """
    config = _r.notification_configs.create_config(name, target, template)
    if output == lib.OUTPUT_DEFAULT:
        output = lib.OUTPUT_YAML
    cli.show(config, output)
