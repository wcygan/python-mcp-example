"""Configuration management for the Kubernetes MCP server."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import yaml


@dataclass
class KubernetesConfig:
    """Kubernetes connection configuration."""
    kubeconfig_path: Optional[str] = None
    context: Optional[str] = None
    timeout: int = 30
    use_service_account: bool = False
    service_account_path: str = "/var/run/secrets/kubernetes.io/serviceaccount"


@dataclass 
class MCPConfig:
    """MCP server configuration."""
    server_name: str = "kubernetes-mcp"
    version: str = "0.1.0"
    max_connections: int = 10


@dataclass
class ResourceConfig:
    """Resource access configuration."""
    default_namespace: Optional[str] = None
    max_items_per_request: int = 1000
    allowed_namespaces: List[str] = None
    
    def __post_init__(self):
        if self.allowed_namespaces is None:
            self.allowed_namespaces = []


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    max_log_lines: int = 100
    enable_audit: bool = True


@dataclass
class SecurityConfig:
    """Security settings."""
    rbac_check: bool = True
    filter_sensitive_data: bool = True
    allowed_operations: List[str] = None
    read_only_mode: bool = True
    
    def __post_init__(self):
        if self.allowed_operations is None:
            # Default to read-only operations
            self.allowed_operations = ["list", "get", "watch", "logs"]


@dataclass
class FeatureConfig:
    """Feature flags."""
    enable_custom_resources: bool = False
    enable_metrics: bool = False
    enable_events: bool = True


@dataclass
class ServerConfig:
    """Complete server configuration."""
    kubernetes: KubernetesConfig
    mcp: MCPConfig
    resources: ResourceConfig
    logging: LoggingConfig
    security: SecurityConfig
    features: FeatureConfig
    
    @classmethod
    def from_file(cls, config_path: str) -> "ServerConfig":
        """Load configuration from YAML file."""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        return cls.from_dict(config_data)
    
    @classmethod
    def from_dict(cls, config_data: dict) -> "ServerConfig":
        """Create configuration from dictionary."""
        return cls(
            kubernetes=KubernetesConfig(**config_data.get("kubernetes", {})),
            mcp=MCPConfig(**config_data.get("mcp", {})),
            resources=ResourceConfig(**config_data.get("resources", {})),
            logging=LoggingConfig(**config_data.get("logging", {})),
            security=SecurityConfig(**config_data.get("security", {})),
            features=FeatureConfig(**config_data.get("features", {}))
        )
    
    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Load configuration from environment variables."""
        kubernetes_config = KubernetesConfig(
            kubeconfig_path=os.getenv("KUBECONFIG"),
            timeout=int(os.getenv("MCP_KUBERNETES_TIMEOUT", "30")),
            use_service_account=os.getenv("MCP_KUBERNETES_USE_SERVICE_ACCOUNT", "false").lower() == "true"
        )
        
        mcp_config = MCPConfig(
            server_name=os.getenv("MCP_KUBERNETES_SERVER_NAME", "kubernetes-mcp"),
            max_connections=int(os.getenv("MCP_KUBERNETES_MAX_CONNECTIONS", "10"))
        )
        
        resources_config = ResourceConfig(
            default_namespace=os.getenv("MCP_KUBERNETES_NAMESPACE"),
            max_items_per_request=int(os.getenv("MCP_KUBERNETES_MAX_RESOURCES", "1000")),
            allowed_namespaces=_parse_list_env("MCP_KUBERNETES_ALLOWED_NAMESPACES")
        )
        
        logging_config = LoggingConfig(
            level=os.getenv("MCP_KUBERNETES_LOG_LEVEL", "INFO"),
            max_log_lines=int(os.getenv("MCP_KUBERNETES_LOG_LINES", "100")),
            enable_audit=os.getenv("MCP_KUBERNETES_ENABLE_AUDIT", "true").lower() == "true"
        )
        
        security_config = SecurityConfig(
            rbac_check=os.getenv("MCP_KUBERNETES_RBAC_CHECK", "true").lower() == "true",
            filter_sensitive_data=os.getenv("MCP_KUBERNETES_FILTER_SENSITIVE", "true").lower() == "true",
            read_only_mode=os.getenv("MCP_KUBERNETES_READ_ONLY", "true").lower() == "true",
            allowed_operations=_parse_list_env("MCP_KUBERNETES_ALLOWED_OPERATIONS") or ["list", "get", "watch", "logs"]
        )
        
        features_config = FeatureConfig(
            enable_custom_resources=os.getenv("MCP_KUBERNETES_ENABLE_CRDS", "false").lower() == "true",
            enable_metrics=os.getenv("MCP_KUBERNETES_ENABLE_METRICS", "false").lower() == "true",
            enable_events=os.getenv("MCP_KUBERNETES_ENABLE_EVENTS", "true").lower() == "true"
        )
        
        return cls(
            kubernetes=kubernetes_config,
            mcp=mcp_config,
            resources=resources_config,
            logging=logging_config,
            security=security_config,
            features=features_config
        )
    
    @classmethod
    def default(cls) -> "ServerConfig":
        """Create default configuration."""
        return cls(
            kubernetes=KubernetesConfig(),
            mcp=MCPConfig(),
            resources=ResourceConfig(),
            logging=LoggingConfig(),
            security=SecurityConfig(),
            features=FeatureConfig()
        )
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "kubernetes": {
                "kubeconfig_path": self.kubernetes.kubeconfig_path,
                "context": self.kubernetes.context,
                "timeout": self.kubernetes.timeout,
                "use_service_account": self.kubernetes.use_service_account,
                "service_account_path": self.kubernetes.service_account_path
            },
            "mcp": {
                "server_name": self.mcp.server_name,
                "version": self.mcp.version,
                "max_connections": self.mcp.max_connections
            },
            "resources": {
                "default_namespace": self.resources.default_namespace,
                "max_items_per_request": self.resources.max_items_per_request,
                "allowed_namespaces": self.resources.allowed_namespaces
            },
            "logging": {
                "level": self.logging.level,
                "max_log_lines": self.logging.max_log_lines,
                "enable_audit": self.logging.enable_audit
            },
            "security": {
                "rbac_check": self.security.rbac_check,
                "filter_sensitive_data": self.security.filter_sensitive_data,
                "allowed_operations": self.security.allowed_operations,
                "read_only_mode": self.security.read_only_mode
            },
            "features": {
                "enable_custom_resources": self.features.enable_custom_resources,
                "enable_metrics": self.features.enable_metrics,
                "enable_events": self.features.enable_events
            }
        }
    
    def save_to_file(self, config_path: str) -> None:
        """Save configuration to YAML file."""
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)


def _parse_list_env(env_var: str) -> Optional[List[str]]:
    """Parse comma-separated environment variable into list."""
    value = os.getenv(env_var)
    if value:
        return [item.strip() for item in value.split(",") if item.strip()]
    return None


def load_config(config_path: Optional[str] = None) -> ServerConfig:
    """Load configuration from file, environment, or defaults."""
    if config_path and Path(config_path).exists():
        return ServerConfig.from_file(config_path)
    
    # Check for default config file
    default_config_path = Path("config.yaml")
    if default_config_path.exists():
        return ServerConfig.from_file(str(default_config_path))
    
    # Fall back to environment variables
    return ServerConfig.from_env()