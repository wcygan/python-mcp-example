"""Core MCP server implementation for Kubernetes integration."""

import json
import logging
from typing import Any, Dict, List, Optional, Sequence

from kubernetes import client, config
from kubernetes.client.rest import ApiException
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    CallToolResult,
    ListResourcesResult,
    ReadResourceResult,
)

from .config import ServerConfig, load_config

logger = logging.getLogger(__name__)


class KubernetesMCPServer:
    """MCP server providing Kubernetes cluster management capabilities."""

    def __init__(self, config_path: Optional[str] = None, server_config: Optional[ServerConfig] = None):
        """Initialize the Kubernetes MCP server.
        
        Args:
            config_path: Path to configuration file. If None, uses environment or defaults.
            server_config: Pre-loaded server configuration. Takes precedence over config_path.
        """
        # Load configuration
        if server_config:
            self.config = server_config
        else:
            self.config = load_config(config_path)
        
        # Initialize MCP server
        self.server = Server(self.config.mcp.server_name)
        
        # Kubernetes API clients
        self.v1_core: Optional[client.CoreV1Api] = None
        self.v1_apps: Optional[client.AppsV1Api] = None
        
        # Setup logging
        logging.getLogger().setLevel(getattr(logging, self.config.logging.level))
        
        # Setup handlers
        self._setup_handlers()
        
    def _setup_handlers(self) -> None:
        """Setup MCP protocol handlers."""
        
        @self.server.list_resources()
        async def list_resources() -> ListResourcesResult:
            """List available Kubernetes resources."""
            resources = [
                Resource(
                    uri="k8s://pods",
                    name="Kubernetes Pods",
                    description="List and inspect Kubernetes pods",
                    mimeType="application/json"
                ),
                Resource(
                    uri="k8s://services", 
                    name="Kubernetes Services",
                    description="List and inspect Kubernetes services",
                    mimeType="application/json"
                ),
                Resource(
                    uri="k8s://deployments",
                    name="Kubernetes Deployments", 
                    description="List and inspect Kubernetes deployments",
                    mimeType="application/json"
                ),
                Resource(
                    uri="k8s://namespaces",
                    name="Kubernetes Namespaces",
                    description="List Kubernetes namespaces",
                    mimeType="application/json"
                )
            ]
            return ListResourcesResult(resources=resources)
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> ReadResourceResult:
            """Read specific Kubernetes resource data."""
            await self._ensure_connected()
            
            try:
                if uri.startswith("k8s://pods"):
                    namespace = self._extract_namespace_from_uri(uri)
                    data = await self._list_pods(namespace)
                elif uri.startswith("k8s://services"):
                    namespace = self._extract_namespace_from_uri(uri)
                    data = await self._list_services(namespace)
                elif uri.startswith("k8s://deployments"):
                    namespace = self._extract_namespace_from_uri(uri)
                    data = await self._list_deployments(namespace)
                elif uri.startswith("k8s://namespaces"):
                    data = await self._list_namespaces()
                else:
                    raise ValueError(f"Unknown resource URI: {uri}")
                
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text=json.dumps(data, indent=2, default=str)
                        )
                    ]
                )
            except Exception as e:
                logger.error(f"Error reading resource {uri}: {e}")
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text", 
                            text=f"Error reading resource: {str(e)}"
                        )
                    ]
                )
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available Kubernetes read-only tools."""
            return [
                Tool(
                    name="get_pod_logs",
                    description="Get logs from a specific pod (read-only)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pod_name": {
                                "type": "string",
                                "description": "Name of the pod"
                            },
                            "namespace": {
                                "type": "string", 
                                "description": "Kubernetes namespace",
                                "default": "default"
                            },
                            "lines": {
                                "type": "integer",
                                "description": "Number of log lines to retrieve",
                                "default": 100
                            },
                            "container": {
                                "type": "string",
                                "description": "Container name (for multi-container pods)"
                            }
                        },
                        "required": ["pod_name"]
                    }
                ),
                Tool(
                    name="describe_pod",
                    description="Get detailed information about a specific pod (read-only)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pod_name": {
                                "type": "string",
                                "description": "Name of the pod"
                            },
                            "namespace": {
                                "type": "string",
                                "description": "Kubernetes namespace",
                                "default": "default"
                            }
                        },
                        "required": ["pod_name"]
                    }
                ),
                Tool(
                    name="get_pod_status",
                    description="Get current status of pods matching criteria (read-only)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "namespace": {
                                "type": "string",
                                "description": "Kubernetes namespace to filter by"
                            },
                            "label_selector": {
                                "type": "string",
                                "description": "Label selector to filter pods (e.g., 'app=nginx')"
                            },
                            "field_selector": {
                                "type": "string",
                                "description": "Field selector to filter pods (e.g., 'status.phase=Running')"
                            }
                        }
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Execute Kubernetes read-only tools."""
            await self._ensure_connected()
            
            try:
                if name == "get_pod_logs":
                    result = await self._get_pod_logs(**arguments)
                elif name == "describe_pod":
                    result = await self._describe_pod(**arguments)
                elif name == "get_pod_status":
                    result = await self._get_pod_status(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=result
                        )
                    ]
                )
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Error executing {name}: {str(e)}"
                        )
                    ],
                    isError=True
                )
    
    async def _ensure_connected(self) -> None:
        """Ensure connection to Kubernetes cluster."""
        if self.v1_core is None:
            try:
                if self.config.kubernetes.use_service_account:
                    config.load_incluster_config()
                elif self.config.kubernetes.kubeconfig_path:
                    config.load_kube_config(
                        config_file=self.config.kubernetes.kubeconfig_path,
                        context=self.config.kubernetes.context
                    )
                else:
                    # Try in-cluster config first, then local config
                    try:
                        config.load_incluster_config()
                    except config.ConfigException:
                        config.load_kube_config(context=self.config.kubernetes.context)
                
                # Set timeout configuration
                configuration = client.Configuration.get_default_copy()
                configuration.timeout = self.config.kubernetes.timeout
                client.Configuration.set_default(configuration)
                
                self.v1_core = client.CoreV1Api()
                self.v1_apps = client.AppsV1Api()
                
                # Test connection
                await self._test_connection()
                
            except Exception as e:
                logger.error(f"Failed to connect to Kubernetes: {e}")
                raise ConnectionError(f"Cannot connect to Kubernetes cluster: {e}")
    
    async def _test_connection(self) -> None:
        """Test Kubernetes cluster connection."""
        try:
            self.v1_core.list_namespace(limit=1)
            logger.info("Successfully connected to Kubernetes cluster")
        except ApiException as e:
            logger.error(f"Kubernetes API error: {e}")
            raise
    
    def _extract_namespace_from_uri(self, uri: str) -> Optional[str]:
        """Extract namespace parameter from URI."""
        if "?" in uri:
            query = uri.split("?", 1)[1]
            for param in query.split("&"):
                if param.startswith("namespace="):
                    return param.split("=", 1)[1]
        return None
    
    async def _list_pods(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """List pods in specified namespace or all namespaces."""
        try:
            if namespace:
                response = self.v1_core.list_namespaced_pod(namespace=namespace)
            else:
                response = self.v1_core.list_pod_for_all_namespaces()
            
            pods = []
            for pod in response.items:
                pods.append({
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "status": pod.status.phase,
                    "created": pod.metadata.creation_timestamp,
                    "ready_containers": sum(1 for c in (pod.status.container_statuses or []) if c.ready),
                    "total_containers": len(pod.spec.containers),
                    "node": pod.spec.node_name,
                    "pod_ip": pod.status.pod_ip
                })
            
            return pods
        except ApiException as e:
            logger.error(f"Error listing pods: {e}")
            raise
    
    async def _list_services(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """List services in specified namespace or all namespaces."""
        try:
            if namespace:
                response = self.v1_core.list_namespaced_service(namespace=namespace)
            else:
                response = self.v1_core.list_service_for_all_namespaces()
            
            services = []
            for svc in response.items:
                services.append({
                    "name": svc.metadata.name,
                    "namespace": svc.metadata.namespace,
                    "type": svc.spec.type,
                    "cluster_ip": svc.spec.cluster_ip,
                    "ports": [{"port": p.port, "target_port": p.target_port, "protocol": p.protocol} for p in (svc.spec.ports or [])],
                    "selector": svc.spec.selector or {},
                    "created": svc.metadata.creation_timestamp
                })
            
            return services
        except ApiException as e:
            logger.error(f"Error listing services: {e}")
            raise
    
    async def _list_deployments(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """List deployments in specified namespace or all namespaces."""
        try:
            if namespace:
                response = self.v1_apps.list_namespaced_deployment(namespace=namespace)
            else:
                response = self.v1_apps.list_deployment_for_all_namespaces()
            
            deployments = []
            for deploy in response.items:
                deployments.append({
                    "name": deploy.metadata.name,
                    "namespace": deploy.metadata.namespace,
                    "ready_replicas": deploy.status.ready_replicas or 0,
                    "replicas": deploy.spec.replicas or 0,
                    "updated_replicas": deploy.status.updated_replicas or 0,
                    "available_replicas": deploy.status.available_replicas or 0,
                    "selector": deploy.spec.selector.match_labels or {},
                    "created": deploy.metadata.creation_timestamp
                })
            
            return deployments
        except ApiException as e:
            logger.error(f"Error listing deployments: {e}")
            raise
    
    async def _list_namespaces(self) -> List[Dict[str, Any]]:
        """List all namespaces."""
        try:
            response = self.v1_core.list_namespace()
            
            namespaces = []
            for ns in response.items:
                namespaces.append({
                    "name": ns.metadata.name,
                    "status": ns.status.phase,
                    "created": ns.metadata.creation_timestamp,
                    "labels": ns.metadata.labels or {}
                })
            
            return namespaces
        except ApiException as e:
            logger.error(f"Error listing namespaces: {e}")
            raise
    
    async def _get_pod_logs(self, pod_name: str, namespace: str = "default", 
                           lines: int = 100, container: Optional[str] = None) -> str:
        """Get logs from a specific pod."""
        try:
            kwargs = {
                "name": pod_name,
                "namespace": namespace,
                "tail_lines": lines
            }
            if container:
                kwargs["container"] = container
            
            logs = self.v1_core.read_namespaced_pod_log(**kwargs)
            return logs
        except ApiException as e:
            logger.error(f"Error getting pod logs: {e}")
            raise
    
    async def _describe_pod(self, pod_name: str, namespace: str = "default") -> str:
        """Get detailed information about a specific pod."""
        try:
            pod = self.v1_core.read_namespaced_pod(name=pod_name, namespace=namespace)
            
            # Format pod details as readable text
            details = {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase,
                "created": pod.metadata.creation_timestamp,
                "node": pod.spec.node_name,
                "pod_ip": pod.status.pod_ip,
                "host_ip": pod.status.host_ip,
                "labels": pod.metadata.labels or {},
                "annotations": pod.metadata.annotations or {},
                "containers": [],
                "conditions": []
            }
            
            # Add container information
            if pod.spec.containers:
                for container in pod.spec.containers:
                    container_info = {
                        "name": container.name,
                        "image": container.image,
                        "ports": [{"containerPort": p.container_port, "protocol": p.protocol} for p in (container.ports or [])],
                        "resources": {
                            "requests": container.resources.requests if container.resources and container.resources.requests else {},
                            "limits": container.resources.limits if container.resources and container.resources.limits else {}
                        }
                    }
                    details["containers"].append(container_info)
            
            # Add container status information
            if pod.status.container_statuses:
                for i, status in enumerate(pod.status.container_statuses):
                    if i < len(details["containers"]):
                        details["containers"][i].update({
                            "ready": status.ready,
                            "restart_count": status.restart_count,
                            "state": str(status.state)
                        })
            
            # Add pod conditions
            if pod.status.conditions:
                for condition in pod.status.conditions:
                    details["conditions"].append({
                        "type": condition.type,
                        "status": condition.status,
                        "reason": condition.reason,
                        "message": condition.message,
                        "last_transition_time": condition.last_transition_time
                    })
            
            return json.dumps(details, indent=2, default=str)
        except ApiException as e:
            logger.error(f"Error describing pod: {e}")
            raise
    
    async def _get_pod_status(self, namespace: Optional[str] = None, 
                             label_selector: Optional[str] = None,
                             field_selector: Optional[str] = None) -> str:
        """Get current status of pods matching criteria."""
        try:
            kwargs = {}
            if label_selector:
                kwargs["label_selector"] = label_selector
            if field_selector:
                kwargs["field_selector"] = field_selector
            
            if namespace:
                response = self.v1_core.list_namespaced_pod(namespace=namespace, **kwargs)
            else:
                response = self.v1_core.list_pod_for_all_namespaces(**kwargs)
            
            pod_statuses = []
            for pod in response.items:
                status_info = {
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "phase": pod.status.phase,
                    "ready": "0/0",
                    "restarts": 0,
                    "age": pod.metadata.creation_timestamp,
                    "node": pod.spec.node_name,
                    "pod_ip": pod.status.pod_ip
                }
                
                # Calculate ready containers
                if pod.status.container_statuses:
                    ready_count = sum(1 for c in pod.status.container_statuses if c.ready)
                    total_count = len(pod.status.container_statuses)
                    status_info["ready"] = f"{ready_count}/{total_count}"
                    status_info["restarts"] = sum(c.restart_count for c in pod.status.container_statuses)
                
                # Add reason for non-running pods
                if pod.status.phase != "Running" and pod.status.container_statuses:
                    for container_status in pod.status.container_statuses:
                        if container_status.state and container_status.state.waiting:
                            status_info["reason"] = container_status.state.waiting.reason
                            break
                
                pod_statuses.append(status_info)
            
            return json.dumps(pod_statuses, indent=2, default=str)
        except ApiException as e:
            logger.error(f"Error getting pod status: {e}")
            raise
    
    async def run_server(self) -> None:
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="kubernetes-mcp",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None
                    )
                )
            )