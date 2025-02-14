"""Contains the get command group."""

import click

import spyctl.spyctl_lib as lib
from spyctl.commands.get import (
    agent_health,
    agents,
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


get.add_command(agents.get_agents, aliases=["agent"])
get.add_command(bash_cmds.get_bash_cmds_cmd, aliases=["bash-cmd"])
get.add_command(
    clusterrolebindings.get_clusterrolebindings_cmd,
    aliases=["cluster-role-binding"],
)
get.add_command(clusterroles.get_clusterroles_cmd, aliases=["clusterrole"])
get.add_command(clusters.get_clusters, aliases=["cluster"])
get.add_command(connection_bundles.get_conn_bun_cmd, aliases=["connbun"])
get.add_command(connections.get_connections_cmd, aliases=["connection"])
get.add_command(containers.get_containers_cmd, aliases=["container"])
get.add_command(custom_flags.get_custom_flags, aliases=["custom-flag"])
get.add_command(daemonsets.get_daemonsets_cmd, aliases=["daemonset", "ds"])
get.add_command(deployments.get_deployments_cmd, aliases=["deployment", "deploy"])
get.add_command(deviations.get_deviations_cmd, aliases=["deviation"])
get.add_command(fingerprints.get_fingerprints_cmd, aliases=["fingerprint"])
get.add_command(linux_svcs.get_linux_svc, aliases=["linux-svc"])
get.add_command(machines.get_machines_cmd, aliases=["machine"])
get.add_command(namespaces.get_namespaces_cmd, aliases=["namespace", "ns"])
get.add_command(nodes.get_nodes_cmd, aliases=["node"])
get.add_command(opsflags.get_opsflags_cmd, aliases=["ops-flag", "opsflag"])
get.add_command(pods.get_pods_cmd, aliases=["pod"])
get.add_command(policies.get_policies_cmd, aliases=["policy"])
get.add_command(processes.get_processes_cmd, aliases=["process"])
get.add_command(redflags.get_redflags_cmd, aliases=["red-flag", "redflag"])
get.add_command(replicasets.get_replicasets_cmd, aliases=["replicaset"])
get.add_command(rolebindings.get_rolebindings_cmd, aliases=["rolebinding"])
get.add_command(roles.get_roles_cmd, aliases=["role"])
get.add_command(rulesets.get_rulesets_cmd, aliases=["ruleset"])
get.add_command(saved_queries.get_saved_queries, aliases=["saved-query"])
get.add_command(sources.get_sources, aliases=["source"])
get.add_command(spydertraces.get_spydertraces_cmd, aliases=["spydertrace"])
get.add_command(top_data.get_top_data_cmd, aliases=["td"])
get.add_command(notification_targets.get_notification_targets, aliases=["ntar"])
get.add_command(notification_templates.get_notification_templates, aliases=["ntem"])
get.add_command(agent_health.get_agent_health_notification_settings, aliases=["ahns"])
