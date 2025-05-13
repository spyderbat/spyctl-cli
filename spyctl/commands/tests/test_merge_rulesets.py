"""Test merging deviations into rulesets."""

# pylint: disable=missing-function-docstring, redefined-outer-name

from unittest import mock

import pytest
import yaml
from click.testing import CliRunner

import spyctl.commands.merge as _merge
import spyctl.spyctl_lib as lib
from spyctl import spyctl
from spyctl.config import configs, secrets
from spyctl.config.configs import Context
from spyctl.merge_lib.ruleset_merge_object import RulesetPolicyMergeObject
from spyctl.tests.backups import backup_context, restore_context


def test_merge_ruleset_policy(cluster_policy, rulesets, deviation, updated_ruleset):
    def get_rulesets(*_args, **_kwargs):
        return rulesets

    policy_name = cluster_policy[lib.METADATA_FIELD][lib.METADATA_NAME_FIELD]
    with (
        mock.patch("spyctl.commands.merge.get_rulesets", get_rulesets),
        mock.patch("spyctl.merge_lib.ruleset_merge_object.get_rulesets", get_rulesets),
    ):
        mo: RulesetPolicyMergeObject = _merge.merge_resource(
            cluster_policy, policy_name, deviation, src_cmd="diff"
        )[0]
        rs_mo = next(iter(mo.rulesets.values()))
        rs_dict = rs_mo.get_obj_data()
        assert rs_dict == updated_ruleset


def test_merge_ruleset_policy_full_command(rulesets, updated_ruleset_string):
    def get_rulesets(*_args, **_kwargs):
        return rulesets

    runner = CliRunner()
    with (
        mock.patch("spyctl.commands.merge.get_rulesets", get_rulesets),
        mock.patch("spyctl.merge_lib.ruleset_merge_object.get_rulesets", get_rulesets),
        mock.patch.object(
            Context,
            "get_api_data",
            lambda _x: ("test_org", "test_key", "test_url"),
        ),
    ):
        response = runner.invoke(
            spyctl.main,
            [
                "merge",
                "-f",
                "spyctl/commands/tests/testdata/cluster_policy.yaml",
                "-w",
                "spyctl/commands/tests/testdata/cluster_deviation.yaml",
                "-y",
            ],
        )
        assert response.exit_code == 0
        print(response.output.strip())
        assert response.output.strip() == updated_ruleset_string.strip()


@pytest.fixture
def cluster_policy():
    with open(
        "spyctl/commands/tests/testdata/cluster_policy.yaml",
        "r",
        encoding="utf-8",
    ) as f:
        return lib.load_resource_file(f)


@pytest.fixture
def deviation():
    with open(
        "spyctl/commands/tests/testdata/cluster_deviation.yaml",
        "r",
        encoding="utf-8",
    ) as f:
        return yaml.load(f, Loader=yaml.SafeLoader)


@pytest.fixture
def rulesets():
    with open(
        "spyctl/commands/tests/testdata/cluster_ruleset.yaml",
        "r",
        encoding="utf-8",
    ) as f:
        return [lib.load_resource_file(f)]


@pytest.fixture
def updated_ruleset():
    with open(
        "spyctl/commands/tests/testdata/updated_ruleset.yaml",
        "r",
        encoding="utf-8",
    ) as f:
        return lib.load_resource_file(f)


@pytest.fixture
def updated_ruleset_string():
    with open(
        "spyctl/commands/tests/testdata/updated_ruleset.yaml",
        "r",
        encoding="utf-8",
    ) as f:
        return f.read()


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
