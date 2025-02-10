"""Handles the create cluster-policy command"""

import time
from typing import List

import click

import spyctl.resources as _r
import spyctl.spyctl_lib as lib
from spyctl import cli


@click.command(
    "cluster-policy",
    cls=lib.CustomCommand,
    epilog=lib.SUB_EPILOG,
)
@click.help_option("-h", "--help", hidden=True)
@click.option(
    "-n",
    "--name",
    help="Name for the Cluster Policy.",
    metavar="",
    required=True,
)
@click.option(
    "-o",
    "--output",
    default=lib.OUTPUT_DEFAULT,
    type=click.Choice(lib.OUTPUT_CHOICES, case_sensitive=False),
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
    "-g",
    "--no-ruleset-gen",
    "no_rs_gen",
    help="Does not generate rulesets for the cluster policies if set.",
    metavar="",
    is_flag=True,
)
@click.option(
    "-C",
    "--cluster",
    help="Name or Spyderbat ID of Kubernetes cluster.",
    metavar="",
    type=lib.ListParam(),
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
    " ruleset will be generated for the cluster(s) without namespace"
    " context. Supplying this option with no arguments will generate the"
    " ruleset with namespace context. If one or more namespaces are supplied,"
    " the ruleset will generate for only the namespace(s) provided.",
)
def create_cluster_policy(
    name, output, mode, st, et, no_rs_gen, cluster, namespace
):
    """
    Create a Cluster Policy yaml document and accompanying rulesets, outputted to stdout  # noqa
    """
    handle_create_cluster_policy(
        name, mode, output, st, et, no_rs_gen, cluster, namespace
    )


def handle_create_cluster_policy(
    name: str,
    mode: str,
    output: str,
    st: float,
    et: float,
    no_rs_gen: bool,
    cluster: str = None,
    namespace: List[str] = None,
):
    """
    Handles the creation of a cluster policy.

    Args:
        name (str): The name of the cluster policy.
        mode (str): The mode of the cluster policy.
        output (str): The output format of the policy.
        st (float): The start time to gather data for the policy rulesets.
        et (float): The end time to gather data for the policy rulesets.
        no_rs_gen (bool): Flag indicating whether to generate ruleset(s) for
            the policy.
        cluster (str, optional): The cluster to apply the policy to.
            Defaults to None.
        namespace (List[str], optional): The namespaces to apply the policy to.
            Defaults to None.
    """
    policy = _r.cluster_policies.create_cluster_policy(
        name, mode, st, et, no_rs_gen, cluster, namespace
    )
    if output == lib.OUTPUT_DEFAULT:
        output = lib.OUTPUT_YAML
    cli.show(policy, output)
