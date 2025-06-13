# Configuration

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `KUBECONFIG` | Path to kubeconfig file | `~/.kube/config` | No |
| `MCP_KUBERNETES_NAMESPACE` | Default namespace filter | `all` | No |
| `MCP_KUBERNETES_LOG_LINES` | Default log line limit | `100` | No |
| `MCP_KUBERNETES_MAX_RESOURCES` | Maximum resources per request | `1000` | No |
| `MCP_KUBERNETES_TIMEOUT` | Request timeout in seconds | `30` | No |
| `MCP_KUBERNETES_DEBUG` | Enable debug logging | `false` | No |

## Configuration File

Create a `config.yaml` file in your project root:

```yaml
# Kubernetes connection settings
kubernetes:
  kubeconfig_path: ~/.kube/config
  context: ""  # Use specific context, empty for current
  timeout: 30
  
# MCP server settings
mcp:
  server_name: kubernetes-mcp
  version: 1.0.0
  max_connections: 10

# Resource access configuration
resources:
  default_namespace: default
  max_items_per_request: 1000
  allowed_namespaces: []  # Empty = all namespaces
  
# Logging configuration
logging:
  level: INFO
  max_log_lines: 100
  enable_audit: true

# Security settings
security:
  rbac_check: true
  filter_sensitive_data: true
  allowed_operations:
    - list
    - get
    - watch
    - logs

# Feature flags
features:
  enable_custom_resources: false
  enable_metrics: false
  enable_events: true
```

## Authentication Methods

### Kubeconfig File

Default method using your local kubeconfig:

```yaml
kubernetes:
  kubeconfig_path: ~/.kube/config
  context: my-cluster
```

### Service Account Token

For in-cluster deployment:

```yaml
kubernetes:
  use_service_account: true
  service_account_path: /var/run/secrets/kubernetes.io/serviceaccount
```

### Token Authentication

Using bearer token:

```yaml
kubernetes:
  api_server: https://kubernetes.example.com
  token: your-bearer-token
  ca_cert_path: /path/to/ca.crt
```

## RBAC Configuration

### Minimal Permissions

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: mcp-kubernetes-readonly
rules:
- apiGroups: [""]
  resources: ["pods", "services", "namespaces"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
```

### Extended Permissions

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: mcp-kubernetes-operator
rules:
- apiGroups: [""]
  resources: ["pods", "services", "namespaces"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get"]
```

## Performance Tuning

### Connection Pool Settings

```yaml
kubernetes:
  connection_pool:
    max_connections: 10
    idle_timeout: 300
    read_timeout: 30
    write_timeout: 30
```

### Caching Configuration

```yaml
caching:
  enable_resource_cache: true
  cache_ttl: 60  # seconds
  max_cache_size: 1000
```

### Request Limits

```yaml
limits:
  max_concurrent_requests: 50
  rate_limit_per_minute: 1000
  max_log_lines_per_request: 1000
```

## Monitoring and Observability

### Metrics Configuration

```yaml
metrics:
  enable: true
  port: 9090
  path: /metrics
  labels:
    service: mcp-kubernetes
    version: 1.0.0
```

### Health Check

```yaml
health:
  enable: true
  port: 8080
  path: /health
  kubernetes_check: true
```

### Audit Logging

```yaml
audit:
  enable: true
  log_file: /var/log/mcp-kubernetes-audit.log
  log_level: INFO
  include_request_body: false
  include_response_body: false
```

## Example Configurations

### Development Setup

```yaml
kubernetes:
  kubeconfig_path: ~/.kube/config

mcp:
  server_name: kubernetes-mcp-dev

logging:
  level: DEBUG

security:
  rbac_check: false
```

### Production Setup

```yaml
kubernetes:
  use_service_account: true
  timeout: 60

mcp:
  server_name: kubernetes-mcp-prod
  max_connections: 50

resources:
  allowed_namespaces:
    - production
    - monitoring

security:
  rbac_check: true
  filter_sensitive_data: true

metrics:
  enable: true
  port: 9090

audit:
  enable: true
  log_file: /var/log/audit.log
```