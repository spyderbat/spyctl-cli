# pylint: disable=broad-except

import contextlib
import io
import json
import sys
import unittest
from unittest import mock

from click.testing import CliRunner

from spyctl.commands.get.agents import handle_get_agents
from spyctl.commands.get.bash_cmds import handle_get_bash_cmds
from spyctl.commands.get.clusterrolebindings import handle_get_clusterrolebindings
from spyctl.commands.get.clusterroles import handle_get_clusterroles
from spyctl.commands.get.connection_bundles import handle_get_conn_buns
from spyctl.commands.get.custom_flags import handle_get_custom_flags
from spyctl.commands.get.deployments import handle_get_deployments
from spyctl.commands.get.deviations import handle_get_deviations
from spyctl.commands.get.fingerprints import handle_get_fingerprints
from spyctl.commands.get.machines import handle_get_machines
from spyctl.commands.get.namespaces import handle_get_namespaces
from spyctl.commands.get.nodes import handle_get_nodes
from spyctl.commands.get.opsflags import handle_get_opsflags
from spyctl.commands.get.pods import handle_get_pods
from spyctl.commands.get.redflags import handle_get_redflags
from spyctl.commands.get.rolebindings import handle_get_rolebindings
from spyctl.commands.get.roles import handle_get_roles
from spyctl.commands.get.saved_queries import handle_get_saved_queries
from spyctl.commands.get.spydertraces import handle_get_spydertraces
from spyctl.commands.get.top_data import handle_get_top_data
from spyctl.config.configs import Context

with open("spyctl/tests/testdata_resource.json", "r") as file:
    mock_data = json.load(file)


class TestGetResources(unittest.TestCase):
    def setUp(self):
        self.mock_context = mock.Mock(spec=Context)
        self.mock_context.get_api_data.return_value = ("fake_api_key", "fake_org_id")

    # --------------------PODS------------------------------------

    @mock.patch("spyctl.commands.get.pods.search_full_json")
    @mock.patch("spyctl.config.configs.get_current_context")
    @mock.patch("spyctl.commands.get.pods.lib.query_builder")
    def test_handle_get_pods(
        self, mock_query_builder, mock_get_current_context, mock_search_full_json
    ):
        mock_pod_data = [mock_data["Pod"]]
        mock_query = 'kind="Pod"'

        def mocked_search_full_json(_api_key, _org_id, _model, query, *args, **kwargs):
            assert query == mock_query
            return mock_pod_data

        mock_search_full_json.side_effect = mocked_search_full_json
        mock_get_current_context.return_value = self.mock_context
        mock_query_builder.return_value = mock_query

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

        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(name, "mock_pod")

        self.assertTrue(mock_search_full_json.called)

        mock_get_current_context.assert_called_once()
        mock_search_full_json.assert_called_once()
        self.assertEqual(name, "mock_pod")

    # --------------------NODES------------------------------------
    @mock.patch("spyctl.commands.get.nodes.search_full_json")
    @mock.patch("spyctl.config.configs.get_current_context")
    @mock.patch("spyctl.commands.get.nodes.lib.query_builder")
    def test_handle_get_nodes(
        self, mock_query_builder, mock_get_current_context, mock_search_full_json
    ):
        mock_nodes_data = [mock_data["Node"]]
        mock_query = 'kind="Node"'

        # Proper side effect that accepts all positional args expected by the real function
        def mocked_search_full_json(_api_key, _org_id, _model, query, *args, **kwargs):
            assert query == mock_query
            return mock_nodes_data

        mock_search_full_json.side_effect = mocked_search_full_json
        mock_get_current_context.return_value = self.mock_context
        mock_query_builder.return_value = mock_query

        captured_output = io.StringIO()
        sys.stdout = captured_output

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

        sys.stdout = sys.__stdout__
        output = captured_output.getvalue().strip()
        # Split output into lines and extract the second line (actual data)
        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(name, "mock_node")

        self.assertTrue(mock_search_full_json.called)

        mock_get_current_context.assert_called_once()
        mock_search_full_json.assert_called_once()
        self.assertEqual(name, "mock_node")

    # --------------------DEPLOYMENT------------------------------------
    @mock.patch("spyctl.commands.get.deployments.search_full_json")
    @mock.patch("spyctl.config.configs.get_current_context")
    @mock.patch("spyctl.commands.get.deployments.lib.query_builder")
    def test_handle_get_deployments(
        self, mock_query_builder, mock_get_current_context, mock_search_full_json
    ):
        mock_deployments_data = [mock_data["Deployment"]]  # Mock deployment data
        mock_query = 'kind="Deployment"'  # Define the expected query

        def mocked_search_full_json(
            _api_key,
            _org_id,
            _model,
            query,
            *args,
            **kwargs,
        ):
            assert query == mock_query
            return mock_deployments_data

        mock_search_full_json.side_effect = mocked_search_full_json
        mock_get_current_context.return_value = self.mock_context
        mock_query_builder.return_value = mock_query  # Mock the query builder

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

        self.assertTrue(mock_search_full_json.called)
        mock_get_current_context.assert_called_once()
        mock_search_full_json.assert_called_once()
        mock_query_builder.assert_called_once()  # Assert query builder was called

        sys.stdout = sys.__stdout__  # Reset stdout

        output = captured_output.getvalue().strip()  # Remove extra spaces

        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(name, "mock-deployment")

    # --------------------Namespace----------------------------------

    @mock.patch("spyctl.commands.get.namespaces.search_full_json")
    @mock.patch("spyctl.config.configs.get_current_context")
    @mock.patch("spyctl.commands.get.namespaces.lib.query_builder")
    def test_handle_get_namespace(
        self, mock_query_builder, mock_get_current_context, mock_search_full_json
    ):
        mock_namespace_data = [mock_data["Namespace"]]  # Mock namespace data
        mock_query = 'kind="Namespace"'  # Define the expected query

        # Mock search_full_json function
        def mocked_search_full_json(
            _api_key,
            _org_id,
            _model,
            query,  # Capture the query argument
            *args,
            **kwargs,
        ):
            assert query == mock_query  # Assert the query is as expected
            return mock_namespace_data  # Returning mock namespace data

        mock_search_full_json.side_effect = mocked_search_full_json
        mock_get_current_context.return_value = self.mock_context
        mock_query_builder.return_value = mock_query  # Mock the query builder

        captured_output = io.StringIO()
        sys.stdout = captured_output  # Redirect stdout

        # Call handle_get_namespaces directly
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

        self.assertTrue(mock_search_full_json.called)
        mock_get_current_context.assert_called_once()
        mock_search_full_json.assert_called_once()
        mock_query_builder.assert_called_once()  # Assert query builder was called

        sys.stdout = sys.__stdout__  # Reset stdout

        output = captured_output.getvalue().strip()  # Remove extra spaces

        # Split output into lines and extract the second line (actual data)
        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(name, "mock-namespace")

    # -----------------Redflags----------------------------
    @mock.patch("spyctl.commands.get.redflags.search_full_json")
    @mock.patch("spyctl.config.configs.get_current_context")
    @mock.patch("spyctl.commands.get.redflags.lib.query_builder")
    def test_handle_get_redflags(
        self, mock_query_builder, mock_get_current_context, mock_search_full_json
    ):
        mock_redflags_data = [mock_data["Redflag"]]  # Mock redflag data
        mock_query = 'kind="Redflag"'  # Define the expected query

        # Mock search_full_json function
        def mocked_search_full_json(
            _api_key,
            _org_id,
            _model,
            query,  # Capture the query argument
            *args,
            **kwargs,
        ):
            assert query == mock_query  # Assert the query is as expected
            return mock_redflags_data  # Returning mock redflag data

        mock_search_full_json.side_effect = mocked_search_full_json
        mock_get_current_context.return_value = self.mock_context
        mock_query_builder.return_value = mock_query  # Mock the query builder

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

        self.assertTrue(mock_search_full_json.called)
        mock_get_current_context.assert_called_once()
        mock_search_full_json.assert_called_once()
        mock_query_builder.assert_called_once()  # Assert query builder was called

        sys.stdout = sys.__stdout__  # Reset stdout

        output = captured_output.getvalue().strip()  # Remove extra spaces

        lines = output.split("\n")
        if len(lines) > 1:
            flag = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(flag, "command_curl")

    # --------------------OPSFLAGS------------------------------------
    @mock.patch("spyctl.commands.get.opsflags.search_full_json")
    @mock.patch("spyctl.config.configs.get_current_context")
    @mock.patch("spyctl.commands.get.opsflags.lib.query_builder")
    def test_handle_get_opsflags(
        self, mock_query_builder, mock_get_current_context, mock_search_full_json
    ):
        mock_opsflags_data = [mock_data["Opsflag"]]  # Mock opsflag data
        mock_query = 'kind="Opsflag"'

        def mocked_search_full_json(_api_key, _org_id, _model, query, *args, **kwargs):
            assert query == mock_query
            return mock_opsflags_data

        mock_search_full_json.side_effect = mocked_search_full_json
        mock_get_current_context.return_value = self.mock_context
        mock_query_builder.return_value = mock_query

        captured_output = io.StringIO()
        sys.stdout = captured_output

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

        self.assertTrue(mock_search_full_json.called)
        mock_get_current_context.assert_called_once()
        mock_search_full_json.assert_called_once()
        mock_query_builder.assert_called_once()

        sys.stdout = sys.__stdout__

        output = captured_output.getvalue().strip()

        lines = output.split("\n")
        if len(lines) > 1:
            flag = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(flag, "memory_leak")

    # --------------------ROLES------------------------------
    @mock.patch("spyctl.commands.get.roles.search_full_json")
    @mock.patch("spyctl.config.configs.get_current_context")
    @mock.patch("spyctl.commands.get.roles.lib.query_builder")
    def test_handle_get_roles(
        self, mock_query_builder, mock_get_current_context, mock_search_full_json
    ):
        mock_roles_data = [mock_data["Role"]]  # Mock Role data
        mock_query = 'kind="Role"'

        def mocked_search_full_json(api_key, org_id, model, query, *args, **kwargs):
            assert query == mock_query
            return mock_roles_data  # Returning mock Role data

        mock_search_full_json.side_effect = mocked_search_full_json
        mock_get_current_context.return_value = self.mock_context
        mock_query_builder.return_value = mock_query

        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            handle_get_roles(name_or_id=None, output="default", st=None, et=None)
        except Exception as e:
            print(f"Exception occurred: {e}")
            self.fail("handle_get_roles raised an exception!")

        sys.stdout = sys.__stdout__

        output = captured_output.getvalue().strip()

        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(name, "vault-discovery-role")

        self.assertTrue(mock_search_full_json.called)
        mock_get_current_context.assert_called_once()
        mock_search_full_json.assert_called_once()
        mock_query_builder.assert_called_once()

    # --------------CLUSTERROLES-------------------------------------
    @mock.patch("spyctl.commands.get.clusterroles.search_full_json")
    @mock.patch("spyctl.config.configs.get_current_context")
    @mock.patch("spyctl.commands.get.clusterroles.lib.query_builder")
    def test_handle_get_clusterroles(
        self, mock_query_builder, mock_get_current_context, mock_search_full_json
    ):
        mock_clusterroles_data = [mock_data["ClusterRole"]]
        mock_query = 'kind="ClusterRole"'

        def mocked_search_full_json(api_key, org_id, model, query, *args, **kwargs):
            assert query == mock_query
            return mock_clusterroles_data  # Returning mock ClusterRole data

        mock_search_full_json.side_effect = mocked_search_full_json
        mock_get_current_context.return_value = self.mock_context
        mock_query_builder.return_value = mock_query

        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            handle_get_clusterroles(name_or_id=None, output="default", st=None, et=None)
        except Exception as e:
            print(f"Exception occurred: {e}")
            self.fail("handle_get_clusterroles raised an exception!")

        self.assertTrue(mock_search_full_json.called)
        mock_get_current_context.assert_called_once()
        mock_search_full_json.assert_called_once()
        mock_query_builder.assert_called_once()

        sys.stdout = sys.__stdout__

        output = captured_output.getvalue().strip()

        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(name, "vault-agent-injector-clusterrole")

    # --------------CLUSTERROLEBINDNING-------------------------------------
    @mock.patch("spyctl.commands.get.clusterrolebindings.search_full_json")
    @mock.patch("spyctl.config.configs.get_current_context")
    @mock.patch("spyctl.commands.get.clusterrolebindings.lib.query_builder")
    def test_handle_get_clusterrolebindings(
        self, mock_query_builder, mock_get_current_context, mock_search_full_json
    ):
        mock_crb_data = [mock_data["ClusterRoleBinding"]]  # Mock CRB data
        mock_query = 'kind="ClusterRoleBinding"'

        def mocked_search_full_json(_api_key, _org_id, _model, query, *args, **kwargs):
            assert query == mock_query
            return mock_crb_data  # Returning mock CRB data

        mock_search_full_json.side_effect = mocked_search_full_json
        mock_get_current_context.return_value = self.mock_context
        mock_query_builder.return_value = mock_query

        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            handle_get_clusterrolebindings(
                name_or_id=None, output="default", st=None, et=None
            )
        except Exception as e:
            print(f"Exception occurred: {e}")
            self.fail("handle_get_clusterrolebindings raised an exception!")

        self.assertTrue(mock_search_full_json.called)
        mock_get_current_context.assert_called_once()
        mock_search_full_json.assert_called_once()
        mock_query_builder.assert_called_once()

        sys.stdout = sys.__stdout__

        output = captured_output.getvalue().strip()

        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(name, "po-crb")

    # --------------ROLEBINDNING-------------------------------------
    @mock.patch("spyctl.commands.get.rolebindings.search_full_json")
    @mock.patch("spyctl.config.configs.get_current_context")
    @mock.patch("spyctl.commands.get.rolebindings.lib.query_builder")
    def test_handle_get_rolebindings(
        self, mock_query_builder, mock_get_current_context, mock_search_full_json
    ):
        mock_rolebindings_data = [mock_data["RoleBinding"]]
        mock_query = 'kind="RoleBinding"'

        def mocked_search_full_json(_api_key, _org_id, _model, query, *args, **kwargs):
            assert query == mock_query
            return mock_rolebindings_data

        mock_search_full_json.side_effect = mocked_search_full_json
        mock_get_current_context.return_value = self.mock_context
        mock_query_builder.return_value = mock_query

        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            handle_get_rolebindings(name_or_id=None, output="default", st=None, et=None)
        except Exception as e:
            print(f"Exception occurred: {e}")
            self.fail("handle_get_rolebindings raised an exception!")

        self.assertTrue(mock_search_full_json.called)
        mock_get_current_context.assert_called_once()
        mock_search_full_json.assert_called_once()
        mock_query_builder.assert_called_once()

        sys.stdout = sys.__stdout__

        output = captured_output.getvalue().strip()

        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(name, "vault-discovery-rolebinding")

    # --------------AGENTS-------------------------------------
    @mock.patch("spyctl.commands.get.agents.search_full_json")
    @mock.patch("spyctl.config.configs.get_current_context")
    @mock.patch("spyctl.commands.get.agents.ag_api.get_sources_data_for_agents")
    @mock.patch("spyctl.commands.get.agents.lib.query_builder")
    def test_handle_get_agents(
        self,
        mock_query_builder,
        mock_get_sources_data_for_agents,
        mock_get_current_context,
        mock_search_full_json,
    ):
        mock_agent_data = [mock_data["Agent"]]
        mock_source_data = mock_data["Source"]
        mock_query = 'kind="Agent"'

        def mocked_search_full_json(_api_key, _org_id, _model, query, *args, **kwargs):
            assert query == mock_query
            return mock_agent_data

        mock_search_full_json.side_effect = mocked_search_full_json
        mock_get_sources_data_for_agents.return_value = (
            mock_agent_data,
            mock_source_data,
        )
        mock_get_current_context.return_value = self.mock_context
        mock_query_builder.return_value = mock_query

        captured_output = io.StringIO()
        with contextlib.redirect_stdout(captured_output):
            handle_get_agents(name_or_id=None, output="default", st=None, et=None)

        output = captured_output.getvalue().strip()
        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[1].split()[0]

        self.assertTrue(mock_search_full_json.called)
        mock_get_current_context.assert_called_once()
        mock_search_full_json.assert_called_once()
        mock_get_sources_data_for_agents.assert_called_once()
        mock_query_builder.assert_called_once()

        self.assertEqual("ip-XXXXX.us-west-2.compute.internal", name)

    # ----------------SPYDERTRACE-------------------------------------
    @mock.patch("spyctl.commands.get.spydertraces.search_full_json")
    @mock.patch("spyctl.config.configs.get_current_context")
    @mock.patch("spyctl.commands.get.spydertraces.lib.query_builder")
    def test_handle_get_spydertraces(
        self, mock_query_builder, mock_get_current_context, mock_search_full_json
    ):
        mock_trace_data = [mock_data["Spydertrace"]]
        mock_query = 'kind="Spydertrace"'

        def mocked_search_full_json(_api_key, _org_id, _model, query, *args, **kwargs):
            assert query == mock_query
            return mock_trace_data

        mock_search_full_json.side_effect = mocked_search_full_json
        mock_get_current_context.return_value = self.mock_context
        mock_query_builder.return_value = mock_query

        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            handle_get_spydertraces(name_or_id=None, output="default", st=None, et=None)
        except Exception as e:
            print(f"Exception occurred: {e}")

        self.assertTrue(mock_search_full_json.called)
        mock_get_current_context.assert_called_once()
        mock_search_full_json.assert_called_once()
        mock_query_builder.assert_called_once()

        sys.stdout = sys.__stdout__

        output = captured_output.getvalue().strip()

        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[2].split()[1]

        self.assertEqual(name, "command_id")

    # # --------------------DEVIATION-------------------------------------
    @mock.patch("spyctl.commands.get.deviations.search_full_json")
    @mock.patch("spyctl.config.configs.get_current_context")
    @mock.patch("spyctl.commands.get.deviations.pol_api.get_policies")
    @mock.patch("spyctl.commands.get.deviations.lib.query_builder")
    def test_handle_get_deviations(
        self,
        mock_query_builder,
        mock_get_policies,
        mock_get_current_context,
        mock_search_full_json,
    ):
        # --- Setup ---
        mock_policy_data = mock_data["Policy"]
        mock_dev_data = [mock_data["Deviation"]]
        mock_query = 'namespace="dev"'

        mock_context = mock.Mock()
        mock_context.get_api_data.return_value = ("api_key", "org_id", "model")
        mock_get_current_context.return_value = mock_context

        mock_get_policies.return_value.json.return_value = mock_policy_data

        # Match the real function signature
        def mocked_search_full_json(api_key, org_id, model, query, *args, **kwargs):
            return mock_dev_data

        mock_search_full_json.side_effect = mocked_search_full_json

        captured_output = io.StringIO()
        with contextlib.redirect_stdout(captured_output):
            handle_get_deviations(name_or_id=None, output="raw", st=None, et=None)

        # --- Assertions ---
        output = captured_output.getvalue()
        self.assertTrue(mock_search_full_json.called)
        self.assertTrue(mock_get_policies.called)
        self.assertIn("045d6xxxxxxxx", output)
        mock_get_current_context.assert_called_once()
        mock_search_full_json.assert_called_once()
        mock_query_builder.assert_called_once()

    # --------------------FINGERPRINTS------------------------------------
    @mock.patch("spyctl.commands.get.fingerprints.search_full_json")
    @mock.patch("spyctl.config.configs.get_current_context")
    @mock.patch("spyctl.commands.get.fingerprints.lib.query_builder")
    def test_handle_get_fingerprints(
        self, mock_query_builder, mock_get_current_context, mock_search_full_json
    ):
        mock_fingerprint_data = [mock_data["Fingerprint"]]
        mock_query = 'kind="Fingerprint"'

        def mocked_search_full_json(_api_key, _org_id, _model, query, *args, **kwargs):
            return mock_fingerprint_data

        mock_search_full_json.side_effect = mocked_search_full_json
        mock_get_current_context.return_value = self.mock_context
        mock_query_builder.return_value = mock_query

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

        self.assertTrue(mock_search_full_json.called)
        mock_get_current_context.assert_called_once()
        mock_search_full_json.assert_called_once()
        mock_query_builder.assert_called_once()

        sys.stdout = sys.__stdout__  # Reset stdout

        output = captured_output.getvalue().strip()  # Remove extra spaces

        lines = output.split("\n")
        if len(lines) > 1:
            name = lines[1].split()[0]  # Extract first column (NAME)

        self.assertEqual(name, "systemd-gssproxy.service")

    # --------------------TOP-DATA------------------------------------
    @mock.patch("spyctl.commands.get.top_data.search_full_json")
    @mock.patch("spyctl.config.configs.get_current_context")
    @mock.patch("spyctl.commands.get.top_data.lib.query_builder")
    def test_handle_get_top_data(
        self,
        mock_query_builder,
        mock_get_current_context,
        mock_search_full_json,
    ):
        mock_top_data = [mock_data["Top-Data"]]
        mock_query = 'muid="mach:abc"'

        def mocked_search_full_json(api_key, org_id, model, query, *args, **kwargs):
            assert query == mock_query
            return mock_top_data  # Returning mock top data

        mock_search_full_json.side_effect = mocked_search_full_json
        mock_get_current_context.return_value = self.mock_context
        mock_query_builder.return_value = mock_query

        captured_output = io.StringIO()
        sys.stdout = captured_output  # Redirect stdout

        handle_get_top_data(
            name_or_id="top:mach:abc",
            output="json",
            st=None,
            et=None,
            muid_equals="mach:abc",
        )

        sys.stdout = sys.__stdout__  # Reset stdout

        output = captured_output.getvalue()
        self.assertIn("mach:abc", output)

        self.assertTrue(mock_search_full_json.called)
        mock_get_current_context.assert_called_once()
        mock_search_full_json.assert_called_once()
        mock_query_builder.assert_called_once()

    # -------------------CUSTOM-FLAGS----------------------------------

    @mock.patch("spyctl.commands.get.custom_flags.cf_api.get_custom_flags")
    @mock.patch("spyctl.config.configs.get_current_context")
    @mock.patch("spyctl.commands.get.get_lib.show_get_data")
    def test_handle_get_custom_flags(
        self, mock_show_get_data, mock_get_current_context, mock_get_custom_flags
    ):
        mock_flags = [mock_data["Custom-Flag"]]

        mock_get_custom_flags.return_value = (mock_flags, 1)  # (data, total_pages)

        mock_get_current_context.return_value = self.mock_context

        captured_output = io.StringIO()
        sys.stdout = captured_output

        handle_get_custom_flags(name_or_id=None, output="default")

        sys.stdout = sys.__stdout__

        mock_show_get_data.assert_called_once()

        self.assertIn("mock_flag", str(mock_show_get_data.call_args))

    # -------------------SAVED-QUERIES---------------------------------

    @mock.patch("spyctl.commands.get.saved_queries.sq_api.get_saved_queries")
    @mock.patch("spyctl.config.configs.get_current_context")
    @mock.patch("spyctl.commands.get.get_lib.show_get_data")
    def test_handle_get_saved_queries(
        self, mock_show_get_data, mock_get_current_context, mock_get_saved_queries
    ):
        mock_saved_query = [mock_data["Saved-Query"]]

        mock_get_saved_queries.return_value = (mock_saved_query, 1)

        mock_get_current_context.return_value = self.mock_context

        captured_output = io.StringIO()
        sys.stdout = captured_output

        handle_get_saved_queries(name_or_id=None, output="default")

        self.assertIn("mock-query", str(mock_show_get_data.call_args))


if __name__ == "__main__":
    unittest.main()
