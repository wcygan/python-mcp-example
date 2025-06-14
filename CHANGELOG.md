# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-13

### Added

**Core MCP Server Implementation**
- Complete MCP protocol server for Kubernetes cluster management
- Support for listing pods, services, deployments, and namespaces
- Read-only tool operations for secure cluster inspection

**Read-Only Tools**
- `get_pod_logs`: Container log retrieval with line limits and container selection
- `describe_pod`: Detailed pod information including containers, resources, and conditions  
- `get_pod_status`: Filter pods by namespace, labels, or field selectors

**Comprehensive Configuration System**
- YAML configuration file support with structured validation
- Environment variable configuration with `MCP_KUBERNETES_*` prefix
- CLI arguments with override capabilities
- Default read-only mode for enhanced security

**Security Features**
- Read-only mode enforced by default (no cluster modifications)
- RBAC-aware resource access respecting Kubernetes permissions
- Sensitive data filtering in API responses
- Audit logging capabilities for compliance
- Namespace filtering and access controls

**Development Infrastructure**
- Complete Python package structure with pyproject.toml
- Comprehensive unit test suite with Kubernetes client mocking
- Code formatting, linting, and type checking setup
- Make-based development workflow
- Pre-commit hooks and development tools

### Configuration

**Environment Variables**
- `KUBECONFIG`: Path to kubeconfig file
- `MCP_KUBERNETES_NAMESPACE`: Default namespace filter
- `MCP_KUBERNETES_LOG_LINES`: Default log line limit
- `MCP_KUBERNETES_READ_ONLY`: Force read-only mode (default: true)
- `MCP_KUBERNETES_RBAC_CHECK`: Enable RBAC checking (default: true)

**CLI Options**
- `--config`: Custom configuration file path
- `--kubeconfig`: Override kubeconfig path
- `--read-only`: Enable read-only mode (default: true)
- `--debug`: Enable debug logging

### Resources

**Available Resource URIs**
- `k8s://pods[?namespace=<namespace>]`: Kubernetes pods with status information
- `k8s://services[?namespace=<namespace>]`: Services with endpoints and ports
- `k8s://deployments[?namespace=<namespace>]`: Deployments with replica status
- `k8s://namespaces`: Available namespaces with labels and status

### Documentation
- Comprehensive README with configuration examples
- API reference documentation with tool schemas
- Installation guide with multiple deployment options
- Usage examples for AI integration
- Configuration reference with all available options
- Security setup and RBAC configuration guide

### Removed
- Deployment scaling operations (moved to read-only focus)
- Write operations that could modify cluster state
- Unsafe default configurations

## [0.0.1] - 2025-01-13

### Added
- Initial project structure and documentation
- Investigation of MCP and Kubernetes Python client integration
- Proof-of-concept architecture design
- Development roadmap and implementation planning