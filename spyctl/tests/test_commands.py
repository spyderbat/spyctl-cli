import json
import os
import shutil
from fnmatch import fnmatch
from itertools import groupby
from pathlib import Path
from typing import Tuple
from unittest import mock

import pytest
from click.testing import CliRunner

import spyctl.tests.mock_functions as mock_func
from spyctl import spyctl
from spyctl.config.configs import CURR_CONTEXT_NONE, set_testing
from spyctl.spyctl_lib import time_inp
from spyctl.tests.backups import backup_secrets, restore_secrets

API_KEY = os.environ.get("API_KEY")
API_URL = os.environ.get("API_URL")
ORG = os.environ.get("ORG")
TEST_SECRET = "__test_secret__"
TEST_CONTEXT = "__test_context__"
CURR_PATH = Path.cwd()
WORKSPACE_DIR_NAME = "test_workspace__"
WORKSPACE_PATH = Path(f"./{WORKSPACE_DIR_NAME}")
WORKSPACE_CONFIG = Path(str(WORKSPACE_PATH.absolute()) + "/.spyctl/config")
CURRENT_CONTEXT = None


class SetupException(Exception):
    pass


def test_version():
    runner = CliRunner()
    response = runner.invoke(spyctl.main, ["-v"])
    test_pat = "Spyctl, version *.*.*"
    assert response.exit_code == 0
    assert fnmatch(response.output, test_pat)
    response = runner.invoke(spyctl.main, ["--version"])
    test_pat = "Spyctl, version *.*.*"
    assert response.exit_code == 0
    assert fnmatch(response.output, test_pat)


def test_help():
    runner = CliRunner()
    response = runner.invoke(spyctl.main, ["-h"])
    assert response.exit_code == 0
    response = runner.invoke(spyctl.main, ["--help"])
    assert response.exit_code == 0
    response = runner.invoke(spyctl.main, ["get", "redflags", "--help"])
    assert response.exit_code == 0
    response = runner.invoke(spyctl.main, ["config", "--help"])
    assert response.exit_code == 0


@mock.patch(
    "spyctl.commands.get.namespaces.sq_api.get_namespaces",
    mock_func.mock_get_namespaces,
)
def test_get_namespaces():
    get_resource("namespaces", TWOHOURS)
    get_resource("namespaces", TWOHOURS + OUTYML)


TWOHOURS = ["-t", "2h"]
OUTYML = ["-o", "yaml"]
MINS_30 = ["-t", "30m"]
MINS_5 = ["-t", "5m"]


def remove_timestamps(str_list):
    rv = []
    for string in str_list:
        try:
            time_inp(string)
        except ValueError:
            rv.append(string)
    return rv


# asserts that the table has some population and returns
# name_or_id values that should give the first line again
def process_table_response(output: str):
    name_or_id_fields = ("NAME", "UID", "FLAG", "IMAGE", "CGROUP")
    lines = output.strip().splitlines()
    assert len(lines) > 1
    header_line, first_line = lines[:2]
    headers = []
    for non_empty_group, chars in groupby(
        enumerate(header_line), lambda x: not x[1].isspace()
    ):
        if non_empty_group:
            pos, header = next(chars)
            header += "".join(c for _, c in chars)
            headers.append((pos, header))
    rv = []
    for i, (pos, header) in enumerate(headers):
        if header in name_or_id_fields:
            next_pos = headers[i + 1][0] if i < len(headers) - 1 else None
            table_element = first_line[pos:next_pos].strip()
            rv.append(table_element)
    print(header_line)
    print(headers)
    assert len(rv) > 0
    comparison_line = remove_timestamps(first_line.split())
    return comparison_line, rv


resources = (
    "clusters",
    "sources",
    "policies",
    "pods",
    "nodes",
    "deployments",
    "fingerprints",
    "namespaces",  # doesn't output a table
    "redflags",
    "opsflags",
)


def get_resource(resource, args=[], print_output=False):
    runner = CliRunner(mix_stderr=False)
    response = runner.invoke(spyctl.main, ["get", resource, *args])
    if print_output:
        print(response.output)
    assert response.exit_code == 0
    return response.stdout


SPECIAL_GET_ARGS = {"fingerprints": ["--type", "linux-service"]}


def get_args(resource: str) -> Tuple:
    return SPECIAL_GET_ARGS.get(resource, [])


resources_dir = Path(__file__).parent / "test_resources"


def test_create():
    runner = CliRunner()
    response = runner.invoke(
        spyctl.main,
        ["create", "policy", "-f", resources_dir / "test_baseline.yaml"],
    )
    assert response.exit_code == 0
    with open(resources_dir / "test_policy.yaml", "r", encoding="utf-8") as f:
        assert response.output.strip("\n") == f.read().strip("\n")
    response = runner.invoke(
        spyctl.main,
        ["create", "policy", "-f", resources_dir / "test_fprint_group.yaml"],
    )
    assert response.exit_code == 0
    with open(
        resources_dir / "test_created_policy.yaml", "r", encoding="utf-8"
    ) as f:
        assert response.output.strip("\n") == f.read().strip("\n")


@pytest.mark.skip(reason="For local testing. API testing is out of scope.")
def test_create_api():
    runner = CliRunner()
    response = runner.invoke(
        spyctl.main,
        [
            "create",
            "policy",
            "-f",
            resources_dir / "test_fingerprint_list.json",
            "--api",
        ],
    )
    assert response.exit_code == 0


@mock.patch(
    "spyctl.commands.get.policies.pol_api.get_policies",
    mock_func.mock_get_policies,
)
@mock.patch.multiple(
    "spyctl.commands.apply_cmd.apply",
    post_new_policy=mock_func.mock_post_new_policy,
    put_policy_update=mock_func.mock_put_policy_update,
)
@mock.patch.multiple(
    "spyctl.commands.delete.policy",
    get_policies=mock_func.mock_get_policies,
    delete_policy=mock_func.mock_delete_policy,
)
def test_update_policy():
    runner = CliRunner()
    response = runner.invoke(
        spyctl.main, ["apply", "-f", resources_dir / "test_policy.yaml"]
    )
    assert response.exit_code == 0
    assert response.output.startswith(
        "Successfully applied new container guardian policy with uid:"
    )
    response = runner.invoke(
        spyctl.main, ["get", "policies", "spyderbat-test"]
    )
    assert response.exit_code == 0
    assert "spyderbat-test" in response.output
    lines = response.stdout.splitlines()
    uid = lines[2].split(" ")[0]
    get_runner = CliRunner(mix_stderr=False)
    response = get_runner.invoke(
        spyctl.main, ["get", "policies", uid, "-o", "yaml"]
    )
    assert response.exit_code == 0
    assert "spyderbat-test" in response.output
    policy_with_uid = "uid_pol.yaml"
    with open(policy_with_uid, "w") as f:
        f.write(response.output)
    response = runner.invoke(spyctl.main, ["apply", "-f", policy_with_uid])
    assert response.exit_code == 0
    assert response.output.startswith("Successfully updated policy")
    response = runner.invoke(
        spyctl.main, ["delete", "policy", "-y", "spyderbat-test"]
    )
    assert response.exit_code == 0
    assert response.output.startswith("Successfully deleted policy")


@mock.patch(
    "spyctl.commands.get.policies.pol_api.get_policies",
    mock_func.mock_get_policies,
)
@mock.patch.multiple(
    "spyctl.commands.apply_cmd.apply",
    post_new_policy=mock_func.mock_post_new_policy,
)
@mock.patch.multiple(
    "spyctl.commands.delete.policy",
    get_policies=mock_func.mock_get_policies,
    delete_policy=mock_func.mock_delete_policy,
)
def test_apply_delete():
    runner = CliRunner()
    response = runner.invoke(
        spyctl.main, ["apply", "-f", Path(resources_dir, "test_policy.yaml")]
    )
    assert response.exit_code == 0
    assert response.output.startswith(
        "Successfully applied new container guardian policy with uid:"
    )
    response = runner.invoke(
        spyctl.main, ["get", "policies", "spyderbat-test"]
    )
    assert response.exit_code == 0
    assert "spyderbat-test" in response.output
    response = runner.invoke(
        spyctl.main, ["delete", "policy", "-y", "spyderbat-test"]
    )
    assert response.exit_code == 0
    assert response.output.startswith("Successfully deleted policy")


def test_diff():
    runner = CliRunner()
    response = runner.invoke(
        spyctl.main,
        [
            "diff",
            "-f",
            str(resources_dir) + "/test_baseline.yaml",
            "-w",
            str(resources_dir) + "/test_baseline_extra.yaml",
            "-y",
        ],
    )
    print(response.output)
    assert response.exit_code == 0
    assert "+     - name: python3.7" in response.output


@pytest.mark.skip(reason="For local testing. API testing is out of scope.")
def test_diff_api():
    runner = CliRunner()
    response = runner.invoke(
        spyctl.main,
        [
            "diff",
            "-f",
            str(resources_dir) + "/test_baseline.yaml",
            "-w",
            str(resources_dir) + "/test_baseline_extra.yaml",
            "-y",
            "--api",
        ],
    )
    print(response.output)
    assert response.exit_code == 0
    assert "+     - name: python3.7" in response.output


def test_merge():
    runner = CliRunner()
    response = runner.invoke(
        spyctl.main,
        [
            "merge",
            "-f",
            str(resources_dir) + "/test_baseline.yaml",
            "-w",
            str(resources_dir) + "/test_baseline_extra.yaml",
            "-y",
        ],
    )
    print(response.output)
    assert response.exit_code == 0
    assert "\n    - name: python3.7" in response.output
    assert "\n    - name: sh" in response.output


@pytest.mark.skip(reason="For local testing. API testing is out of scope.")
def test_merge_api():
    runner = CliRunner()
    response = runner.invoke(
        spyctl.main,
        [
            "merge",
            "-f",
            str(resources_dir) + "/test_baseline.yaml",
            "-w",
            str(resources_dir) + "/test_baseline_extra.yaml",
            "-y",
            "--api",
        ],
    )
    print(response.output)
    assert response.exit_code == 0
    assert "'name': 'python3.7'" in response.output
    assert "'name': 'sh'" in response.output


@pytest.mark.skip(
    reason="For local testing. API testing is out of scope. "
    "UID lists must be updated as data expires."
)
def test_merge_api_uid_list():
    runner = CliRunner()
    response = runner.invoke(
        spyctl.main,
        [
            "merge",
            "-f",
            str(resources_dir) + "/pol_for_uid_list_merge_test.json",
            "-w",
            str(resources_dir) + "/test_uid_list.json",
            "-y",
            "--api",
        ],
    )
    print(response.output)
    assert response.exit_code == 0


@pytest.mark.skip(
    reason="For local testing. UID lists must be updated as data expires."
)
def test_merge_uid_list():
    runner = CliRunner()
    response = runner.invoke(
        spyctl.main,
        [
            "merge",
            "-f",
            str(resources_dir) + "/pol_for_uid_list_merge_test.json",
            "-w",
            str(resources_dir) + "/test_uid_list.json",
            "-y",
        ],
    )
    print(response.output)
    assert response.exit_code == 0


def test_validate(policy_path):
    runner = CliRunner()
    response = runner.invoke(
        spyctl.main,
        [
            "validate",
            "-f",
            policy_path,
        ],
    )
    print(response.output)
    assert response.exit_code == 0


@pytest.mark.skip(reason="For local testing. API testing is out of scope.")
def test_validate_api(policy_path):
    runner = CliRunner()
    response = runner.invoke(
        spyctl.main,
        [
            "validate",
            "-f",
            policy_path,
            "--api",
        ],
    )
    assert response.exit_code == 0


@pytest.fixture
def policy_path():
    return resources_dir / "test_policy.yaml"


def env_setup() -> bool:
    # Tests that the proper environment variables exist in pyproject.toml
    if not API_KEY or API_KEY == "__NONE__":
        print(
            "No api key provided. Edit the API_KEY environment variable in"
            " pyproject.toml"
        )
        return False
    if not API_URL or API_URL == "__NONE__":
        print(
            "No api url provided. Edit the API_URL environment variable in"
            ' pyproject.toml to "API_URL=https://api.spyderbat.com"'
        )
        return False
    if not ORG or ORG == "__NONE__":
        print(
            "No organization provided. Edit the ORG environment variable in"
            " pyproject.toml"
        )
        return False
    return True


def create_secret():
    runner = CliRunner()
    result = runner.invoke(
        spyctl.main,
        [
            "config",
            "set-apisecret",
            "-k",
            API_KEY,
            "-u",
            API_URL,
            TEST_SECRET,
        ],
    )
    if result.exit_code != 0:
        raise SetupException("Unable to create test secret")


def delete_secret():
    runner = CliRunner()
    runner.invoke(
        spyctl.main,
        [
            "config",
            "delete-apisecret",
            "-y",
            TEST_SECRET,
        ],
    )


def create_context(name):
    runner = CliRunner()
    result = runner.invoke(
        spyctl.main,
        [
            "config",
            "set-context",
            "-s",
            TEST_SECRET,
            "-o",
            ORG,
            "-g",
            "-u",
            name,
        ],
    )
    if result.exit_code != 0:
        raise SetupException("Unable to create test context")


def delete_context(name):
    runner = CliRunner()
    runner.invoke(
        spyctl.main,
        ["config", "delete-context", name],
    )


def delete_test_policies():
    runner = CliRunner()
    runner.invoke(spyctl.main, ["delete", "policy", "-y", "spyderbat-test"])


def current_context():
    runner = CliRunner()
    result = runner.invoke(
        spyctl.main,
        [
            "config",
            "current-context",
        ],
    )
    if result.exit_code != 0:
        raise SetupException("Unable get current context")
    current_ctx = result.output.strip("\n")
    return current_ctx


def use_test_context(name):
    runner = CliRunner()
    runner.invoke(spyctl.main, ["config", "use-context", name])


def use_current_context():
    if CURRENT_CONTEXT:
        runner = CliRunner()
        runner.invoke(spyctl.main, ["config", "use-context", CURRENT_CONTEXT])


def setup_module():
    if not env_setup():
        raise SetupException("Check environment variables in pyproject.toml")
    restore_secrets()  # In case the last test was cancelled
    backup_secrets()

    global CURRENT_CONTEXT
    current_ctx = current_context()
    if current_ctx and current_ctx != CURR_CONTEXT_NONE:
        CURRENT_CONTEXT = current_ctx
    if WORKSPACE_PATH.exists():
        teardown_module()
        raise SetupException("Workspace path already exists")
    WORKSPACE_PATH.mkdir(exist_ok=False)
    os.chdir(WORKSPACE_PATH)
    create_secret()
    create_context(TEST_CONTEXT)
    use_test_context(TEST_CONTEXT)
    # Set a global variable in configs.py to force reloading
    # the config file. Otherwise the global variable LOADED_CONFIG
    # remains set across invocations
    set_testing()


def teardown_module():
    delete_test_policies()
    delete_context(TEST_CONTEXT)
    delete_secret()
    use_current_context()
    os.chdir(CURR_PATH)
    shutil.rmtree(WORKSPACE_PATH, ignore_errors=True)
    restore_secrets()
