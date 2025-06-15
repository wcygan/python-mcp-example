# Integration Tests

This directory contains integration tests for the MCP Kubernetes server that test against real Kubernetes clusters while maintaining security and not exposing sensitive information.

## Safety Features

### 🔒 Security First
- **Read-Only Operations**: All tests only perform read operations
- **No Sensitive Data**: No passwords, secrets, or tokens are used or exposed
- **Safe Namespaces**: Tests only use standard system namespaces (`kube-system`, `default`, `kube-public`)
- **Data Anonymization**: Any potentially sensitive data is filtered or redacted
- **Resource Limits**: Strict limits on response sizes and log lines

### 🛡️ Data Protection
- **No Git Exposure**: No sensitive cluster information is logged or committed
- **Environment Isolation**: Tests use safe environment variable defaults
- **Minimal Scope**: Tests only access necessary resources
- **Timeout Protection**: All operations have reasonable timeouts

## Test Categories

### Core Integration Tests (`test_read_only_integration.py`)
- Server initialization and configuration
- Kubernetes cluster connectivity
- Resource listing (pods, services, deployments, namespaces)
- Tool operations (logs, describe, status)
- Security configuration enforcement
- Resource limit validation

### MCP Protocol Tests (`test_mcp_protocol_integration.py`)
- MCP protocol compliance
- Resource listing protocol
- Tool execution protocol
- Error handling
- Security boundaries
- Response safety

## Running Tests

### Prerequisites
- Kubernetes cluster access (local or remote)
- Valid kubeconfig
- Required permissions (read-only RBAC sufficient)

### Run All Integration Tests
```bash
# Run with pytest
pytest tests/integration/ -v

# Run with marker
pytest -m integration -v

# Skip if no cluster available
SKIP_INTEGRATION_TESTS=true pytest tests/integration/ -v
```

### Run Specific Test Files
```bash
# Read-only integration tests
pytest tests/integration/test_read_only_integration.py -v

# MCP protocol tests
pytest tests/integration/test_mcp_protocol_integration.py -v
```

### Command Line Options
```bash
# Skip integration tests
pytest --no-integration tests/

# Use specific kubeconfig
pytest --kubernetes-config=/path/to/config tests/integration/

# Run only fast tests
pytest -m "not slow" tests/integration/
```

## Environment Variables

### Safety Configuration
- `SKIP_INTEGRATION_TESTS=true` - Skip all integration tests
- `MCP_KUBERNETES_READ_ONLY=true` - Force read-only mode
- `MCP_KUBERNETES_RBAC_CHECK=true` - Enable RBAC checking
- `MCP_KUBERNETES_LOG_LEVEL=WARNING` - Reduce log verbosity
- `MCP_KUBERNETES_LOG_LINES=10` - Limit log output
- `MCP_KUBERNETES_MAX_RESOURCES=50` - Limit response size

### Test Configuration
```bash
# Safe test environment
export MCP_KUBERNETES_READ_ONLY=true
export MCP_KUBERNETES_RBAC_CHECK=true
export MCP_KUBERNETES_FILTER_SENSITIVE=true
export MCP_KUBERNETES_LOG_LEVEL=WARNING

# Run tests
pytest tests/integration/ -v
```

## Kubernetes Cluster Requirements

### Minimum Permissions
The tests require minimal read-only permissions:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: mcp-kubernetes-test
rules:
- apiGroups: [""]
  resources: ["pods", "services", "namespaces"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get"]
```

### Supported Clusters
- Local clusters (minikube, kind, k3s)
- Cloud clusters (EKS, GKE, AKS)
- Self-managed clusters
- Development clusters

### Not Recommended
- Production clusters with sensitive workloads
- Clusters with strict audit requirements
- Shared clusters without proper RBAC isolation

## Test Data Safety

### What Tests Access
- ✅ Standard system namespaces (`kube-system`, `default`, `kube-public`)
- ✅ Resource metadata (names, statuses, counts)
- ✅ Pod logs (limited lines, system pods only)
- ✅ Basic resource configurations

### What Tests Never Access
- ❌ User namespaces or applications
- ❌ Secrets or ConfigMaps
- ❌ Service account tokens
- ❌ Private keys or certificates
- ❌ Environment variables with credentials
- ❌ Persistent volume data

### Data Anonymization
```python
# Example of data filtering
def anonymize_resource_data(data):
    sensitive_fields = [
        "uid", "resourceVersion", "annotations", 
        "labels", "managedFields", "ownerReferences"
    ]
    # Fields are redacted or filtered
```

## Continuous Integration

### GitHub Actions
```yaml
name: Integration Tests
on: [push, pull_request]
jobs:
  integration:
    runs-on: ubuntu-latest
    services:
      kubernetes:
        image: kindest/node:v1.27.0
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -e .[test]
      - name: Run integration tests
        run: pytest tests/integration/ -v
        env:
          MCP_KUBERNETES_READ_ONLY: true
          MCP_KUBERNETES_LOG_LEVEL: WARNING
```

### Local Development
```bash
# Setup test environment
make test-env

# Run integration tests
make test-integration

# Run all tests
make test-all
```

## Troubleshooting

### Common Issues

**No Kubernetes cluster available**
```bash
# Check cluster connectivity
kubectl cluster-info

# Use local cluster
minikube start
# or
kind create cluster
```

**Permission denied**
```bash
# Check current permissions
kubectl auth can-i list pods
kubectl auth can-i get pods/log

# Create test service account if needed
kubectl apply -f docs/rbac-test.yaml
```

**Tests timing out**
```bash
# Increase timeout
export MCP_KUBERNETES_TIMEOUT=60

# Skip slow tests
pytest -m "not slow" tests/integration/
```

**Too much log output**
```bash
# Reduce verbosity
export MCP_KUBERNETES_LOG_LEVEL=ERROR
export MCP_KUBERNETES_LOG_LINES=5

# Run specific tests
pytest tests/integration/test_read_only_integration.py::TestReadOnlyIntegration::test_list_namespaces_safe -v
```

## Security Review

This integration test suite has been designed with security as the primary concern:

- ✅ **No write operations** - Only read-only Kubernetes operations
- ✅ **No sensitive data exposure** - All data is filtered and anonymized
- ✅ **Safe for CI/CD** - Can run in automated environments
- ✅ **Minimal permissions** - Requires only basic read access
- ✅ **Timeout protection** - All operations have reasonable limits
- ✅ **Git safe** - No sensitive information in test code or outputs
- ✅ **Audit friendly** - Clear logging of what operations are performed

The tests validate functionality while maintaining the highest security standards.