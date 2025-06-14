# Usage Guide

## Starting the MCP Server

```bash
# Run the MCP server (read-only by default)
python -m mcp_kubernetes

# With custom configuration file
python -m mcp_kubernetes --config config.yaml

# Override kubeconfig path
python -m mcp_kubernetes --kubeconfig ~/.kube/prod-config

# Enable debug logging
python -m mcp_kubernetes --debug
```

## Connecting AI Clients

### Claude Desktop

Add to your Claude Desktop configuration (`~/.claude/config.json`):

```json
{
  "mcpServers": {
    "kubernetes": {
      "command": "python",
      "args": ["-m", "mcp_kubernetes"],
      "env": {
        "KUBECONFIG": "/path/to/your/kubeconfig",
        "MCP_KUBERNETES_READ_ONLY": "true"
      }
    }
  }
}
```

### Other MCP Clients

The server follows standard MCP protocol and works with any compatible client that supports:
- Resource listing and reading
- Tool execution
- JSON-based responses

## AI Conversation Examples

### Resource Discovery

**Query**: *"Show me all pods in the production namespace"*
```
Resources: k8s://pods?namespace=production
Response: [List of pods with status, ready containers, and age]
```

**Query**: *"List services with external IPs"*
```
Tool: get_pod_status with field_selector for LoadBalancer services
Response: [Services with external IP addresses and ports]
```

### Status Monitoring

**Query**: *"Which pods are not ready?"*
```
Tool: get_pod_status with field_selector="status.phase!=Running"
Response: [Failed/pending pods with reasons and conditions]
```

**Query**: *"Show me pods that have restarted recently"*
```
Tool: get_pod_status 
Response: [Pods with restart counts and last restart times]
```

### Log Analysis

**Query**: *"Get logs from the api-server pod"*
```
Tool: get_pod_logs
Arguments: {"pod_name": "api-server", "namespace": "kube-system", "lines": 100}
Response: [Latest 100 log lines from the pod]
```

**Query**: *"Show me error logs from the database container"*
```
Tool: get_pod_logs  
Arguments: {"pod_name": "mysql-pod", "container": "mysql", "lines": 50}
Response: [Container-specific logs]
```

### Detailed Inspection

**Query**: *"Describe the nginx deployment configuration"*
```
Tool: describe_pod for pods in the deployment
Response: [Pod specs, resource limits, volume mounts, env variables]
```

## Available Resources

### Pods (`k8s://pods`)

Lists Kubernetes pods with comprehensive status information:

```json
{
  "name": "nginx-pod",
  "namespace": "default", 
  "status": "Running",
  "ready_containers": 1,
  "total_containers": 1,
  "node": "worker-node-1",
  "pod_ip": "10.244.1.5"
}
```

**Namespace Filtering**: `k8s://pods?namespace=production`

### Services (`k8s://services`)

Lists services with endpoint and port information:

```json
{
  "name": "web-service",
  "namespace": "default",
  "type": "LoadBalancer", 
  "cluster_ip": "10.96.0.1",
  "ports": [{"port": 80, "target_port": 8080, "protocol": "TCP"}],
  "selector": {"app": "web"}
}
```

### Deployments (`k8s://deployments`)

Lists deployments with replica status:

```json
{
  "name": "web-deployment",
  "namespace": "default",
  "ready_replicas": 3,
  "replicas": 3,
  "updated_replicas": 3,
  "selector": {"app": "web"}
}
```

### Namespaces (`k8s://namespaces`)

Lists available namespaces:

```json
{
  "name": "production",
  "status": "Active",
  "labels": {"env": "prod"}
}
```

## Available Tools

### `get_pod_logs`

Retrieve container logs with filtering options:

**Parameters**:
- `pod_name` (required): Name of the pod
- `namespace` (optional): Kubernetes namespace (default: "default")
- `lines` (optional): Number of log lines (default: 100)
- `container` (optional): Specific container name

**Example**: `get_pod_logs(pod_name="nginx-pod", namespace="web", lines=50)`

### `describe_pod`

Get detailed pod information including containers, resources, and conditions:

**Parameters**:
- `pod_name` (required): Name of the pod  
- `namespace` (optional): Kubernetes namespace (default: "default")

**Response includes**:
- Container specifications and images
- Resource requests and limits
- Pod conditions and events
- Volume mounts and environment variables

### `get_pod_status`

Filter and retrieve pod status information:

**Parameters**:
- `namespace` (optional): Filter by namespace
- `label_selector` (optional): Filter by labels (e.g., "app=nginx,version=v1.0")
- `field_selector` (optional): Filter by fields (e.g., "status.phase=Running")

**Example**: `get_pod_status(label_selector="app=web", namespace="production")`

## Configuration Options

### Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `KUBECONFIG` | Path to kubeconfig file | `~/.kube/config` | `/home/user/.kube/prod-config` |
| `MCP_KUBERNETES_NAMESPACE` | Default namespace filter | `all` | `production` |
| `MCP_KUBERNETES_LOG_LINES` | Default log line limit | `100` | `500` |
| `MCP_KUBERNETES_READ_ONLY` | Force read-only mode | `true` | `true` |
| `MCP_KUBERNETES_RBAC_CHECK` | Enable RBAC checking | `true` | `false` |
| `MCP_KUBERNETES_TIMEOUT` | Request timeout (seconds) | `30` | `60` |

### Configuration File

Create `config.yaml` for advanced configuration:

```yaml
kubernetes:
  kubeconfig_path: ~/.kube/config
  context: production-cluster
  timeout: 30
  use_service_account: false

mcp:
  server_name: kubernetes-mcp
  max_connections: 10

resources:
  max_items_per_request: 1000
  allowed_namespaces: ["production", "staging"]

security:
  read_only_mode: true
  rbac_check: true
  filter_sensitive_data: true
  allowed_operations: ["list", "get", "watch", "logs"]

logging:
  level: INFO
  max_log_lines: 100
  enable_audit: true
```

## Advanced Filtering

### Label Selectors

Filter resources by labels:

```bash
# Pods with specific app label
get_pod_status(label_selector="app=nginx")

# Multiple label criteria
get_pod_status(label_selector="app=web,version=v2.0,env=prod")

# Label existence checks
get_pod_status(label_selector="app,version!=v1.0")
```

### Field Selectors

Filter by resource fields:

```bash
# Running pods only
get_pod_status(field_selector="status.phase=Running")

# Pods on specific node
get_pod_status(field_selector="spec.nodeName=worker-1")

# Failed pods
get_pod_status(field_selector="status.phase=Failed")
```

## Troubleshooting

### Connection Issues

```bash
# Test Kubernetes connectivity
kubectl cluster-info

# Verify kubeconfig access
kubectl get nodes

# Check MCP server with debug logging
python -m mcp_kubernetes --debug
```

### Permission Errors

Common RBAC issues and solutions:

```bash
# Check current permissions
kubectl auth can-i list pods
kubectl auth can-i get pods/log

# View effective permissions
kubectl auth can-i --list
```

Ensure your service account has these minimum permissions:
- `get`, `list`, `watch` on pods, services, deployments
- `get` on pods/log for log retrieval

### Performance Optimization

**For Large Clusters**:
- Use namespace filtering: `MCP_KUBERNETES_NAMESPACE=production`
- Limit allowed namespaces in config: `allowed_namespaces: ["prod", "staging"]`
- Reduce log line limits: `MCP_KUBERNETES_LOG_LINES=50`
- Set request timeouts: `MCP_KUBERNETES_TIMEOUT=60`

**Memory Usage**:
- Limit max items per request: `max_items_per_request: 500`
- Enable resource caching in future versions
- Use field selectors to filter at API level

### Common Error Messages

**"Cannot connect to Kubernetes cluster"**
- Check `KUBECONFIG` environment variable
- Verify kubeconfig file exists and has valid credentials
- Test with `kubectl cluster-info`

**"Permission denied accessing pods"**
- Check RBAC permissions with `kubectl auth can-i list pods`
- Ensure service account has required cluster roles

**"MCP protocol error"**
- Verify AI client MCP compatibility
- Check server logs with `--debug` flag
- Ensure proper JSON formatting in responses