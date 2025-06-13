"""Tests for the Kubernetes MCP server."""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import pytest
from mcp.types import ListResourcesResult, ReadResourceResult, CallToolResult

from mcp_kubernetes.server import KubernetesMCPServer


@pytest.fixture
def mock_k8s_config():
    """Mock Kubernetes configuration loading."""
    with patch("mcp_kubernetes.server.config") as mock_config:
        yield mock_config


@pytest.fixture
def mock_k8s_client():
    """Mock Kubernetes client APIs."""
    with patch("mcp_kubernetes.server.client") as mock_client:
        # Mock CoreV1Api
        mock_core_v1 = MagicMock()
        mock_client.CoreV1Api.return_value = mock_core_v1
        
        # Mock AppsV1Api
        mock_apps_v1 = MagicMock()
        mock_client.AppsV1Api.return_value = mock_apps_v1
        
        yield {
            "core_v1": mock_core_v1,
            "apps_v1": mock_apps_v1,
            "client": mock_client
        }


@pytest.fixture
def server(mock_k8s_config, mock_k8s_client):
    """Create a KubernetesMCPServer instance with mocked dependencies."""
    return KubernetesMCPServer()


class TestKubernetesMCPServer:
    """Test cases for KubernetesMCPServer."""

    def test_init(self, server):
        """Test server initialization."""
        assert server.server.name == "kubernetes-mcp"
        assert server.kubeconfig_path is None
        assert server.v1_core is None
        assert server.v1_apps is None

    def test_init_with_kubeconfig(self, mock_k8s_config, mock_k8s_client):
        """Test server initialization with custom kubeconfig."""
        server = KubernetesMCPServer(kubeconfig_path="/custom/kubeconfig")
        assert server.kubeconfig_path == "/custom/kubeconfig"

    @pytest.mark.asyncio
    async def test_list_resources(self, server):
        """Test listing available resources."""
        # Get the list_resources handler
        handlers = server.server._resource_handlers
        list_handler = handlers.get("list_resources")
        assert list_handler is not None
        
        # Call the handler
        result = await list_handler()
        
        assert isinstance(result, ListResourcesResult)
        assert len(result.resources) == 4
        
        resource_uris = [r.uri for r in result.resources]
        assert "k8s://pods" in resource_uris
        assert "k8s://services" in resource_uris
        assert "k8s://deployments" in resource_uris
        assert "k8s://namespaces" in resource_uris

    @pytest.mark.asyncio
    async def test_read_pods_resource(self, server, mock_k8s_client):
        """Test reading pods resource."""
        # Mock pod data
        mock_pod = MagicMock()
        mock_pod.metadata.name = "test-pod"
        mock_pod.metadata.namespace = "default"
        mock_pod.metadata.creation_timestamp = datetime.now()
        mock_pod.status.phase = "Running"
        mock_pod.status.container_statuses = [MagicMock(ready=True)]
        mock_pod.spec.containers = [MagicMock()]
        mock_pod.spec.node_name = "test-node"
        mock_pod.status.pod_ip = "10.0.0.1"
        
        mock_response = MagicMock()
        mock_response.items = [mock_pod]
        mock_k8s_client["core_v1"].list_pod_for_all_namespaces.return_value = mock_response
        
        # Ensure connection is established
        server.v1_core = mock_k8s_client["core_v1"]
        server.v1_apps = mock_k8s_client["apps_v1"]
        
        # Get the read_resource handler
        handlers = server.server._resource_handlers
        read_handler = handlers.get("read_resource")
        assert read_handler is not None
        
        # Call the handler
        result = await read_handler("k8s://pods")
        
        assert isinstance(result, ReadResourceResult)
        assert len(result.contents) == 1
        
        # Parse the JSON content
        content_text = result.contents[0].text
        pods_data = json.loads(content_text)
        
        assert len(pods_data) == 1
        assert pods_data[0]["name"] == "test-pod"
        assert pods_data[0]["namespace"] == "default"
        assert pods_data[0]["status"] == "Running"

    @pytest.mark.asyncio
    async def test_read_services_resource(self, server, mock_k8s_client):
        """Test reading services resource."""
        # Mock service data
        mock_service = MagicMock()
        mock_service.metadata.name = "test-service"
        mock_service.metadata.namespace = "default"
        mock_service.metadata.creation_timestamp = datetime.now()
        mock_service.spec.type = "ClusterIP"
        mock_service.spec.cluster_ip = "10.96.0.1"
        mock_service.spec.ports = [MagicMock(port=80, target_port=8080, protocol="TCP")]
        mock_service.spec.selector = {"app": "test"}
        
        mock_response = MagicMock()
        mock_response.items = [mock_service]
        mock_k8s_client["core_v1"].list_service_for_all_namespaces.return_value = mock_response
        
        # Ensure connection is established
        server.v1_core = mock_k8s_client["core_v1"]
        server.v1_apps = mock_k8s_client["apps_v1"]
        
        # Get the read_resource handler
        handlers = server.server._resource_handlers
        read_handler = handlers.get("read_resource")
        assert read_handler is not None
        
        # Call the handler
        result = await read_handler("k8s://services")
        
        assert isinstance(result, ReadResourceResult)
        assert len(result.contents) == 1
        
        # Parse the JSON content
        content_text = result.contents[0].text
        services_data = json.loads(content_text)
        
        assert len(services_data) == 1
        assert services_data[0]["name"] == "test-service"
        assert services_data[0]["type"] == "ClusterIP"

    @pytest.mark.asyncio
    async def test_read_deployments_resource(self, server, mock_k8s_client):
        """Test reading deployments resource."""
        # Mock deployment data
        mock_deployment = MagicMock()
        mock_deployment.metadata.name = "test-deployment"
        mock_deployment.metadata.namespace = "default"
        mock_deployment.metadata.creation_timestamp = datetime.now()
        mock_deployment.spec.replicas = 3
        mock_deployment.status.ready_replicas = 3
        mock_deployment.status.updated_replicas = 3
        mock_deployment.status.available_replicas = 3
        mock_deployment.spec.selector.match_labels = {"app": "test"}
        
        mock_response = MagicMock()
        mock_response.items = [mock_deployment]
        mock_k8s_client["apps_v1"].list_deployment_for_all_namespaces.return_value = mock_response
        
        # Ensure connection is established
        server.v1_core = mock_k8s_client["core_v1"]
        server.v1_apps = mock_k8s_client["apps_v1"]
        
        # Get the read_resource handler
        handlers = server.server._resource_handlers
        read_handler = handlers.get("read_resource")
        assert read_handler is not None
        
        # Call the handler
        result = await read_handler("k8s://deployments")
        
        assert isinstance(result, ReadResourceResult)
        assert len(result.contents) == 1
        
        # Parse the JSON content
        content_text = result.contents[0].text
        deployments_data = json.loads(content_text)
        
        assert len(deployments_data) == 1
        assert deployments_data[0]["name"] == "test-deployment"
        assert deployments_data[0]["replicas"] == 3

    @pytest.mark.asyncio
    async def test_read_namespaces_resource(self, server, mock_k8s_client):
        """Test reading namespaces resource."""
        # Mock namespace data
        mock_namespace = MagicMock()
        mock_namespace.metadata.name = "test-namespace"
        mock_namespace.metadata.creation_timestamp = datetime.now()
        mock_namespace.status.phase = "Active"
        mock_namespace.metadata.labels = {"env": "test"}
        
        mock_response = MagicMock()
        mock_response.items = [mock_namespace]
        mock_k8s_client["core_v1"].list_namespace.return_value = mock_response
        
        # Ensure connection is established
        server.v1_core = mock_k8s_client["core_v1"]
        server.v1_apps = mock_k8s_client["apps_v1"]
        
        # Get the read_resource handler
        handlers = server.server._resource_handlers
        read_handler = handlers.get("read_resource")
        assert read_handler is not None
        
        # Call the handler
        result = await read_handler("k8s://namespaces")
        
        assert isinstance(result, ReadResourceResult)
        assert len(result.contents) == 1
        
        # Parse the JSON content
        content_text = result.contents[0].text
        namespaces_data = json.loads(content_text)
        
        assert len(namespaces_data) == 1
        assert namespaces_data[0]["name"] == "test-namespace"
        assert namespaces_data[0]["status"] == "Active"

    @pytest.mark.asyncio
    async def test_read_resource_with_namespace_filter(self, server, mock_k8s_client):
        """Test reading resource with namespace filter."""
        # Mock pod data
        mock_pod = MagicMock()
        mock_pod.metadata.name = "test-pod"
        mock_pod.metadata.namespace = "production"
        mock_pod.metadata.creation_timestamp = datetime.now()
        mock_pod.status.phase = "Running"
        mock_pod.status.container_statuses = [MagicMock(ready=True)]
        mock_pod.spec.containers = [MagicMock()]
        mock_pod.spec.node_name = "test-node"
        mock_pod.status.pod_ip = "10.0.0.1"
        
        mock_response = MagicMock()
        mock_response.items = [mock_pod]
        mock_k8s_client["core_v1"].list_namespaced_pod.return_value = mock_response
        
        # Ensure connection is established
        server.v1_core = mock_k8s_client["core_v1"]
        server.v1_apps = mock_k8s_client["apps_v1"]
        
        # Get the read_resource handler
        handlers = server.server._resource_handlers
        read_handler = handlers.get("read_resource")
        assert read_handler is not None
        
        # Call the handler with namespace filter
        result = await read_handler("k8s://pods?namespace=production")
        
        assert isinstance(result, ReadResourceResult)
        # Verify the correct namespaced method was called
        mock_k8s_client["core_v1"].list_namespaced_pod.assert_called_once_with(namespace="production")

    @pytest.mark.asyncio
    async def test_read_resource_unknown_uri(self, server):
        """Test reading resource with unknown URI."""
        # Ensure connection is established
        server.v1_core = MagicMock()
        server.v1_apps = MagicMock()
        
        # Get the read_resource handler
        handlers = server.server._resource_handlers
        read_handler = handlers.get("read_resource")
        assert read_handler is not None
        
        # Call the handler with unknown URI
        result = await read_handler("k8s://unknown")
        
        assert isinstance(result, ReadResourceResult)
        assert len(result.contents) == 1
        assert "Error reading resource" in result.contents[0].text

    @pytest.mark.asyncio
    async def test_list_tools(self, server):
        """Test listing available tools."""
        # Get the list_tools handler
        handlers = server.server._tool_handlers
        list_handler = handlers.get("list_tools")
        assert list_handler is not None
        
        # Call the handler
        tools = await list_handler()
        
        assert len(tools) == 2
        
        tool_names = [tool.name for tool in tools]
        assert "get_pod_logs" in tool_names
        assert "scale_deployment" in tool_names

    @pytest.mark.asyncio
    async def test_get_pod_logs_tool(self, server, mock_k8s_client):
        """Test get_pod_logs tool."""
        # Mock log response
        mock_logs = "2023-01-01 12:00:00 INFO Starting application\n2023-01-01 12:00:01 INFO Ready"
        mock_k8s_client["core_v1"].read_namespaced_pod_log.return_value = mock_logs
        
        # Ensure connection is established
        server.v1_core = mock_k8s_client["core_v1"]
        server.v1_apps = mock_k8s_client["apps_v1"]
        
        # Get the call_tool handler
        handlers = server.server._tool_handlers
        call_handler = handlers.get("call_tool")
        assert call_handler is not None
        
        # Call the handler
        result = await call_handler("get_pod_logs", {"pod_name": "test-pod", "namespace": "default"})
        
        assert isinstance(result, CallToolResult)
        assert len(result.content) == 1
        assert mock_logs in result.content[0].text
        
        # Verify the correct method was called
        mock_k8s_client["core_v1"].read_namespaced_pod_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_namespace_from_uri(self, server):
        """Test namespace extraction from URI."""
        # Test with namespace parameter
        namespace = server._extract_namespace_from_uri("k8s://pods?namespace=production")
        assert namespace == "production"
        
        # Test with multiple parameters
        namespace = server._extract_namespace_from_uri("k8s://pods?namespace=test&limit=10")
        assert namespace == "test"
        
        # Test without namespace parameter
        namespace = server._extract_namespace_from_uri("k8s://pods")
        assert namespace is None
        
        # Test with other parameters only
        namespace = server._extract_namespace_from_uri("k8s://pods?limit=10")
        assert namespace is None

    @pytest.mark.asyncio
    async def test_ensure_connected_success(self, server, mock_k8s_config, mock_k8s_client):
        """Test successful connection establishment."""
        # Mock successful configuration loading
        mock_k8s_config.load_kube_config.return_value = None
        
        # Mock successful namespace list (connection test)
        mock_k8s_client["core_v1"].list_namespace.return_value = MagicMock()
        
        # Test connection
        await server._ensure_connected()
        
        assert server.v1_core is not None
        assert server.v1_apps is not None
        
        # Verify configuration was loaded
        mock_k8s_config.load_kube_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_connected_with_custom_kubeconfig(self, mock_k8s_config, mock_k8s_client):
        """Test connection with custom kubeconfig path."""
        server = KubernetesMCPServer(kubeconfig_path="/custom/kubeconfig")
        
        # Mock successful configuration loading
        mock_k8s_config.load_kube_config.return_value = None
        
        # Mock successful namespace list (connection test)
        mock_k8s_client["core_v1"].list_namespace.return_value = MagicMock()
        
        # Test connection
        await server._ensure_connected()
        
        # Verify custom kubeconfig was used
        mock_k8s_config.load_kube_config.assert_called_once_with(config_file="/custom/kubeconfig")

    @pytest.mark.asyncio
    async def test_ensure_connected_in_cluster_fallback(self, server, mock_k8s_config, mock_k8s_client):
        """Test in-cluster config fallback."""
        # Mock in-cluster config failure, then local config success
        mock_k8s_config.load_incluster_config.side_effect = mock_k8s_config.ConfigException("Not in cluster")
        mock_k8s_config.load_kube_config.return_value = None
        
        # Mock successful namespace list (connection test)
        mock_k8s_client["core_v1"].list_namespace.return_value = MagicMock()
        
        # Test connection
        await server._ensure_connected()
        
        # Verify both methods were tried
        mock_k8s_config.load_incluster_config.assert_called_once()
        mock_k8s_config.load_kube_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_connected_failure(self, server, mock_k8s_config, mock_k8s_client):
        """Test connection failure handling."""
        # Mock configuration loading failure
        mock_k8s_config.load_incluster_config.side_effect = mock_k8s_config.ConfigException("Not in cluster")
        mock_k8s_config.load_kube_config.side_effect = mock_k8s_config.ConfigException("Config not found")
        
        # Test connection failure
        with pytest.raises(ConnectionError, match="Cannot connect to Kubernetes cluster"):
            await server._ensure_connected()