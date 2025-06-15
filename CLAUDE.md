# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python MCP (Model Context Protocol) server that provides read-only Kubernetes cluster access to AI assistants. The server acts as a bridge between AI clients (like Claude Desktop) and Kubernetes clusters, enabling safe cluster inspection without modification risks.

## Key Development Commands

```bash
# Setup and installation
python -m venv venv && source venv/bin/activate
pip install -e .                    # Install in development mode
make install-dev                    # Install with dev dependencies and pre-commit hooks

# Testing
pytest tests/test_server.py -v      # Run single test file
make test                           # Unit tests only
make test-integration              # Integration tests (requires K8s cluster)
make test-integration-safe         # Integration tests with safety flags
make test-all                      # All tests
make test-cov                      # Tests with coverage report

# Code quality
make format                        # Format code with black and isort
make lint                          # Check code quality
make type-check                    # Run mypy type checking
make check                         # Run all checks (lint + type-check + test)

# Development server
make dev                           # Start server with debug logging
python -m mcp_kubernetes --debug   # Alternative debug server start
```

## Architecture Overview

The codebase follows a clean layered architecture:

- **`mcp_kubernetes/server.py`**: Core MCP server implementation with Kubernetes API integration
- **`mcp_kubernetes/config.py`**: Hierarchical configuration system (CLI > Config object > File > Env > Defaults)
- **`mcp_kubernetes/cli.py`**: Command-line interface and server orchestration
- **`tests/integration/`**: Comprehensive security-focused integration tests

### Key Architectural Patterns

**Configuration Hierarchy**: The system supports multiple configuration sources with clear precedence:
1. CLI arguments (highest priority)
2. Server config object 
3. YAML configuration file
4. Environment variables
5. Default values (lowest priority)

**Connection Management**: Lazy initialization with fallback strategies:
- In-cluster service account authentication
- Kubeconfig file with optional context selection
- Automatic connection testing and timeout handling

**Security-First Design**: Read-only operations enforced at multiple levels:
- Configuration-level read-only mode
- Operation whitelisting (only list, get, watch, logs)
- RBAC awareness and sensitive data filtering
- Safe namespace restrictions for testing

## MCP Protocol Implementation

The server implements three main components:

**Resources** (URI-based):
- `k8s://pods[?namespace=<ns>]`
- `k8s://services[?namespace=<ns>]` 
- `k8s://deployments[?namespace=<ns>]`
- `k8s://namespaces`

**Tools** (function-based):
- `get_pod_logs`: Container log retrieval with filtering
- `describe_pod`: Detailed pod information
- `get_pod_status`: Pod status with label/field selectors

## Testing Strategy

**Unit Tests**: Mock Kubernetes API clients for isolated testing
**Integration Tests**: Two comprehensive test suites:
- `test_read_only_integration.py`: Security boundary validation
- `test_mcp_protocol_integration.py`: MCP protocol compliance

Integration tests include data anonymization and safety measures to prevent sensitive information exposure.

## Configuration Examples

**Environment Variables**:
- `MCP_KUBERNETES_READ_ONLY=true` - Force read-only mode
- `MCP_KUBERNETES_LOG_LEVEL=DEBUG` - Enable debug logging
- `KUBECONFIG=~/.kube/config` - Kubernetes configuration path

**YAML Configuration** (`config.yaml`):
```yaml
kubernetes:
  kubeconfig_path: ~/.kube/config
  timeout: 30
security:
  read_only_mode: true
  rbac_check: true
resources:
  max_items_per_request: 1000
```

## Important Implementation Details

**Error Handling**: All Kubernetes API calls include proper exception handling with logging and graceful error responses in MCP protocol format.

**Performance Limits**: Configurable limits prevent resource exhaustion:
- `max_items_per_request`: Limits resource listing size
- `max_log_lines`: Limits log retrieval size
- Connection timeouts: Prevents hanging operations

**Data Transformation**: Clean transformation from Kubernetes API objects to simplified JSON structures, extracting only essential information while handling nullable fields gracefully.

## Development Notes

- All code uses async/await patterns for non-blocking operations
- Type hints are used throughout (mypy configured for strict checking)
- The project uses dataclasses for configuration management
- Pre-commit hooks enforce code quality standards
- Integration tests can be safely run in CI/CD environments