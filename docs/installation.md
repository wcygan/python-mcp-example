# Installation Guide

## Prerequisites

- Python 3.8 or higher
- Access to a Kubernetes cluster
- Valid kubeconfig file

## Installation Methods

### From Source

```bash
git clone <repository-url>
cd python-mcp-example
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Using pip (when published)

```bash
pip install mcp-kubernetes
```

## Kubernetes Configuration

### Local Development

For local testing with minikube or kind:

```bash
# Start minikube
minikube start

# Verify connection
kubectl cluster-info
```

### Production Cluster

Ensure your kubeconfig is properly configured:

```bash
# Set kubeconfig path
export KUBECONFIG=/path/to/your/kubeconfig

# Test connection
kubectl get nodes
```

## Service Account Setup (Recommended)

Create a dedicated service account with appropriate permissions:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: mcp-kubernetes
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: mcp-kubernetes
rules:
- apiGroups: [""]
  resources: ["pods", "services", "namespaces"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: mcp-kubernetes
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: mcp-kubernetes
subjects:
- kind: ServiceAccount
  name: mcp-kubernetes
  namespace: default
```

Apply the configuration:

```bash
kubectl apply -f service-account.yaml
```

## Verification

Test the installation:

```bash
python -c "from mcp_kubernetes import server; print('Installation successful')"
```