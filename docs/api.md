# API Reference

## MCP Protocol Implementation

This server implements the Model Context Protocol (MCP) specification for Kubernetes integration.

## Resources

### Kubernetes Pods

**URI Pattern**: `k8s://pods[?namespace=<namespace>]`

**Description**: Access to Kubernetes pod resources

**Example Usage**:
```json
{
  "method": "resources/read",
  "params": {
    "uri": "k8s://pods?namespace=default"
  }
}
```

**Response Format**:
```json
{
  "contents": [
    {
      "uri": "k8s://pods",
      "mimeType": "application/json",
      "text": "[{\"name\": \"nginx-pod\", \"namespace\": \"default\", \"status\": \"Running\"}]"
    }
  ]
}
```

### Kubernetes Services

**URI Pattern**: `k8s://services[?namespace=<namespace>]`

**Description**: Access to Kubernetes service resources

### Kubernetes Deployments

**URI Pattern**: `k8s://deployments[?namespace=<namespace>]`

**Description**: Access to Kubernetes deployment resources

## Tools

### Get Pod Logs

**Name**: `get_pod_logs`

**Description**: Retrieve logs from a specific pod

**Parameters**:
- `pod_name` (required): Name of the pod
- `namespace` (optional): Kubernetes namespace, defaults to 'default'
- `lines` (optional): Number of log lines to retrieve, defaults to 100
- `container` (optional): Specific container name in multi-container pods

**Example**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "get_pod_logs",
    "arguments": {
      "pod_name": "nginx-deployment-abc123",
      "namespace": "default",
      "lines": 50
    }
  }
}
```

### Scale Deployment

**Name**: `scale_deployment`

**Description**: Scale a deployment to specified replica count

**Parameters**:
- `deployment_name` (required): Name of the deployment
- `namespace` (optional): Kubernetes namespace, defaults to 'default'
- `replicas` (required): Target number of replicas

### Restart Deployment

**Name**: `restart_deployment`

**Description**: Restart a deployment by updating its annotation

**Parameters**:
- `deployment_name` (required): Name of the deployment
- `namespace` (optional): Kubernetes namespace, defaults to 'default'

## Error Handling

### Common Error Responses

**Authentication Error**:
```json
{
  "error": {
    "code": "AUTHENTICATION_FAILED",
    "message": "Unable to authenticate with Kubernetes cluster"
  }
}
```

**Permission Error**:
```json
{
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "Insufficient permissions to access resource"
  }
}
```

**Resource Not Found**:
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Pod 'nginx-pod' not found in namespace 'default'"
  }
}
```

## Rate Limiting

- Maximum 100 requests per minute per client
- Bulk operations limited to 50 resources per request
- Log streaming limited to 1000 lines per request

## Security Considerations

- All operations respect Kubernetes RBAC permissions
- Service account tokens are never exposed in responses
- Sensitive data is filtered from resource descriptions
- Audit logging is enabled for all operations

## Versioning

This API follows semantic versioning:
- Current version: 1.0.0
- Supported MCP protocol version: 1.0.0
- Minimum Kubernetes version: 1.20.0

## Extensions

### Custom Resource Definitions (CRDs)

Support for custom resources can be enabled by configuration:

```yaml
extensions:
  custom_resources:
    - group: "example.com"
      version: "v1"
      plural: "customresources"
```

### Namespace Restrictions

Limit access to specific namespaces:

```yaml
security:
  allowed_namespaces:
    - "default"
    - "monitoring"
    - "production"
```