# Usage Guide

## Starting the MCP Server

```bash
# Run the MCP server
python -m mcp_kubernetes

# Or with custom configuration
python -m mcp_kubernetes --config config.yaml
```

## Connecting AI Clients

### Claude Desktop

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "kubernetes": {
      "command": "python",
      "args": ["-m", "mcp_kubernetes"],
      "env": {
        "KUBECONFIG": "/path/to/your/kubeconfig"
      }
    }
  }
}
```

### Other MCP Clients

The server follows standard MCP protocol and works with any compatible client.

## Available Resources

### Pods

List all pods across namespaces:
```
Query: "Show me all pods in the cluster"
```

Get specific pod details:
```
Query: "Get details for pod nginx-deployment-abc123 in default namespace"
```

### Services

List services:
```
Query: "List all services in the production namespace"
```

### Deployments

Check deployment status:
```
Query: "Show the status of my web-app deployment"
```

## Common Operations

### Viewing Logs

```
Query: "Show me the logs for the nginx pod"
AI Response: [Latest 100 lines of pod logs]
```

### Resource Status

```
Query: "What's the health status of my application pods?"
AI Response: [Pod status summary with ready/running states]
```

### Namespace Information

```
Query: "What resources are running in the monitoring namespace?"
AI Response: [List of pods, services, deployments in namespace]
```

## Advanced Queries

### Filtering Resources

```
Query: "Show me all failed pods from the last hour"
Query: "List services with external LoadBalancer IPs"
Query: "Find deployments that are not at desired replica count"
```

### Cross-Resource Analysis

```
Query: "Which pods are not covered by any service?"
Query: "Show me the resource usage of pods in the database namespace"
```

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `KUBECONFIG` | Path to kubeconfig file | `~/.kube/config` |
| `MCP_KUBERNETES_NAMESPACE` | Default namespace filter | `all` |
| `MCP_KUBERNETES_LOG_LINES` | Default log line limit | `100` |

### Configuration File

Create `config.yaml`:

```yaml
kubernetes:
  kubeconfig_path: ~/.kube/config
  default_namespace: default
  max_log_lines: 200

mcp:
  server_name: kubernetes-mcp
  version: 1.0.0
```

## Troubleshooting

### Connection Issues

```bash
# Test Kubernetes connectivity
kubectl cluster-info

# Check MCP server logs
python -m mcp_kubernetes --debug
```

### Permission Errors

Ensure your service account has the required RBAC permissions (see installation guide).

### Performance Tips

- Use namespace filtering for large clusters
- Limit log line requests for better performance
- Consider using resource version for efficient watching