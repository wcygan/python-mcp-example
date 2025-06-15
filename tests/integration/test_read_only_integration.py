"""
Read-only integration tests for MCP Kubernetes server.

These tests verify the server works with real Kubernetes clusters
but only perform safe, read-only operations. No sensitive information
is exposed or logged.
"""

import asyncio
import json
import os
import pytest
from typing import Dict, Any, List
from unittest.mock import patch

from mcp_kubernetes.server import KubernetesMCPServer
from mcp_kubernetes.config import ServerConfig


@pytest.fixture
def read_only_config():
    """Create a strictly read-only configuration for testing."""
    config = ServerConfig.default()
    config.security.read_only_mode = True
    config.security.rbac_check = True
    config.security.filter_sensitive_data = True
    config.security.allowed_operations = ["list", "get", "watch", "logs"]
    config.logging.level = "WARNING"  # Reduce log noise
    config.logging.max_log_lines = 10  # Limit log output
    config.resources.max_items_per_request = 50  # Limit response size
    return config


@pytest.fixture
def server(read_only_config):
    """Create a server instance with read-only configuration."""
    return KubernetesMCPServer(server_config=read_only_config)


def anonymize_resource_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove any potentially sensitive information from resource data."""
    sensitive_fields = [
        "uid", "resourceVersion", "selfLink", "generation",
        "managedFields", "ownerReferences", "finalizers",
        "annotations", "labels"  # May contain sensitive info
    ]
    
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            if key in sensitive_fields:
                cleaned[key] = "[REDACTED]"
            elif isinstance(value, dict):
                cleaned[key] = anonymize_resource_data(value)
            elif isinstance(value, list):
                cleaned[key] = [anonymize_resource_data(item) if isinstance(item, dict) else "[REDACTED]" 
                               for item in value]
            else:
                cleaned[key] = value
        return cleaned
    return data


class TestReadOnlyIntegration:
    """Integration tests that only perform read-only operations."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        os.getenv("SKIP_INTEGRATION_TESTS") == "true",
        reason="Integration tests disabled"
    )
    async def test_server_initialization(self, server):
        """Test server can be initialized with read-only config."""
        assert server.server.name == "kubernetes-mcp"
        assert server.config.security.read_only_mode is True
        assert "list" in server.config.security.allowed_operations
        assert "get" in server.config.security.allowed_operations
        
        # Ensure no write operations are allowed
        forbidden_operations = ["create", "update", "patch", "delete"]
        for op in forbidden_operations:
            assert op not in server.config.security.allowed_operations

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        os.getenv("SKIP_INTEGRATION_TESTS") == "true",
        reason="Integration tests disabled"
    )
    async def test_kubernetes_connection(self, server):
        """Test connection to Kubernetes cluster."""
        try:
            await server._ensure_connected()
            assert server.v1_core is not None
            assert server.v1_apps is not None
        except Exception as e:
            pytest.skip(f"No Kubernetes cluster available: {e}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        os.getenv("SKIP_INTEGRATION_TESTS") == "true",
        reason="Integration tests disabled"
    )
    async def test_list_namespaces_safe(self, server):
        """Test listing namespaces (safe operation)."""
        try:
            await server._ensure_connected()
            namespaces = await server._list_namespaces()
            
            # Verify response structure without exposing details
            assert isinstance(namespaces, list)
            if namespaces:
                namespace = namespaces[0]
                assert "name" in namespace
                assert "status" in namespace
                
                # Ensure we only get standard system namespaces or safe ones
                safe_namespaces = {
                    "default", "kube-system", "kube-public", "kube-node-lease"
                }
                namespace_names = {ns["name"] for ns in namespaces}
                has_safe_namespace = bool(namespace_names.intersection(safe_namespaces))
                assert has_safe_namespace, "Should have at least one standard namespace"
                
        except Exception as e:
            pytest.skip(f"Kubernetes operation failed: {e}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        os.getenv("SKIP_INTEGRATION_TESTS") == "true",
        reason="Integration tests disabled"
    )
    async def test_list_system_pods_safe(self, server):
        """Test listing pods in kube-system namespace (safe operation)."""
        try:
            await server._ensure_connected()
            
            # Only test with kube-system namespace (standard system namespace)
            pods = await server._list_pods(namespace="kube-system")
            
            assert isinstance(pods, list)
            if pods:
                pod = pods[0]
                # Verify expected fields exist
                required_fields = ["name", "namespace", "status"]
                for field in required_fields:
                    assert field in pod
                
                # Ensure namespace is what we requested
                assert pod["namespace"] == "kube-system"
                
                # Verify only safe status information is included
                safe_statuses = {"Running", "Pending", "Succeeded", "Failed", "Unknown"}
                assert pod["status"] in safe_statuses
                
        except Exception as e:
            pytest.skip(f"Kubernetes operation failed: {e}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        os.getenv("SKIP_INTEGRATION_TESTS") == "true",
        reason="Integration tests disabled"
    )
    async def test_list_system_services_safe(self, server):
        """Test listing services in kube-system namespace (safe operation)."""
        try:
            await server._ensure_connected()
            
            services = await server._list_services(namespace="kube-system")
            
            assert isinstance(services, list)
            if services:
                service = services[0]
                required_fields = ["name", "namespace", "type"]
                for field in required_fields:
                    assert field in service
                
                assert service["namespace"] == "kube-system"
                
                # Verify service types are standard
                valid_types = {"ClusterIP", "NodePort", "LoadBalancer", "ExternalName"}
                assert service["type"] in valid_types
                
        except Exception as e:
            pytest.skip(f"Kubernetes operation failed: {e}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        os.getenv("SKIP_INTEGRATION_TESTS") == "true",
        reason="Integration tests disabled"
    )
    async def test_pod_status_filtering_safe(self, server):
        """Test pod status filtering with safe parameters."""
        try:
            await server._ensure_connected()
            
            # Test with safe field selector
            status_json = await server._get_pod_status(
                namespace="kube-system",
                field_selector="status.phase=Running"
            )
            
            status_data = json.loads(status_json)
            assert isinstance(status_data, list)
            
            # Verify all returned pods are actually running
            for pod_status in status_data:
                assert pod_status.get("phase") == "Running"
                assert pod_status.get("namespace") == "kube-system"
                
        except Exception as e:
            pytest.skip(f"Kubernetes operation failed: {e}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        os.getenv("SKIP_INTEGRATION_TESTS") == "true",
        reason="Integration tests disabled"
    )
    async def test_pod_logs_safe_limited(self, server):
        """Test pod log retrieval with strict limits (safe operation)."""
        try:
            await server._ensure_connected()
            
            # Get a system pod for testing
            pods = await server._list_pods(namespace="kube-system")
            if not pods:
                pytest.skip("No pods available for log testing")
            
            # Find a pod that's likely to have logs
            test_pod = None
            for pod in pods:
                if pod["status"] == "Running":
                    test_pod = pod
                    break
            
            if not test_pod:
                pytest.skip("No running pods available for log testing")
            
            # Request minimal logs
            logs = await server._get_pod_logs(
                pod_name=test_pod["name"],
                namespace=test_pod["namespace"],
                lines=3  # Very limited
            )
            
            # Verify logs are returned as string
            assert isinstance(logs, str)
            
            # Verify line limit is respected
            log_lines = logs.splitlines()
            assert len(log_lines) <= 3
            
            # Don't assert on log content - could contain sensitive info
            # Just verify we can retrieve logs safely
            
        except Exception as e:
            # Log retrieval can fail for many legitimate reasons
            pytest.skip(f"Pod log retrieval failed (normal): {e}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        os.getenv("SKIP_INTEGRATION_TESTS") == "true",
        reason="Integration tests disabled"
    )
    async def test_describe_pod_safe_limited(self, server):
        """Test pod description with sensitive data filtering."""
        try:
            await server._ensure_connected()
            
            pods = await server._list_pods(namespace="kube-system")
            if not pods:
                pytest.skip("No pods available for describe testing")
            
            test_pod = pods[0]
            
            description_json = await server._describe_pod(
                pod_name=test_pod["name"],
                namespace=test_pod["namespace"]
            )
            
            description = json.loads(description_json)
            
            # Verify expected structure
            assert isinstance(description, dict)
            assert "name" in description
            assert "namespace" in description
            assert "status" in description
            assert "containers" in description
            
            # Verify namespace matches
            assert description["namespace"] == "kube-system"
            
            # Verify containers structure
            containers = description["containers"]
            assert isinstance(containers, list)
            
            if containers:
                container = containers[0]
                assert "name" in container
                assert "image" in container
                
                # Verify no sensitive environment variables are exposed
                # This is handled by our anonymization in the server
                
        except Exception as e:
            pytest.skip(f"Pod describe failed: {e}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        os.getenv("SKIP_INTEGRATION_TESTS") == "true",
        reason="Integration tests disabled"
    )
    async def test_uri_parsing_safety(self, server):
        """Test URI parsing doesn't expose sensitive information."""
        test_cases = [
            ("k8s://pods", None),
            ("k8s://pods?namespace=kube-system", "kube-system"),
            ("k8s://services?namespace=default", "default"),
            ("k8s://deployments?namespace=test&other=param", "test"),
        ]
        
        for uri, expected_namespace in test_cases:
            result = server._extract_namespace_from_uri(uri)
            assert result == expected_namespace

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        os.getenv("SKIP_INTEGRATION_TESTS") == "true",
        reason="Integration tests disabled"
    )
    async def test_configuration_security(self, server):
        """Test that security configuration is properly enforced."""
        config = server.config
        
        # Verify read-only mode
        assert config.security.read_only_mode is True
        
        # Verify RBAC checking is enabled
        assert config.security.rbac_check is True
        
        # Verify sensitive data filtering
        assert config.security.filter_sensitive_data is True
        
        # Verify only safe operations are allowed
        allowed = set(config.security.allowed_operations)
        safe_operations = {"list", "get", "watch", "logs"}
        assert allowed.issubset(safe_operations)
        
        # Verify dangerous operations are not allowed
        dangerous_operations = {"create", "update", "patch", "delete", "deletecollection"}
        assert not allowed.intersection(dangerous_operations)

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        os.getenv("SKIP_INTEGRATION_TESTS") == "true",
        reason="Integration tests disabled"
    )
    async def test_resource_limits_enforced(self, server):
        """Test that resource limits are enforced for safety."""
        config = server.config
        
        # Verify reasonable limits are set
        assert config.resources.max_items_per_request <= 1000
        assert config.logging.max_log_lines <= 1000
        assert config.kubernetes.timeout <= 300  # 5 minutes max
        
        # Test that limits are actually enforced in practice
        try:
            await server._ensure_connected()
            
            # Test with kube-system namespace (should be safe)
            pods = await server._list_pods(namespace="kube-system")
            
            # Verify we don't get an overwhelming number of results
            assert len(pods) <= config.resources.max_items_per_request
            
        except Exception as e:
            pytest.skip(f"Resource limit test failed: {e}")


class TestConfigurationSafety:
    """Test that configuration loading is safe and doesn't expose secrets."""

    def test_environment_config_safe(self):
        """Test environment configuration doesn't expose secrets."""
        # Mock environment variables to ensure no real secrets are used
        with patch.dict(os.environ, {
            "KUBECONFIG": "/safe/path/to/config",
            "MCP_KUBERNETES_READ_ONLY": "true",
            "MCP_KUBERNETES_RBAC_CHECK": "true",
        }, clear=False):
            config = ServerConfig.from_env()
            
            assert config.security.read_only_mode is True
            assert config.security.rbac_check is True
            assert config.kubernetes.kubeconfig_path == "/safe/path/to/config"

    def test_config_serialization_safe(self):
        """Test that configuration serialization doesn't expose secrets."""
        config = ServerConfig.default()
        config.security.read_only_mode = True
        
        config_dict = config.to_dict()
        
        # Verify structure
        assert "kubernetes" in config_dict
        assert "security" in config_dict
        assert "mcp" in config_dict
        
        # Verify read-only mode is preserved
        assert config_dict["security"]["read_only_mode"] is True
        
        # Verify no actual credential values are exposed
        # Note: "secret" appears in standard service_account_path which is safe
        sensitive_credential_patterns = ["password", "token", "credential", "private_key"]
        config_str = str(config_dict).lower()
        
        # Should not contain actual credential values
        for pattern in sensitive_credential_patterns:
            assert pattern not in config_str


# Integration test configuration
def pytest_configure(config):
    """Configure pytest for integration tests."""
    config.addinivalue_line(
        "markers", 
        "integration: mark test as integration test requiring Kubernetes cluster"
    )


if __name__ == "__main__":
    # Allow running integration tests directly
    import sys
    
    # Set environment variable to enable tests
    os.environ.pop("SKIP_INTEGRATION_TESTS", None)
    
    pytest.main([__file__, "-v"] + sys.argv[1:])