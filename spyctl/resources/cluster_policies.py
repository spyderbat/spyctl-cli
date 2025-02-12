"""
Contains the ClusterPolicy class, which is used to define a policy for a
kubernetes cluster.
"""

from typing import Dict, List

import spyctl.resources.cluster_rulesets as crs
import spyctl.resources.clusters as c
import spyctl.schemas_v2 as schemas
import spyctl.spyctl_lib as lib


def create_cluster_policy(
    name: str,
    mode: str,
    st: float,
    et: float,
    no_rs_gen: bool,
    clusters: List[str] = None,
    namespace: List[str] = None,
) -> Dict:
    """
    Create a cluster policy and output it to stdout in the desired format.

    Args:
        name (str): The name of the cluster policy.
        mode (str): The mode of the cluster policy.
        st (str): The start time of the cluster policy.
        et (str): The end time of the cluster policy.
        no_rs_gen (bool): Whether or not to generate rulesets.
        cluster (str, optional): The cluster name. Defaults to None.
        namespace (List[str], optional): Scope ruleset rules to namespace(s).
    """
    metadata = schemas.GuardianMetadataModel(name=name, type=lib.POL_TYPE_CLUS)
    rulesets: List[crs.ClusterRuleset] = []
    spec = schemas.ClusterPolicySpecModel(
        clusterSelector=schemas.ClusterSelectorModel(
            matchFields={
                "name": "PROVIDE_CLUSTER_NAME",
            }
        ),
        mode=mode,
        enabled=True,
        rulesets=[],
        response=schemas.GuardianResponseModel(**lib.RESPONSE_ACTION_TEMPLATE),
    )
    if clusters:
        __add_cluster_selector(clusters, spec)
        rulesets = __build_rulesets(clusters, no_rs_gen, st, et, namespace)
    policy = schemas.ClusterPolicyModel(
        apiVersion=lib.API_VERSION,
        kind=lib.POL_KIND,
        metadata=metadata,
        spec=spec,
    )
    if not rulesets:
        rv = policy.model_dump(by_alias=True, exclude_unset=True)
    else:
        items = []
        for ruleset in rulesets:
            rs_name = ruleset.name
            spec.rulesets.append(rs_name)
            items.append(ruleset.as_dict())
        pol_dict = policy.model_dump(by_alias=True, exclude_unset=True)
        items.append(pol_dict)
        rv = {
            lib.API_FIELD: lib.API_VERSION,
            lib.ITEMS_FIELD: items,
        }
    return rv


def __add_cluster_selector(clusters: List[str], spec: schemas.ClusterPolicySpecModel):
    if len(clusters) == 1:
        key = "uid" if clusters[0].startswith("clus:") else "name"
        spec.cluster_selector.match_fields = {
            key: clusters[0],
        }
    else:
        exprs: Dict[str, schemas.SelectorExpression] = {}
        for clus in clusters:
            key = "uid" if clus.startswith("clus:") else "name"
            if key not in exprs:
                exprs[key] = schemas.SelectorExpression(
                    key=key, operator=lib.IN_OPERATOR, values=[clus]
                )
            else:
                exprs[key].values.append(clus)


def __build_rulesets(
    clusters: List,
    no_rs_gen: bool,
    st: float,
    et: float,
    namespace: List,
) -> List[crs.ClusterRuleset]:
    rulesets = []
    lib.try_log("Validating cluster(s) exist within the system.")
    for clus in clusters:
        if not c.cluster_exists(clus):
            lib.err_exit(f"Cluster {clus} does not exist")
        if no_rs_gen:
            continue
        filters = {
            "cluster": clus,
        }
        if namespace:
            filters["namespace"] = namespace
        lib.try_log(f"Creating ruleset for cluster {clus}")
        rulesets.append(
            crs.create_ruleset(f"{clus}_ruleset", True, (st, et), **filters)
        )
    lib.try_log("Cluster(s) validated... creating policy.")
    return rulesets
