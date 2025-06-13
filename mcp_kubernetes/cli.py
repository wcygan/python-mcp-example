"""Command-line interface for the Kubernetes MCP server."""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

from .config import ServerConfig
from .server import KubernetesMCPServer


def setup_logging(debug: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="MCP server for Kubernetes cluster management (read-only mode)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (default: config.yaml or environment variables)"
    )
    
    parser.add_argument(
        "--kubeconfig",
        type=str,
        help="Path to kubeconfig file (overrides config file setting)"
    )
    
    parser.add_argument(
        "--read-only",
        action="store_true",
        default=True,
        help="Enable read-only mode (default: true)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )
    
    return parser.parse_args()


async def main_async() -> None:
    """Main async entry point."""
    args = parse_args()
    setup_logging(args.debug)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Kubernetes MCP server in read-only mode")
    
    try:
        # Load configuration
        if args.config:
            config_file = Path(args.config)
            if not config_file.exists():
                logger.error(f"Configuration file not found: {args.config}")
                sys.exit(1)
            server_config = ServerConfig.from_file(str(config_file))
        else:
            # Use environment variables or defaults
            server_config = ServerConfig.from_env()
        
        # Override kubeconfig from command line if provided
        if args.kubeconfig:
            kubeconfig_file = Path(args.kubeconfig)
            if not kubeconfig_file.exists():
                logger.error(f"Kubeconfig file not found: {args.kubeconfig}")
                sys.exit(1)
            server_config.kubernetes.kubeconfig_path = str(kubeconfig_file)
        
        # Override debug logging if specified
        if args.debug:
            server_config.logging.level = "DEBUG"
        
        # Ensure read-only mode is enabled
        server_config.security.read_only_mode = True
        
        logger.info(f"Server configuration: read_only={server_config.security.read_only_mode}")
        logger.info(f"Allowed operations: {server_config.security.allowed_operations}")
        
        # Create and run server
        server = KubernetesMCPServer(server_config=server_config)
        await server.run_server()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()