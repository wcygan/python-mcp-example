"""Configuration for integration tests."""

import os
import pytest
from typing import Generator


def pytest_configure(config):
    """Configure pytest for integration tests."""
    config.addinivalue_line(
        "markers", 
        "integration: mark test as integration test requiring Kubernetes cluster"
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle integration test markers."""
    if config.getoption("--no-integration"):
        skip_integration = pytest.mark.skip(reason="Integration tests disabled")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)


def pytest_addoption(parser):
    """Add command line options for integration tests."""
    parser.addoption(
        "--no-integration",
        action="store_true",
        default=False,
        help="Skip integration tests"
    )
    parser.addoption(
        "--kubernetes-config",
        action="store",
        default=None,
        help="Path to kubeconfig file for integration tests"
    )


@pytest.fixture(scope="session")
def kubernetes_available() -> bool:
    """Check if Kubernetes cluster is available for testing."""
    try:
        import subprocess
        result = subprocess.run(
            ["kubectl", "cluster-info"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


@pytest.fixture(scope="session")
def integration_config() -> dict:
    """Provide configuration for integration tests."""
    return {
        "skip_if_no_cluster": os.getenv("SKIP_INTEGRATION_TESTS", "false").lower() == "true",
        "max_test_duration": 30,  # seconds
        "safe_namespaces": ["kube-system", "default", "kube-public"],
        "test_timeout": 10,  # seconds per operation
    }


@pytest.fixture
def safe_test_environment(monkeypatch) -> Generator[None, None, None]:
    """Ensure tests run in a safe environment with no sensitive data exposure."""
    # Set environment variables to safe defaults
    safe_env = {
        "MCP_KUBERNETES_READ_ONLY": "true",
        "MCP_KUBERNETES_RBAC_CHECK": "true", 
        "MCP_KUBERNETES_FILTER_SENSITIVE": "true",
        "MCP_KUBERNETES_LOG_LEVEL": "WARNING",
        "MCP_KUBERNETES_LOG_LINES": "10",
        "MCP_KUBERNETES_MAX_RESOURCES": "50",
    }
    
    for key, value in safe_env.items():
        monkeypatch.setenv(key, value)
    
    # Ensure any existing sensitive environment variables are not used
    sensitive_vars = [
        "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
        "GOOGLE_APPLICATION_CREDENTIALS", 
        "AZURE_CLIENT_SECRET",
        "KUBECTL_TOKEN", "KUBERNETES_TOKEN"
    ]
    
    for var in sensitive_vars:
        if var in os.environ:
            monkeypatch.delenv(var, raising=False)
    
    yield


@pytest.fixture
def mock_cluster_data():
    """Provide mock cluster data for tests that don't need real clusters."""
    return {
        "namespaces": [
            {"name": "default", "status": "Active", "labels": {}},
            {"name": "kube-system", "status": "Active", "labels": {}},
            {"name": "kube-public", "status": "Active", "labels": {}},
        ],
        "pods": [
            {
                "name": "test-pod-1",
                "namespace": "default",
                "status": "Running",
                "ready_containers": 1,
                "total_containers": 1,
                "node": "test-node",
                "pod_ip": "10.244.0.1"
            },
            {
                "name": "system-pod-1", 
                "namespace": "kube-system",
                "status": "Running",
                "ready_containers": 1,
                "total_containers": 1,
                "node": "test-node",
                "pod_ip": "10.244.0.2"
            }
        ],
        "services": [
            {
                "name": "kubernetes",
                "namespace": "default",
                "type": "ClusterIP",
                "cluster_ip": "10.96.0.1",
                "ports": [{"port": 443, "target_port": 6443, "protocol": "TCP"}],
                "selector": {}
            }
        ],
        "deployments": [
            {
                "name": "test-deployment",
                "namespace": "default", 
                "ready_replicas": 2,
                "replicas": 2,
                "updated_replicas": 2,
                "available_replicas": 2,
                "selector": {"app": "test"}
            }
        ]
    }