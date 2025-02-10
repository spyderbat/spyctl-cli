"""Contains the get command group."""

import click

import spyctl.spyctl_lib as lib
from spyctl.commands.get import (
    agents,
    agent_health,
    bash_cmds,
    clusterrolebindings,
    clusterroles,
    clusters,
    connection_bundles,
    connections,
    containers,
    custom_flags,
    daemonsets,
    deployments,
    deviations,
    fingerprints,
    linux_svcs,
    machines,
    namespaces,
    nodes,
    notification_targets,
    notification_templates,
    opsflags,
    pods,
    policies,
    processes,
    redflags,
    replicasets,
    rolebindings,
    roles,
    rulesets,
    saved_queries,
    sources,
    spydertraces,
    top_data,
)


@click.group("get", cls=lib.CustomSubGroup, epilog=lib.SUB_EPILOG)
@click.help_option("-h", "--help", hidden=True)
def get():
    """Get Spyderbat Resources."""


get.add_command(agents.get_agents)
get.add_command(bash_cmds.get_bash_cmds_cmd)
get.add_command(clusterrolebindings.get_clusterrolebindings_cmd)
get.add_command(clusterroles.get_clusterroles_cmd)
get.add_command(clusters.get_clusters)
get.add_command(connection_bundles.get_conn_bun_cmd)
get.add_command(connections.get_connections_cmd)
get.add_command(containers.get_containers_cmd)
get.add_command(custom_flags.get_custom_flags)
get.add_command(daemonsets.get_daemonsets_cmd)
get.add_command(deployments.get_deployments_cmd)
get.add_command(deviations.get_deviations_cmd)
get.add_command(fingerprints.get_fingerprints_cmd)
get.add_command(linux_svcs.get_linux_svc)
get.add_command(machines.get_machines_cmd)
get.add_command(namespaces.get_namespaces_cmd)
get.add_command(nodes.get_nodes_cmd)
get.add_command(opsflags.get_opsflags_cmd)
get.add_command(pods.get_pods_cmd)
get.add_command(policies.get_policies_cmd)
get.add_command(processes.get_processes_cmd)
get.add_command(redflags.get_redflags_cmd)
get.add_command(replicasets.get_replicasets_cmd)
get.add_command(rolebindings.get_rolebindings_cmd)
get.add_command(roles.get_roles_cmd)
get.add_command(rulesets.get_rulesets_cmd)
get.add_command(saved_queries.get_saved_queries)
get.add_command(sources.get_sources)
get.add_command(spydertraces.get_spydertraces_cmd)
get.add_command(top_data.get_top_data_cmd)
get.add_command(notification_targets.get_notification_targets)
get.add_command(notification_templates.get_notification_templates)
get.add_command(agent_health.get_agent_health_notification_settings)
