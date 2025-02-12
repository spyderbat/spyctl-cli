"""Test the merge logic for ruleset policies."""

# pylint: disable=redefined-outer-name, missing-function-docstring

from typing import Dict
from unittest import mock

import pytest

import spyctl.merge_lib.merge_object_helper as _moh
import spyctl.merge_lib.ruleset_merge_object as _rmo
import spyctl.schemas_v2 as schemas
import spyctl.spyctl_lib as lib
from spyctl.config import configs, secrets
from spyctl.tests.backups import backup_context, restore_context


def test_default_deny_merge(
    ruleset_policy_merge_object: _rmo.RulesetPolicyMergeObject, deviation_1
):
    mo = ruleset_policy_merge_object
    mo.asymmetric_merge(deviation_1)
    assert any(
        d[lib.RULE_TARGET_FIELD] == "container::image"
        and d[lib.RULE_VERB_FIELD] == lib.RULE_VERB_ALLOW
        and "docker.io/mongo" in d[lib.RULE_VALUES_FIELD]
        for d in mo.ruleset_trackers["test_ruleset_1"].rules_map.values()
    )


def test_default_deny_merge_2(
    ruleset_policy_merge_object: _rmo.RulesetPolicyMergeObject, deviation_2
):
    """Second ruleset has imageID target, not first"""
    mo = ruleset_policy_merge_object
    mo.asymmetric_merge(deviation_2)
    assert any(
        d[lib.RULE_TARGET_FIELD] == "container::imageID"
        and d[lib.RULE_VERB_FIELD] == lib.RULE_VERB_ALLOW
        and "sha256@foo123baz" in d[lib.RULE_VALUES_FIELD]
        for d in mo.ruleset_trackers["test_ruleset_2"].rules_map.values()
    )


def test_default_deny_merge_3(
    ruleset_policy_merge_object: _rmo.RulesetPolicyMergeObject, deviation_3
):
    """No ruleset with this target"""
    mo = ruleset_policy_merge_object
    mo.asymmetric_merge(deviation_3)
    new_rule = {
        lib.RULE_TARGET_FIELD: "container::containerName",
        lib.RULE_VERB_FIELD: lib.RULE_VERB_ALLOW,
        lib.RULE_VALUES_FIELD: ["my_test_container"],
    }
    assert new_rule in mo.ruleset_trackers["test_ruleset_1"].rules_map.values()


def test_explicit_deny_global_scope(
    ruleset_policy_merge_object: _rmo.RulesetPolicyMergeObject, deviation_4
):
    mo = ruleset_policy_merge_object
    mo.asymmetric_merge(deviation_4)
    del_rule = {
        lib.RULE_TARGET_FIELD: "container::image",
        lib.RULE_VERB_FIELD: lib.RULE_VERB_DENY,
        lib.RULE_VALUES_FIELD: ["docker.io/bad-image"],
    }
    assert del_rule not in mo.ruleset_trackers["test_ruleset_1"].rules_map.values()
    assert any(
        d[lib.RULE_TARGET_FIELD] == "container::image"
        and d[lib.RULE_VERB_FIELD] == lib.RULE_VERB_ALLOW
        and "docker.io/bad-image" in d[lib.RULE_VALUES_FIELD]
        for d in mo.ruleset_trackers["test_ruleset_1"].rules_map.values()
    )


def test_explicit_deny_scoped(
    ruleset_policy_merge_object: _rmo.RulesetPolicyMergeObject, deviation_5
):
    mo = ruleset_policy_merge_object
    mo.asymmetric_merge(deviation_5)
    keep_rule = {
        lib.RULE_TARGET_FIELD: "container::image",
        lib.RULE_VERB_FIELD: lib.RULE_VERB_DENY,
        lib.RULE_VALUES_FIELD: ["docker.io/bad-image"],
    }
    del_rule = {
        lib.NAMESPACE_SELECTOR_FIELD: {
            lib.MATCH_LABELS_FIELD: {
                "kubernetes.io/namespace": "bad_image_ns",
            },
        },
        lib.RULE_TARGET_FIELD: "container::image",
        lib.RULE_VERB_FIELD: lib.RULE_VERB_DENY,
        lib.RULE_VALUES_FIELD: ["docker.io/bad-image"],
    }
    add_rule = {
        lib.NAMESPACE_SELECTOR_FIELD: {
            lib.MATCH_LABELS_FIELD: {
                "kubernetes.io/namespace": "bad_image_ns",
            },
        },
        lib.RULE_TARGET_FIELD: "container::image",
        lib.RULE_VERB_FIELD: lib.RULE_VERB_ALLOW,
        lib.RULE_VALUES_FIELD: ["docker.io/bad-image"],
    }
    assert keep_rule in mo.ruleset_trackers["test_ruleset_1"].rules_map.values()
    assert del_rule not in mo.ruleset_trackers["test_ruleset_1"].rules_map.values()
    assert add_rule in mo.ruleset_trackers["test_ruleset_1"].rules_map.values()


def test_explicit_deny_with_explicit_allow(
    ruleset_policy_merge_object: _rmo.RulesetPolicyMergeObject, deviation_6
):
    mo = ruleset_policy_merge_object
    mo.asymmetric_merge(deviation_6)
    del_rule = {
        lib.RULE_TARGET_FIELD: "container::image",
        lib.RULE_VERB_FIELD: lib.RULE_VERB_DENY,
        lib.RULE_VALUES_FIELD: ["docker.io/nginx"],
    }
    add_rule = {
        lib.RULE_TARGET_FIELD: "container::image",
        lib.RULE_VERB_FIELD: lib.RULE_VERB_ALLOW,
        lib.RULE_VALUES_FIELD: ["docker.io/nginx"],
    }
    assert del_rule not in mo.ruleset_trackers["test_ruleset_3"].rules_map.values()
    assert add_rule in mo.ruleset_trackers["test_ruleset_1"].rules_map.values()


def test_explicit_deny_with_explicit_allow_2(
    ruleset_policy_merge_object: _rmo.RulesetPolicyMergeObject, deviation_7
):
    mo = ruleset_policy_merge_object
    mo.asymmetric_merge(deviation_7)
    del_rule = {
        lib.NAMESPACE_SELECTOR_FIELD: {
            lib.MATCH_LABELS_FIELD: {
                "app": "mysql",
            },
        },
        lib.RULE_TARGET_FIELD: "container::image",
        lib.RULE_VERB_FIELD: lib.RULE_VERB_DENY,
        lib.RULE_VALUES_FIELD: ["docker.io/mysql"],
    }
    add_rule = {
        lib.NAMESPACE_SELECTOR_FIELD: {
            lib.MATCH_LABELS_FIELD: {
                "app": "mysql",
            },
        },
        lib.RULE_TARGET_FIELD: "container::image",
        lib.RULE_VERB_FIELD: lib.RULE_VERB_ALLOW,
        lib.RULE_VALUES_FIELD: ["docker.io/mysql"],
    }
    assert del_rule not in mo.ruleset_trackers["test_ruleset_3"].rules_map.values()
    assert add_rule in mo.ruleset_trackers["test_ruleset_3"].rules_map.values()


def test_explicit_deny_with_explicit_allow_3(
    ruleset_policy_merge_object: _rmo.RulesetPolicyMergeObject, deviation_8
):
    mo = ruleset_policy_merge_object
    mo.asymmetric_merge(deviation_8)
    del_rule = {
        lib.NAMESPACE_SELECTOR_FIELD: {
            lib.MATCH_LABELS_FIELD: {
                "app": "python",
            },
        },
        lib.RULE_TARGET_FIELD: "container::image",
        lib.RULE_VERB_FIELD: lib.RULE_VERB_DENY,
        lib.RULE_VALUES_FIELD: ["docker.io/python"],
    }
    add_rule = {
        lib.NAMESPACE_SELECTOR_FIELD: {
            lib.MATCH_LABELS_FIELD: {
                "app": "python",
            },
        },
        lib.RULE_TARGET_FIELD: "container::image",
        lib.RULE_VERB_FIELD: lib.RULE_VERB_ALLOW,
        lib.RULE_VALUES_FIELD: ["docker.io/not-python", "docker.io/python"],
    }
    keep_rule = {
        lib.NAMESPACE_SELECTOR_FIELD: {
            lib.MATCH_LABELS_FIELD: {
                "app": "python",
            },
        },
        lib.RULE_TARGET_FIELD: "container::image",
        lib.RULE_VERB_FIELD: lib.RULE_VERB_DENY,
        lib.RULE_VALUES_FIELD: ["docker.io/keep-me", "docker.io/pyth*n"],
    }
    assert del_rule not in mo.ruleset_trackers["test_ruleset_3"].rules_map.values()
    assert add_rule in mo.ruleset_trackers["test_ruleset_3"].rules_map.values()
    assert keep_rule in mo.ruleset_trackers["test_ruleset_3"].rules_map.values()


@pytest.fixture
def ruleset_policy_merge_object(cluster_pol_1: Dict):
    def get_rulesets(*_args, **_kwargs):
        return [CLUSTER_RULESET_1, CLUSTER_RULESET_2, CLUSTER_RULESET_3]

    with mock.patch("spyctl.merge_lib.ruleset_merge_object.get_rulesets", get_rulesets):
        mo = _moh.get_merge_object(lib.POL_KIND, cluster_pol_1, True, "merge")
        assert isinstance(mo, _rmo.RulesetPolicyMergeObject)
    return mo


@pytest.fixture
def cluster_pol_1():
    cluster_policy = {
        lib.API_FIELD: lib.API_VERSION,
        lib.KIND_FIELD: lib.POL_KIND,
        lib.METADATA_FIELD: {
            lib.METADATA_NAME_FIELD: "test",
            lib.METADATA_TYPE_FIELD: lib.POL_TYPE_CLUS,
            lib.METADATA_UID_FIELD: "pol:1",
        },
        lib.SPEC_FIELD: {
            lib.ENABLED_FIELD: True,
            lib.POL_MODE_FIELD: lib.POL_MODE_ENFORCE,
            lib.CLUS_SELECTOR_FIELD: {
                lib.MATCH_FIELDS_FIELD: {
                    lib.NAME_FIELD: "clus1",
                }
            },
            lib.RULESETS_FIELD: [
                "test_ruleset_1",
                "test_ruleset_2",
                "test_ruleset_2",
            ],
            lib.RESPONSE_FIELD: {
                lib.RESP_DEFAULT_FIELD: [
                    {
                        lib.ACTION_MAKE_REDFLAG: {
                            lib.RESP_SEVERITY_FIELD: "high",
                        }
                    }
                ],
                lib.RESP_ACTIONS_FIELD: [],
            },
        },
    }
    assert schemas.valid_object(cluster_policy)
    return cluster_policy


CLUSTER_RULESET_1 = {
    lib.API_FIELD: lib.API_VERSION,
    lib.KIND_FIELD: lib.RULESET_KIND,
    lib.METADATA_FIELD: {
        lib.METADATA_NAME_FIELD: "test_ruleset_1",
        lib.METADATA_TYPE_FIELD: lib.RULESET_TYPE_CLUS,
        lib.METADATA_UID_FIELD: "rs:1",
    },
    lib.SPEC_FIELD: {
        lib.RULES_FIELD: [
            {
                lib.RULE_TARGET_FIELD: "container::image",
                lib.RULE_VERB_FIELD: lib.RULE_VERB_ALLOW,
                lib.RULE_VALUES_FIELD: ["docker.io/nginx"],
            },
            {
                lib.NAMESPACE_SELECTOR_FIELD: {
                    lib.MATCH_LABELS_FIELD: {
                        "app": "nginx",
                    },
                },
                lib.RULE_TARGET_FIELD: "container::image",
                lib.RULE_VERB_FIELD: lib.RULE_VERB_ALLOW,
                lib.RULE_VALUES_FIELD: ["docker.io/apache"],
            },
            {
                lib.RULE_TARGET_FIELD: "container::image",
                lib.RULE_VERB_FIELD: lib.RULE_VERB_DENY,
                lib.RULE_VALUES_FIELD: ["docker.io/bad-image"],
            },
            {
                lib.NAMESPACE_SELECTOR_FIELD: {
                    lib.MATCH_LABELS_FIELD: {
                        "kubernetes.io/namespace": "bad_image_ns",
                    },
                },
                lib.RULE_TARGET_FIELD: "container::image",
                lib.RULE_VERB_FIELD: lib.RULE_VERB_DENY,
                lib.RULE_VALUES_FIELD: ["docker.io/bad-image"],
            },
        ],
    },
}


CLUSTER_RULESET_2 = {
    lib.API_FIELD: lib.API_VERSION,
    lib.KIND_FIELD: lib.RULESET_KIND,
    lib.METADATA_FIELD: {
        lib.METADATA_NAME_FIELD: "test_ruleset_2",
        lib.METADATA_TYPE_FIELD: lib.RULESET_TYPE_CLUS,
        lib.METADATA_UID_FIELD: "rs:1",
    },
    lib.SPEC_FIELD: {
        lib.RULES_FIELD: [
            {
                lib.RULE_TARGET_FIELD: "container::imageID",
                lib.RULE_VERB_FIELD: lib.RULE_VERB_ALLOW,
                lib.RULE_VALUES_FIELD: ["sha256@1234"],
            },
            {
                lib.NAMESPACE_SELECTOR_FIELD: {
                    lib.MATCH_LABELS_FIELD: {
                        "app": "nginx",
                    },
                },
                lib.RULE_TARGET_FIELD: "container::imageID",
                lib.RULE_VERB_FIELD: lib.RULE_VERB_ALLOW,
                lib.RULE_VALUES_FIELD: ["sha256@4321"],
            },
        ],
    },
}

CLUSTER_RULESET_3 = {
    lib.API_FIELD: lib.API_VERSION,
    lib.KIND_FIELD: lib.RULESET_KIND,
    lib.METADATA_FIELD: {
        lib.METADATA_NAME_FIELD: "test_ruleset_3",
        lib.METADATA_TYPE_FIELD: lib.RULESET_TYPE_CLUS,
        lib.METADATA_UID_FIELD: "rs:1",
    },
    lib.SPEC_FIELD: {
        lib.RULES_FIELD: [
            {
                lib.RULE_TARGET_FIELD: "container::image",
                lib.RULE_VERB_FIELD: lib.RULE_VERB_DENY,
                lib.RULE_VALUES_FIELD: ["docker.io/nginx"],
            },
            {
                lib.NAMESPACE_SELECTOR_FIELD: {
                    lib.MATCH_LABELS_FIELD: {
                        "app": "mysql",
                    },
                },
                lib.RULE_TARGET_FIELD: "container::image",
                lib.RULE_VERB_FIELD: lib.RULE_VERB_DENY,
                lib.RULE_VALUES_FIELD: ["docker.io/mysql"],
            },
            {
                lib.RULE_TARGET_FIELD: "container::image",
                lib.RULE_VERB_FIELD: lib.RULE_VERB_ALLOW,
                lib.RULE_VALUES_FIELD: ["docker.io/mysql"],
            },
            {
                lib.NAMESPACE_SELECTOR_FIELD: {
                    lib.MATCH_LABELS_FIELD: {
                        "app": "python",
                    },
                },
                lib.RULE_TARGET_FIELD: "container::image",
                lib.RULE_VERB_FIELD: lib.RULE_VERB_DENY,
                lib.RULE_VALUES_FIELD: [
                    "docker.io/keep-me",
                    "docker.io/python",
                    "docker.io/pyth*n",
                ],
            },
            {
                lib.NAMESPACE_SELECTOR_FIELD: {
                    lib.MATCH_LABELS_FIELD: {
                        "app": "python",
                    },
                },
                lib.RULE_TARGET_FIELD: "container::image",
                lib.RULE_VERB_FIELD: lib.RULE_VERB_ALLOW,
                lib.RULE_VALUES_FIELD: ["docker.io/not-python"],
            },
        ],
    },
}


@pytest.fixture
def base_deviation():
    rv = {
        lib.API_FIELD: lib.API_VERSION,
        lib.KIND_FIELD: lib.DEVIATION_KIND,
        lib.METADATA_FIELD: {
            lib.METADATA_NAME_FIELD: "test_deviation",
            lib.METADATA_TYPE_FIELD: lib.POL_TYPE_CLUS,
            lib.METADATA_UID_FIELD: "dev:1",
        },
        lib.SPEC_FIELD: {
            lib.RULES_FIELD: [],
        },
    }
    return rv


@pytest.fixture
def deviation_1(base_deviation):
    base_deviation[lib.METADATA_FIELD][lib.METADATA_SCOPES_FIELD] = {
        lib.NAMESPACE_SELECTOR_FIELD: {
            "labels": {
                "app": "foo",
            },
        }
    }
    base_deviation[lib.SPEC_FIELD][lib.RULES_FIELD].append(
        {
            lib.RULE_TARGET_FIELD: "container::image",
            lib.RULE_VERB_FIELD: lib.RULE_VERB_ALLOW,
            lib.RULE_VALUES_FIELD: ["docker.io/mongo"],
        },
    )
    return base_deviation


@pytest.fixture
def deviation_2(base_deviation):
    base_deviation[lib.METADATA_FIELD][lib.METADATA_SCOPES_FIELD] = {
        lib.NAMESPACE_SELECTOR_FIELD: {
            "labels": {
                "app": "foo",
            },
        }
    }
    base_deviation[lib.SPEC_FIELD][lib.RULES_FIELD].append(
        {
            lib.RULE_TARGET_FIELD: "container::imageID",
            lib.RULE_VERB_FIELD: lib.RULE_VERB_ALLOW,
            lib.RULE_VALUES_FIELD: ["sha256@foo123baz"],
        },
    )
    return base_deviation


@pytest.fixture
def deviation_3(base_deviation):
    base_deviation[lib.METADATA_FIELD][lib.METADATA_SCOPES_FIELD] = {
        lib.NAMESPACE_SELECTOR_FIELD: {
            "labels": {
                "app": "foo",
            },
        }
    }
    base_deviation[lib.SPEC_FIELD][lib.RULES_FIELD].append(
        {
            lib.RULE_TARGET_FIELD: "container::containerName",
            lib.RULE_VERB_FIELD: lib.RULE_VERB_ALLOW,
            lib.RULE_VALUES_FIELD: ["my_test_container"],
        },
    )
    return base_deviation


@pytest.fixture
def deviation_4(base_deviation):
    base_deviation[lib.METADATA_FIELD][lib.METADATA_SCOPES_FIELD] = {}
    base_deviation[lib.SPEC_FIELD][lib.RULES_FIELD].append(
        {
            lib.RULE_TARGET_FIELD: "container::image",
            lib.RULE_VERB_FIELD: lib.RULE_VERB_ALLOW,
            lib.RULE_VALUES_FIELD: ["docker.io/bad-image"],
        },
    )
    return base_deviation


@pytest.fixture
def deviation_5(base_deviation):
    base_deviation[lib.METADATA_FIELD][lib.METADATA_SCOPES_FIELD] = {
        lib.NAMESPACE_SELECTOR_FIELD: {
            "labels": {
                "kubernetes.io/namespace": "bad_image_ns",
            },
        }
    }
    base_deviation[lib.SPEC_FIELD][lib.RULES_FIELD].append(
        {
            lib.RULE_TARGET_FIELD: "container::image",
            lib.RULE_VERB_FIELD: lib.RULE_VERB_ALLOW,
            lib.RULE_VALUES_FIELD: ["docker.io/bad-image"],
        },
    )
    return base_deviation


@pytest.fixture
def deviation_6(base_deviation):
    base_deviation[lib.METADATA_FIELD][lib.METADATA_SCOPES_FIELD] = {
        lib.NAMESPACE_SELECTOR_FIELD: {
            "labels": {
                "app": "nginx",
            },
        }
    }
    base_deviation[lib.SPEC_FIELD][lib.RULES_FIELD].append(
        {
            lib.RULE_TARGET_FIELD: "container::image",
            lib.RULE_VERB_FIELD: lib.RULE_VERB_ALLOW,
            lib.RULE_VALUES_FIELD: ["docker.io/nginx"],
        },
    )
    return base_deviation


@pytest.fixture
def deviation_7(base_deviation):
    base_deviation[lib.METADATA_FIELD][lib.METADATA_SCOPES_FIELD] = {
        lib.NAMESPACE_SELECTOR_FIELD: {
            "labels": {
                "app": "mysql",
            },
        }
    }
    base_deviation[lib.SPEC_FIELD][lib.RULES_FIELD].append(
        {
            lib.RULE_TARGET_FIELD: "container::image",
            lib.RULE_VERB_FIELD: lib.RULE_VERB_ALLOW,
            lib.RULE_VALUES_FIELD: ["docker.io/mysql"],
        },
    )
    return base_deviation


@pytest.fixture
def deviation_8(base_deviation):
    base_deviation[lib.METADATA_FIELD][lib.METADATA_SCOPES_FIELD] = {
        lib.NAMESPACE_SELECTOR_FIELD: {
            "labels": {
                "app": "python",
            },
        }
    }
    base_deviation[lib.SPEC_FIELD][lib.RULES_FIELD].append(
        {
            lib.RULE_TARGET_FIELD: "container::image",
            lib.RULE_VERB_FIELD: lib.RULE_VERB_ALLOW,
            lib.RULE_VALUES_FIELD: ["docker.io/python"],
        },
    )
    return base_deviation


def setup_module():
    def get_api_data():
        return "test_org", "test_key", "test_url"

    restore_context()  # In case the last test was cancelled
    backup_context()
    mock_ctx = mock.Mock()
    mock_ctx.get_api_data = mock.Mock()
    mock_ctx.get_api_data = get_api_data
    secrets.set_api_call()
    configs.set_current_context(mock_ctx)


def teardown_module():
    restore_context()
