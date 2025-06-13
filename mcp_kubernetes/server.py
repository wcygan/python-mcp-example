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

logger = logging.getLogger(__name__)


class KubernetesMCPServer:
    """MCP server providing Kubernetes cluster management capabilities."""

    def __init__(self, kubeconfig_path: Optional[str] = None):
        """Initialize the Kubernetes MCP server.
        
        Args:
            kubeconfig_path: Path to kubeconfig file. If None, uses default config.
        """
        self.server = Server("kubernetes-mcp")
        self.kubeconfig_path = kubeconfig_path
        
        # Kubernetes API clients
        self.v1_core: Optional[client.CoreV1Api] = None
        self.v1_apps: Optional[client.AppsV1Api] = None
        
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
            """List available Kubernetes management tools."""
            return [
                Tool(
                    name="get_pod_logs",
                    description="Get logs from a specific pod",
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
                    name="scale_deployment",
                    description="Scale a deployment to specified replica count",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "deployment_name": {
                                "type": "string",
                                "description": "Name of the deployment"
                            },
                            "namespace": {
                                "type": "string",
                                "description": "Kubernetes namespace", 
                                "default": "default"
                            },
                            "replicas": {
                                "type": "integer",
                                "description": "Target number of replicas"
                            }
                        },
                        "required": ["deployment_name", "replicas"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Execute Kubernetes management tools."""
            await self._ensure_connected()
            
            try:
                if name == "get_pod_logs":
                    result = await self._get_pod_logs(**arguments)
                elif name == "scale_deployment":
                    result = await self._scale_deployment(**arguments)
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
                if self.kubeconfig_path:
                    config.load_kube_config(config_file=self.kubeconfig_path)
                else:
                    # Try in-cluster config first, then local config
                    try:
                        config.load_incluster_config()
                    except config.ConfigException:
                        config.load_kube_config()
                
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
    
    async def _scale_deployment(self, deployment_name: str, replicas: int, 
                               namespace: str = "default") -> str:
        """Scale a deployment to specified replica count."""
        try:
            # Get current deployment
            deployment = self.v1_apps.read_namespaced_deployment(
                name=deployment_name, 
                namespace=namespace
            )
            
            # Update replica count
            deployment.spec.replicas = replicas
            
            # Apply the change
            self.v1_apps.patch_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=deployment
            )
            
            return f"Successfully scaled deployment {deployment_name} to {replicas} replicas"
        except ApiException as e:
            logger.error(f"Error scaling deployment: {e}")
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