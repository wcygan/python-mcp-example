# MCP Kubernetes Server

AI-driven read-only Kubernetes cluster management through the Model Context Protocol.

## Quick Start

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -e .

# Configure Kubernetes access
export KUBECONFIG=~/.kube/config

# Run MCP server (read-only mode by default)
python -m mcp_kubernetes
```

## Features

- **Read-Only Operations**: Secure cluster inspection without modification risk
- **Resource Discovery**: List and inspect pods, services, deployments, namespaces
- **Log Analysis**: Container log retrieval with filtering
- **Status Monitoring**: Detailed pod status with label/field selectors
- **Configuration-Driven**: Comprehensive YAML and environment variable support
- **RBAC Integration**: Respects Kubernetes permissions and security boundaries

## Requirements

- Python 3.8+
- Kubernetes cluster access
- MCP-compatible AI client (Claude Desktop, etc.)

## Architecture

```
AI Client (Claude Desktop) <-> MCP Protocol <-> Python Server <-> Kubernetes API <-> Cluster
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `KUBECONFIG` | Path to kubeconfig file | `~/.kube/config` | No |
| `MCP_KUBERNETES_NAMESPACE` | Default namespace filter | `all` | No |
| `MCP_KUBERNETES_LOG_LINES` | Default log line limit | `100` | No |
| `MCP_KUBERNETES_READ_ONLY` | Force read-only mode | `true` | No |
| `MCP_KUBERNETES_RBAC_CHECK` | Enable RBAC checking | `true` | No |

### Configuration File

Create `config.yaml`:

```yaml
kubernetes:
  kubeconfig_path: ~/.kube/config
  timeout: 30

mcp:
  server_name: kubernetes-mcp
  max_connections: 10

resources:
  max_items_per_request: 1000
  allowed_namespaces: []  # Empty = all namespaces

security:
  read_only_mode: true
  rbac_check: true
  allowed_operations: ["list", "get", "watch", "logs"]

logging:
  level: INFO
  max_log_lines: 100
```

## CLI Usage

```bash
# Basic usage (read-only by default)
python -m mcp_kubernetes

# With custom configuration
python -m mcp_kubernetes --config config.yaml

# Override kubeconfig
python -m mcp_kubernetes --kubeconfig /path/to/config

# Enable debug logging
python -m mcp_kubernetes --debug
```

## AI Integration Examples

### Resource Queries
```
"Show me all pods in the production namespace"
"List services with external LoadBalancer IPs"
"What deployments are not at desired replica count?"
```

### Status Monitoring
```
"Which pods are not ready?"
"Show me failed pods from the last hour"
"Get the status of all nginx pods"
```

### Log Analysis
```
"Get logs from the api-server pod"
"Show me the last 50 lines from the database container"
"Retrieve logs from pods with label app=frontend"
```

## Available Tools

- **`get_pod_logs`**: Retrieve container logs with line limits and container selection
- **`describe_pod`**: Detailed pod information including containers, resources, and conditions
- **`get_pod_status`**: Filter pods by namespace, labels, or field selectors

## Available Resources

- **`k8s://pods`**: Kubernetes pods with status and container information
- **`k8s://services`**: Services with endpoints and port configurations
- **`k8s://deployments`**: Deployments with replica status and selector information
- **`k8s://namespaces`**: Available namespaces with labels and status

## Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
make test

# Format code
make format

# Type checking
make type-check

# Run all checks
make check
```

## Security

- **Read-Only by Default**: No cluster modifications possible
- **RBAC Aware**: Respects Kubernetes role-based access controls
- **Audit Logging**: Optional request/response logging for compliance
- **Namespace Filtering**: Restrict access to specific namespaces
- **Sensitive Data Filtering**: Automatically removes secrets and tokens from responses