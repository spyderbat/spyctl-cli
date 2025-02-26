from typing import Dict, List

from tabulate import tabulate

import spyctl.spyctl_lib as lib


def agent_summary_output(agents: List[Dict], sources: Dict[str, Dict]) -> str:
    header = ["NAME", "ID", "HEALTH", "ACTIVE BATS", "AGENT_VERSION"]
    data = []
    for agent in agents:
        data.append(agent_summary_data(agent, sources))
    data.sort(key=lambda line: (calc_health_priority(line[2]), line[0]))
    return tabulate(data, header, tablefmt="plain")


def agent_summary_data(agent: Dict, sources: Dict[str, Dict]) -> List:
    active_bats = calc_active_bats(agent)
    source_name = sources.get(agent["muid"], {}).get("name")
    rv = [
        source_name or agent["hostname"],
        agent["id"],
        agent["status"],
        active_bats,
        agent["agent_version"],
    ]
    return rv


def agents_output_wide(
    agents: List[Dict],
    source_data: Dict[str, Dict],
) -> None:
    header = [
        "NAME",
        "ID",
        "HEALTH",
        "ACTIVE BATS",
        "AGENT VERSION",
        "CLUSTER",
        "CLOUD REGION",
        "CLOUD TYPE",
    ]
    data = []
    for agent in agents:
        data.append(agent_output_wide_data(agent, source_data))
    data.sort(key=lambda line: (calc_health_priority(line[2]), line[0]))
    return tabulate(data, header, tablefmt="plain")


def agent_output_wide_data(agent: Dict, source_data: Dict[str, Dict]) -> List:
    active_bats = calc_active_bats(agent)
    source_name = source_data.get(agent["muid"], {}).get("name")
    rv = [
        source_name or agent["hostname"],
        agent["id"],
        agent["status"],
        active_bats,
        agent["agent_version"],
        agent.get("cluster_name") or lib.NOT_AVAILABLE,
    ]
    muid = agent["muid"]
    source = source_data.get(muid)
    if source:
        rv.extend(
            [
                source["cloud_region"],
                source["cloud_type"],
            ]
        )
    else:
        rv.extend([lib.NOT_AVAILABLE, lib.NOT_AVAILABLE, lib.NOT_AVAILABLE])
    return rv


def calc_active_bats(agent: Dict):
    bat_statuses = agent.get(lib.AGENT_BAT_STATUSES, {})
    total = len(bat_statuses)
    active = 0
    for status in bat_statuses.values():
        if status.get("running", False) is True:
            active += 1
    return f"{active}/{total}"


def calc_health_priority(status):
    return lib.HEALTH_PRIORITY.get(status, 0)
