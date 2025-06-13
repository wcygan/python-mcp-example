# MCP Kubernetes Client

Python MCP server providing AI-driven Kubernetes cluster management through the Model Context Protocol.

## Quick Start

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Configure Kubernetes access
export KUBECONFIG=~/.kube/config

# Run MCP server
python -m mcp_kubernetes
```

## Features

- List and inspect Kubernetes resources (pods, services, deployments)
- View container logs through MCP protocol
- Basic cluster operations via AI integration
- Secure RBAC-aware resource access

## Requirements

- Python 3.8+
- Kubernetes cluster access
- MCP-compatible AI client

## Architecture

```
AI Client (Claude, etc.) êí MCP Protocol êí Kubernetes Python Client êí K8s Cluster
```

## Usage

Connect through any MCP-compatible client:

```python
# Example resource query
resources = mcp_client.list_resources()
pods = mcp_client.read_resource("k8s://pods")
```

## Development

```bash
# Install dependencies
pip install -e .

# Run tests
python -m pytest

# Type check
mypy mcp_kubernetes/
```