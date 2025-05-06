# pylint: disable=broad-except
import io
import json
import sys
import unittest
from unittest import mock
from click.testing import CliRunner
from spyctl.commands.get.pods import handle_get_pods
from spyctl.commands.get.nodes import handle_get_nodes
from spyctl.commands.get.roles import handle_get_roles
from spyctl.commands.get.clusterroles import handle_get_clusterroles
from spyctl.commands.get.rolebindings import handle_get_rolebindings
from spyctl.commands.get.clusterrolebindings import handle_get_clusterrolebindings
from spyctl.commands.get.namespaces import handle_get_namespaces
from spyctl.commands.get.redflags import handle_get_redflags
from spyctl.commands.get.opsflags import handle_get_opsflags
from spyctl.commands.get.deployments import handle_get_deployments
from spyctl.commands.get.agents import handle_get_agents
from spyctl.commands.get.spydertraces import handle_get_spydertraces
from spyctl.commands.get.deviations import handle_get_deviations
from spyctl.commands.get.fingerprints import handle_get_fingerprints
from spyctl.commands.get.top_data import handle_get_top_data
from spyctl.commands.get.bash_cmds import handle_get_bash_cmds
from spyctl.commands.get.connection_bundles import handle_get_conn_buns
from spyctl.commands.get.machines import handle_get_machines
from spyctl.commands.get.custom_flags import handle_get_custom_flags
from spyctl.commands.get.saved_queries import handle_get_saved_queries
from spyctl.config.configs import Context


with open("spyctl/tests/testdata_resources.json", "r") as file:
    mock_data = json.load(file)


class TestGetResources(unittest.TestCase):
    def setUp(self):
        self.mock_context = mock.Mock(spec=Context)
        self.mock_context.get_api_data.return_value = ("fake_api_key", "fake_org_id")

    # --------------------PODS------------------------------------

    @mock.patch("spyctl.commands.get.pods.search_athena")
    @mock.patch("spyctl.config.configs.get_current_context")
    def test_handle_get_pods(self, mock_get_current_context, mock_search_athena):

        mock_pods_data = [mock_data["Pod"]]

        # Mock search_athena function
        def mocked_search_athena(
            _api_key,
            _org_id,
            _model,
            _query,
            _start_time=None,
            _end_time=None,
            _desc=None,
            *args,
            **kwargs,
        ):
            return mock_pods_data

        mock_search_athena.side_effect = mocked_search_athena
        mock_get_current_context.return_value = self.mock_context

        captured_output = io.StringIO()
        sys.stdout = captured_output  # Redirect stdout

        try:
            handle_get_pods(
                name_or_id=None,
                output="default",
                st=None,
                et=None,
            )
        except Exception as e:
            print(f"Exception occurred: {e}")
            self.fail("handle_get_pods raised an exception!")

        sys.stdout = sys.__stdout__  # Reset stdout

        output = captured_output.getvalue().strip()  # Remove extra spaces

        # Split output into lines and extract the second line (actual data)
        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(name, "mock_pod")

        self.assertTrue(mock_search_athena.called)

        mock_get_current_context.assert_called_once()
        mock_search_athena.assert_called_once()
        self.assertEqual(name, "mock_pod")

    # --------------------NODES------------------------------------
    @mock.patch("spyctl.commands.get.nodes.search_athena")
    @mock.patch("spyctl.config.configs.get_current_context")
    def test_handle_get_nodes(self, mock_get_current_context, mock_search_athena):

        mock_nodes_data = [mock_data["Node"]]

        # Mock search_athena function
        def mocked_search_athena(
            _api_key,
            _org_id,
            _model,
            _query,
            _start_time=None,
            _end_time=None,
            _desc=None,
            *args,
            **kwargs,
        ):
            return mock_nodes_data  # Returning mock node data

        mock_search_athena.side_effect = mocked_search_athena
        mock_get_current_context.return_value = self.mock_context

        captured_output = io.StringIO()
        sys.stdout = captured_output  # Redirect stdout

        try:
            handle_get_nodes(
                name_or_id=None,
                output="default",
                st=None,
                et=None,
            )
        except Exception as e:
            print(f"Exception occurred: {e}")
            self.fail("handle_get_nodes raised an exception!")

        self.assertTrue(mock_search_athena.called)

        sys.stdout = sys.__stdout__  # Reset stdout

        output = captured_output.getvalue().strip()  # Remove extra spaces

        # Split output into lines and extract the second line (actual data)
        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(name, "mock_node")

        mock_get_current_context.assert_called_once()
        mock_search_athena.assert_called_once()

    # --------------------DEPLOYMENT------------------------------------
    @mock.patch("spyctl.commands.get.deployments.search_athena")
    @mock.patch("spyctl.config.configs.get_current_context")
    def test_handle_get_deployments(self, mock_get_current_context, mock_search_athena):

        mock_deployments_data = [mock_data["Deployment"]]  # Mock deployment data

        def mocked_search_athena(
            _api_key,
            _org_id,
            _model,
            _query,
            _start_time=None,
            _end_time=None,
            _desc=None,
            *args,
            **kwargs,
        ):
            return mock_deployments_data  # Returning mock deployment data

        mock_search_athena.side_effect = mocked_search_athena
        mock_get_current_context.return_value = self.mock_context

        captured_output = io.StringIO()
        sys.stdout = captured_output  # Redirect stdout

        # Call handle_get_deployments directly
        try:
            handle_get_deployments(
                name_or_id=None,
                output="default",
                st=None,
                et=None,
            )
        except Exception as e:
            print(f"Exception occurred: {e}")
            self.fail("handle_get_deployments raised an exception!")

        self.assertTrue(mock_search_athena.called)

        sys.stdout = sys.__stdout__  # Reset stdout

        output = captured_output.getvalue().strip()  # Remove extra spaces

        # Split output into lines and extract the second line (actual data)
        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(name, "mock-deployment")

        mock_get_current_context.assert_called_once()
        mock_search_athena.assert_called_once()

    # --------------------Namespace----------------------------------

    @mock.patch("spyctl.commands.get.namespaces.search_athena")
    @mock.patch("spyctl.config.configs.get_current_context")
    def test_handle_get_namespace(self, mock_get_current_context, mock_search_athena):

        mock_namespace_data = [mock_data["Namespace"]]  # Mock namespace data

        # Mock search_athena function
        def mocked_search_athena(
            _api_key,
            _org_id,
            _model,
            _query,
            _start_time=None,
            _end_time=None,
            _desc=None,
            *args,
            **kwargs,
        ):
            return mock_namespace_data  # Returning mock namespace data

        mock_search_athena.side_effect = mocked_search_athena
        mock_get_current_context.return_value = self.mock_context

        captured_output = io.StringIO()
        sys.stdout = captured_output  # Redirect stdout

        # Call handle_get_namespace directly
        try:
            handle_get_namespaces(
                name_or_id=None,
                output="default",
                st=None,
                et=None,
            )
        except Exception as e:
            print(f"Exception occurred: {e}")
            self.fail("handle_get_namespace raised an exception!")

        self.assertTrue(mock_search_athena.called)

        sys.stdout = sys.__stdout__  # Reset stdout

        output = captured_output.getvalue().strip()  # Remove extra spaces

        # Split output into lines and extract the second line (actual data)
        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(name, "mock-namespace")

        mock_get_current_context.assert_called_once()
        mock_search_athena.assert_called_once()

    # -----------------Redflags----------------------------

    @mock.patch("spyctl.commands.get.redflags.search_athena")
    @mock.patch("spyctl.config.configs.get_current_context")
    def test_handle_get_redflags(self, mock_get_current_context, mock_search_athena):

        mock_redflags_data = [mock_data["Redflag"]]  # Mock redflag data

        # Mock search_athena function
        def mocked_search_athena(
            _api_key,
            _org_id,
            _model,
            _query,
            _start_time=None,
            _end_time=None,
            _desc=None,
            *args,
            **kwargs,
        ):
            return mock_redflags_data  # Returning mock redflag data

        mock_search_athena.side_effect = mocked_search_athena
        mock_get_current_context.return_value = self.mock_context

        captured_output = io.StringIO()
        sys.stdout = captured_output  # Redirect stdout

        # Call handle_get_redflags directly
        try:
            handle_get_redflags(
                name_or_id=None,
                output="default",
                st=None,
                et=None,
            )
        except Exception as e:
            print(f"Exception occurred: {e}")
            self.fail("handle_get_redflags raised an exception!")

        self.assertTrue(mock_search_athena.called)

        sys.stdout = sys.__stdout__  # Reset stdout

        output = captured_output.getvalue().strip()  # Remove extra spaces

        lines = output.split("\n")
        if len(lines) > 1:
            flag = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(flag, "command_curl")

        mock_get_current_context.assert_called_once()
        mock_search_athena.assert_called_once()

    # -----------------Opsflag----------------------------

    @mock.patch("spyctl.commands.get.opsflags.search_athena")
    @mock.patch("spyctl.config.configs.get_current_context")
    def test_handle_get_opsflags(self, mock_get_current_context, mock_search_athena):

        mock_opsflags_data = [mock_data["Opsflag"]]  # Mock opsflag data

        # Mock search_athena function
        def mocked_search_athena(
            _api_key,
            _org_id,
            _model,
            _query,
            _start_time=None,
            _end_time=None,
            _desc=None,
            *args,
            **kwargs,
        ):
            return mock_opsflags_data  # Returning mock opsflag data

        mock_search_athena.side_effect = mocked_search_athena
        mock_get_current_context.return_value = self.mock_context

        captured_output = io.StringIO()
        sys.stdout = captured_output  # Redirect stdout

        # Call handle_get_opsflags directly
        try:
            handle_get_opsflags(
                name_or_id=None,
                output="default",
                st=None,
                et=None,
            )
        except Exception as e:
            print(f"Exception occurred: {e}")
            self.fail("handle_get_opsflags raised an exception!")

        self.assertTrue(mock_search_athena.called)

        sys.stdout = sys.__stdout__  # Reset stdout

        output = captured_output.getvalue().strip()  # Remove extra spaces

        lines = output.split("\n")
        if len(lines) > 1:
            flag = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(flag, "memory_leak")

        mock_get_current_context.assert_called_once()
        mock_search_athena.assert_called_once()

    # --------------------Roles------------------------------

    @mock.patch("spyctl.commands.get.roles.search_athena")
    @mock.patch("spyctl.config.configs.get_current_context")
    def test_handle_get_roles(self, mock_get_current_context, mock_search_athena):

        mock_roles_data = [mock_data["Role"]]  # Mock Role data

        def mocked_search_athena(api_key, org_id, model, query, *args, **kwargs):
            return mock_roles_data  # Returning mock Role data

        mock_search_athena.side_effect = mocked_search_athena
        mock_get_current_context.return_value = self.mock_context

        captured_output = io.StringIO()
        sys.stdout = captured_output  # Redirect stdout

        try:
            handle_get_roles(name_or_id=None, output="default", st=None, et=None)
        except Exception as e:
            print(f"Exception occurred: {e}")
            self.fail("handle_get_roles raised an exception!")

        sys.stdout = sys.__stdout__  # Reset stdout

        output = captured_output.getvalue().strip()  # Remove extra spaces

        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(name, "vault-discovery-role")

        self.assertTrue(mock_search_athena.called)

        mock_get_current_context.assert_called_once()
        mock_search_athena.assert_called_once()

    # --------------ClusterRoles-------------------------------------

    @mock.patch("spyctl.commands.get.clusterroles.search_athena")
    @mock.patch("spyctl.config.configs.get_current_context")
    def test_handle_get_clusterroles(
        self, mock_get_current_context, mock_search_athena
    ):

        mock_clusterroles_data = [mock_data["ClusterRole"]]

        def mocked_search_athena(api_key, org_id, model, query, *args, **kwargs):
            return mock_clusterroles_data  # Returning mock ClusterRole data

        mock_search_athena.side_effect = mocked_search_athena
        mock_get_current_context.return_value = self.mock_context

        captured_output = io.StringIO()
        sys.stdout = captured_output  # Redirect stdout

        try:
            handle_get_clusterroles(name_or_id=None, output="default", st=None, et=None)
        except Exception as e:
            print(f"Exception occurred: {e}")
            self.fail("handle_get_clusterroles raised an exception!")

        self.assertTrue(mock_search_athena.called)

        sys.stdout = sys.__stdout__  # Reset stdout

        output = captured_output.getvalue().strip()  # Remove extra spaces

        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(name, "vault-agent-injector-clusterrole")

        mock_get_current_context.assert_called_once()
        mock_search_athena.assert_called_once()

    # --------------ClusterRoleBindning-------------------------------------

    @mock.patch("spyctl.commands.get.clusterrolebindings.search_athena")
    @mock.patch("spyctl.config.configs.get_current_context")
    def test_handle_get_clusterrolebindings(
        self, mock_get_current_context, mock_search_athena
    ):

        mock_crb_data = [mock_data["ClusterRoleBinding"]]  # Mock CRB data

        def mocked_search_athena(_api_key, _org_id, _model, _query, *args, **kwargs):
            return mock_crb_data  # Returning mock CRB data

        mock_search_athena.side_effect = mocked_search_athena
        mock_get_current_context.return_value = self.mock_context

        captured_output = io.StringIO()
        sys.stdout = captured_output  # Redirect stdout

        try:
            handle_get_clusterrolebindings(
                name_or_id=None, output="default", st=None, et=None
            )
        except Exception as e:
            print(f"Exception occurred: {e}")
            self.fail("handle_get_clusterrolebindings raised an exception!")

        self.assertTrue(mock_search_athena.called)

        sys.stdout = sys.__stdout__  # Reset stdout

        output = captured_output.getvalue().strip()  # Remove extra spaces

        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(name, "pomerium-gen-secrets")

        mock_get_current_context.assert_called_once()
        mock_search_athena.assert_called_once()

    # --------------RoleBindning-------------------------------------

    @mock.patch("spyctl.commands.get.rolebindings.search_athena")
    @mock.patch("spyctl.config.configs.get_current_context")
    def test_handle_get_rolebindings(
        self, mock_get_current_context, mock_search_athena
    ):

        mock_rolebindings_data = [mock_data["RoleBinding"]]

        def mocked_search_athena(_api_key, _org_id, _model, _query, *args, **kwargs):
            return mock_rolebindings_data

        mock_search_athena.side_effect = mocked_search_athena
        mock_get_current_context.return_value = self.mock_context

        captured_output = io.StringIO()
        sys.stdout = captured_output  # Redirect stdout

        try:
            handle_get_rolebindings(name_or_id=None, output="default", st=None, et=None)
        except Exception as e:
            print(f"Exception occurred: {e}")
            self.fail("handle_get_rolebindings raised an exception!")

        self.assertTrue(mock_search_athena.called)

        sys.stdout = sys.__stdout__  # Reset stdout

        output = captured_output.getvalue().strip()  # Remove extra spaces

        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(name, "vault-discovery-rolebinding")

        mock_get_current_context.assert_called_once()
        mock_search_athena.assert_called_once()

    # --------------Agents-------------------------------------

    @mock.patch("spyctl.commands.get.agents.search_athena")
    @mock.patch("spyctl.config.configs.get_current_context")
    def test_handle_get_agents(self, mock_get_current_context, mock_search_athena):

        mock_agent_data = [mock_data["Agent"]]

        def mocked_search_athena(_api_key, _org_id, _model, _query, *args, **kwargs):
            return mock_agent_data

        mock_search_athena.side_effect = mocked_search_athena
        mock_get_current_context.return_value = self.mock_context

        captured_output = io.StringIO()
        sys.stdout = captured_output  # Redirect stdout

        try:
            handle_get_agents(name_or_id=None, output="default", st=None, et=None)
        except Exception as e:
            print(f"Exception occurred: {e}")

        self.assertTrue(mock_search_athena.called)

        sys.stdout = sys.__stdout__  # Reset stdout

        output = captured_output.getvalue().strip()  # Remove extra spaces

        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(name, "vault-discovery-rolebinding")

        mock_get_current_context.assert_called_once()
        mock_search_athena.assert_called_once()

    # ----------------Spydertrace-------------------------------------

    @mock.patch("spyctl.commands.get.spydertraces.search_athena")
    @mock.patch("spyctl.config.configs.get_current_context")
    def test_handle_get_spydertraces(
        self, mock_get_current_context, mock_search_athena
    ):

        mock_trace_data = [mock_data["Spydertrace"]]

        def mocked_search_athena(_api_key, _org_id, _model, _query, *args, **kwargs):
            return mock_trace_data

        mock_search_athena.side_effect = mocked_search_athena
        mock_get_current_context.return_value = self.mock_context

        captured_output = io.StringIO()
        sys.stdout = captured_output  # Redirect stdout

        try:
            handle_get_spydertraces(name_or_id=None, output="default", st=None, et=None)
        except Exception as e:
            print(f"Exception occurred: {e}")

        self.assertTrue(mock_search_athena.called)

        sys.stdout = sys.__stdout__  # Reset stdout

        output = captured_output.getvalue().strip()  # Remove extra spaces

        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(name, "vault-discovery-rolebinding")

        mock_get_current_context.assert_called_once()
        mock_search_athena.assert_called_once()

    # --------------------Deviation-------------------------------------

    @mock.patch("spyctl.commands.get.deviations.pol_api.get_policies")
    @mock.patch("spyctl.config.configs.get_current_context")
    @mock.patch("spyctl.commands.get.deviations.search_athena")
    def test_handle_get_deviations(
        self, mock_get_current_context, mock_get_policies, mock_search_athena
    ):
        # Mock data to be returned by `get_policies()`
        mock_policy_data = [
            {
                "apiVersion": "spyderbat/v1",
                "kind": "SpyderbatPolicy",
                "metadata": {
                    "name": "supress_command_airflow_data-prod",
                    "type": "trace",
                    "uid": "pol:AKFXXXXXXXXXXX",
                    "version": 1,
                },
                "spec": {
                    "allowedFlags": [
                        {
                            "class": "redflag/proc/command/high_severity/hidden/python",
                            "display_name": "command_python",
                            "display_severity": "high",
                        },
                    ]
                },
            }
        ]

        # Mock `get_current_context()` to return a mocked context object
        mock_context = mock.Mock()
        mock_context.get_api_data.return_value = (
            "api_key",
            "org_id",
            "model",
        )
        mock_get_current_context.return_value = mock_context

        # Mock `get_policies` to return the mock data
        mock_get_policies.return_value = mock.Mock(
            json=mock.Mock(return_value=mock_policy_data)
        )

        mock_dev_data = [mock_data["Deviation"]]

        def mocked_search_athena(_api_key, _org_id, _model, _query, *args, **kwargs):
            return mock_dev_data  # Returning mock Deviation data

        mock_search_athena.side_effect = mocked_search_athena

        captured_output = io.StringIO()
        sys.stdout = captured_output  # Redirect stdout

        try:
            handle_get_deviations(name_or_id=None, output="wide", st=None, et=None)
        except Exception as e:
            print(f"Exception occurred: {e}")

        self.assertTrue(mock_get_policies.called)

        sys.stdout = sys.__stdout__  # Reset stdout

        output = captured_output.getvalue().strip()
        print("Captured Output:", output)

    # --------------------Fingerprints------------------------------------

    @mock.patch("spyctl.commands.get.fingerprints.search_athena")
    @mock.patch("spyctl.config.configs.get_current_context")
    def test_handle_get_fingerprints(
        self, mock_get_current_context, mock_search_athena
    ):

        mock_fingerprint_data = [mock_data["Fingerprint"]]

        def mocked_search_athena(_api_key, _org_id, _model, _query, *args, **kwargs):
            return mock_fingerprint_data

        mock_search_athena.side_effect = mocked_search_athena
        mock_get_current_context.return_value = self.mock_context

        captured_output = io.StringIO()
        sys.stdout = captured_output  # Redirect stdout

        try:
            handle_get_fingerprints(
                name_or_id=None,
                output="default",
                st=None,
                et=None,
                fprint_type="linux-service",
            )
        except Exception as e:
            print(f"Exception occurred: {e}")

        self.assertTrue(mock_search_athena.called)

        sys.stdout = sys.__stdout__  # Reset stdout

        output = captured_output.getvalue().strip()  # Remove extra spaces

        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(name, "vault-discovery-rolebinding")

        mock_get_current_context.assert_called_once()
        mock_search_athena.assert_called_once()

    # --------------------Top-Data------------------------------------

    @mock.patch("spyctl.commands.get.top_data.search_athena")
    @mock.patch("spyctl.config.configs.get_current_context")
    def test_handle_get_top_data(self, mock_get_current_context, mock_search_athena):

        mock_top_data = [mock_data["Top-Data"]]

        def mocked_search_athena(_api_key, _org_id, _model, _query, *args, **kwargs):
            return mock_top_data

        mock_search_athena.side_effect = mocked_search_athena
        mock_get_current_context.return_value = self.mock_context

        captured_output = io.StringIO()
        sys.stdout = captured_output  # Redirect stdout

        try:
            handle_get_top_data(
                name_or_id=None,
                output="default",
                st=None,
                et=None,
                muid_equals="mach:abc",
            )
        except Exception as e:
            print(f"Exception occurred: {e}")

        self.assertTrue(mock_search_athena.called)

        sys.stdout = sys.__stdout__  # Reset stdout

        output = captured_output.getvalue().strip()  # Remove extra spaces

        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(name, "vault-discovery-rolebinding")

        mock_get_current_context.assert_called_once()
        mock_search_athena.assert_called_once()

    # --------------------Bash-cmds------------------------------------

    @mock.patch("spyctl.commands.get.bash_cmds.search_athena")
    @mock.patch("spyctl.config.configs.get_current_context")
    def test_handle_get_bash_cmds(self, mock_get_current_context, mock_search_athena):

        mock_bash_data = [mock_data["Bash-cmd"]]

        def mocked_search_athena(api_key, org_id, model, query, *args, **kwargs):
            return mock_bash_data

        mock_search_athena.side_effect = mocked_search_athena
        mock_get_current_context.return_value = self.mock_context

        captured_output = io.StringIO()
        sys.stdout = captured_output  # Redirect stdout

        try:
            handle_get_bash_cmds(name_or_id=None, output="default", st=None, et=None)
        except Exception as e:
            print(f"Exception occurred: {e}")

        self.assertTrue(mock_search_athena.called)

        sys.stdout = sys.__stdout__  # Reset stdout

        output = captured_output.getvalue().strip()  # Remove extra spaces

        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(name, "vault-discovery-rolebinding")

        mock_get_current_context.assert_called_once()
        mock_search_athena.assert_called_once()

    # --------------------CONNECTION-BUNDLE------------------------------------

    @mock.patch("spyctl.commands.get.connection_bundles.search_athena")
    @mock.patch("spyctl.config.configs.get_current_context")
    def test_handle_get_bash_cmds(self, mock_get_current_context, mock_search_athena):

        mock_cb_data = [mock_data["CBUN"]]

        def mocked_search_athena(_api_key, _org_id, _model, _query, *args, **kwargs):
            return mock_cb_data

        mock_search_athena.side_effect = mocked_search_athena
        mock_get_current_context.return_value = self.mock_context

        captured_output = io.StringIO()
        sys.stdout = captured_output  # Redirect stdout

        try:
            handle_get_conn_buns(name_or_id=None, output="default", st=None, et=None)
        except Exception as e:
            print(f"Exception occurred: {e}")

        self.assertTrue(mock_search_athena.called)

        sys.stdout = sys.__stdout__  # Reset stdout

        output = captured_output.getvalue().strip()

        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(name, "vault-discovery-rolebinding")

        mock_get_current_context.assert_called_once()
        mock_search_athena.assert_called_once()

    # -------------------MACHINE------------------------------------

    @mock.patch("spyctl.commands.get.machines.search_athena")
    @mock.patch("spyctl.config.configs.get_current_context")
    def test_handle_get_machines(self, mock_get_current_context, mock_search_athena):

        mock_mach_data = [mock_data["Machine"]]

        def mocked_search_athena(_api_key, _org_id, _model, _query, *args, **kwargs):
            return mock_mach_data

        mock_search_athena.side_effect = mocked_search_athena
        mock_get_current_context.return_value = self.mock_context

        captured_output = io.StringIO()
        sys.stdout = captured_output  # Redirect stdout

        try:
            handle_get_machines(name_or_id=None, output="default", st=None, et=None)
        except Exception as e:
            print(f"Exception occurred: {e}")

        self.assertTrue(mock_search_athena.called)

        sys.stdout = sys.__stdout__  # Reset stdout

        output = captured_output.getvalue().strip()

        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(name, "vault-discovery-rolebinding")

        mock_get_current_context.assert_called_once()
        mock_search_athena.assert_called_once()

    # -------------------CUSTOM-FLAGS----------------------------------

    @mock.patch("spyctl.commands.get.custom_flags.cf_api.get_custom_flags")
    @mock.patch("spyctl.config.configs.get_current_context")
    @mock.patch("spyctl.commands.get.get_lib.show_get_data")
    def test_handle_get_custom_flags(
        self, mock_show_get_data, mock_get_current_context, mock_get_custom_flags
    ):
        """Test handle_get_custom_flags() with valid input"""

        mock_flags = [mock_data["Custom-Flag"]]

        mock_get_custom_flags.return_value = (mock_flags, 1)  # (data, total_pages)

        mock_get_current_context.return_value = self.mock_context

        captured_output = io.StringIO()
        sys.stdout = captured_output

        handle_get_custom_flags(name_or_id=None, output="default")

        sys.stdout = sys.__stdout__

        # mock_get_custom_flags.assert_called_once_with(
        #     "fake_api_key",
        #     "fake_org_id",
        #     name_or_uid_contains="mock",
        #     page=1,
        #     page_size=5,
        # )

        mock_show_get_data.assert_called_once()

        self.assertIn("mock_flag", str(mock_show_get_data.call_args))

    # -------------------SAVED-QUERIES---------------------------------

    @mock.patch("spyctl.commands.get.saved_queries.sq_api.get_saved_queries")
    @mock.patch("spyctl.config.configs.get_current_context")
    @mock.patch("spyctl.commands.get.get_lib.show_get_data")
    def test_handle_get_saved_queries(
        self, mock_show_get_data, mock_get_current_context, mock_get_saved_queries
    ):
        """Test handle_get_saved_queries() with valid input"""

        mock_saved_query = [mock_data["Saved-Query"]]

        mock_get_saved_queries.return_value = (mock_saved_query, 1)

        mock_get_current_context.return_value = self.mock_context

        captured_output = io.StringIO()
        sys.stdout = captured_output

        handle_get_saved_queries(name_or_id=None, output="default")

        sys.stdout = sys.__stdout__

        # output = captured_output.getvalue()
        # print("Captured Output:\n", output)

        self.assertIn("mock-query", str(mock_show_get_data.call_args))


if __name__ == "__main__":
    unittest.main()
