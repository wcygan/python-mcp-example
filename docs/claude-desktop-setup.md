# Claude Desktop Setup Guide

This guide shows how to integrate the MCP Kubernetes Server with Claude Desktop for AI-driven cluster management.

## Prerequisites

- Claude Desktop application installed
- Python 3.8+ with the MCP Kubernetes Server installed
- Access to a Kubernetes cluster
- Valid kubeconfig file

## Installation Steps

### 1. Install MCP Kubernetes Server

```bash
# Clone and install the server
git clone <repository-url>
cd python-mcp-example
python -m venv venv
source venv/bin/activate
pip install -e .
```

### 2. Test Server Installation

```bash
# Verify the server can start
python -m mcp_kubernetes --debug

# Test Kubernetes connectivity
kubectl cluster-info
```

### 3. Configure Claude Desktop

Edit Claude Desktop's configuration file:

**Location**: `~/.claude/config.json` (create if it doesn't exist)

```json
{
  "mcpServers": {
    "kubernetes": {
      "command": "python",
      "args": ["-m", "mcp_kubernetes"],
      "env": {
        "KUBECONFIG": "/Users/your-username/.kube/config",
        "MCP_KUBERNETES_READ_ONLY": "true",
        "MCP_KUBERNETES_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### 4. Advanced Configuration (Optional)

For production environments, create a dedicated configuration:

**Create**: `~/.claude/kubernetes-mcp-config.yaml`

```yaml
kubernetes:
  kubeconfig_path: ~/.kube/config
  context: production-cluster
  timeout: 30

security:
  read_only_mode: true
  rbac_check: true
  allowed_namespaces: ["production", "monitoring"]

logging:
  level: INFO
  max_log_lines: 100
```

**Update Claude Desktop config**:

```json
{
  "mcpServers": {
    "kubernetes": {
      "command": "python",
      "args": [
        "-m", "mcp_kubernetes", 
        "--config", "/Users/your-username/.claude/kubernetes-mcp-config.yaml"
      ],
      "env": {
        "MCP_KUBERNETES_READ_ONLY": "true"
      }
    }
  }
}
```

## Verification

### 1. Restart Claude Desktop

Close and reopen Claude Desktop to load the new configuration.

### 2. Test the Connection

In a new Claude conversation, try these queries:

```
"Can you show me the available Kubernetes resources?"
```

Expected response: List of available resources (pods, services, deployments, namespaces)

```
"List all pods in the default namespace"
```

Expected response: JSON formatted list of pods with status information

### 3. Test Tools

```
"Get logs from any running pod"
```

Expected response: Container logs from the specified pod

```
"Describe a specific pod in detail"
```

Expected response: Detailed pod information including containers and conditions

## Example Conversations

### Cluster Overview

**You**: "What's the overall health of my Kubernetes cluster?"

**Claude**: I'll check the status of your Kubernetes resources to give you an overview of cluster health.

[Claude will use the MCP tools to list pods, services, and deployments, then provide a summary of the cluster state]

### Troubleshooting

**You**: "I'm having issues with my web application. Can you help me debug?"

**Claude**: I'll help you troubleshoot your web application. Let me start by checking the status of your pods and then look at recent logs.

[Claude will use `get_pod_status` and `get_pod_logs` to identify issues]

### Resource Monitoring

**You**: "Show me which pods are using the most resources"

**Claude**: I'll examine your pods to show resource usage information.

[Claude will use `describe_pod` to get resource requests/limits and current usage]

## Troubleshooting

### Server Not Starting

**Issue**: Claude Desktop shows "MCP server failed to start"

**Solutions**:
1. Verify Python environment:
   ```bash
   which python
   python -m mcp_kubernetes --version
   ```

2. Check kubeconfig access:
   ```bash
   kubectl cluster-info
   ```

3. Test server manually:
   ```bash
   python -m mcp_kubernetes --debug
   ```

### Permission Errors

**Issue**: "Permission denied accessing Kubernetes resources"

**Solutions**:
1. Verify RBAC permissions:
   ```bash
   kubectl auth can-i list pods
   kubectl auth can-i get pods/log
   ```

2. Check kubeconfig context:
   ```bash
   kubectl config current-context
   kubectl config get-contexts
   ```

### Connection Timeouts

**Issue**: Requests timing out or failing

**Solutions**:
1. Increase timeout in configuration:
   ```yaml
   kubernetes:
     timeout: 60
   ```

2. Check cluster connectivity:
   ```bash
   kubectl get nodes
   ```

3. Use namespace filtering for large clusters:
   ```yaml
   resources:
     allowed_namespaces: ["production"]
   ```

## Security Considerations

### Read-Only Mode

The server is configured for read-only access by default:
- No cluster modifications possible
- Safe for production environments
- Respects existing RBAC permissions

### Sensitive Data Filtering

Automatic filtering of sensitive information:
- Kubernetes secrets are not exposed
- Service account tokens are filtered
- Environment variables containing credentials are masked

### Audit Logging

Enable audit logging for compliance:

```yaml
logging:
  enable_audit: true
  level: INFO
```

## Performance Tips

### Large Clusters

For clusters with many resources:

1. **Namespace Filtering**:
   ```yaml
   resources:
     allowed_namespaces: ["production", "staging"]
   ```

2. **Resource Limits**:
   ```yaml
   resources:
     max_items_per_request: 500
   ```

3. **Connection Pooling**:
   ```yaml
   kubernetes:
     timeout: 60
   mcp:
     max_connections: 5
   ```

### Memory Optimization

```yaml
logging:
  max_log_lines: 50

resources:
  max_items_per_request: 200
```

## Advanced Features

### Multiple Clusters

Configure access to multiple clusters:

```json
{
  "mcpServers": {
    "kubernetes-prod": {
      "command": "python",
      "args": ["-m", "mcp_kubernetes"],
      "env": {
        "KUBECONFIG": "/Users/your-username/.kube/prod-config",
        "MCP_KUBERNETES_READ_ONLY": "true"
      }
    },
    "kubernetes-staging": {
      "command": "python", 
      "args": ["-m", "mcp_kubernetes"],
      "env": {
        "KUBECONFIG": "/Users/your-username/.kube/staging-config",
        "MCP_KUBERNETES_READ_ONLY": "true"
      }
    }
  }
}
```

### Custom Aliases

Create conversation shortcuts:

**You**: "Show me prod status" → Claude checks production namespace
**You**: "Debug web app" → Claude checks specific application pods and logs

These patterns emerge naturally as Claude learns your common queries.

## Support

For issues with:
- **MCP Server**: Check server logs with `--debug` flag
- **Claude Desktop**: Restart the application and check console logs
- **Kubernetes Access**: Verify with `kubectl` commands
- **Configuration**: Validate YAML syntax and file paths