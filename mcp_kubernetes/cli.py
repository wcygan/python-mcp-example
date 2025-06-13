"""Command-line interface for the Kubernetes MCP server."""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

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
        description="MCP server for Kubernetes cluster management"
    )
    
    parser.add_argument(
        "--kubeconfig",
        type=str,
        help="Path to kubeconfig file (default: use default config)"
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
    logger.info("Starting Kubernetes MCP server")
    
    # Validate kubeconfig if provided
    kubeconfig_path: Optional[str] = None
    if args.kubeconfig:
        kubeconfig_file = Path(args.kubeconfig)
        if not kubeconfig_file.exists():
            logger.error(f"Kubeconfig file not found: {args.kubeconfig}")
            sys.exit(1)
        kubeconfig_path = str(kubeconfig_file)
    
    try:
        # Create and run server
        server = KubernetesMCPServer(kubeconfig_path=kubeconfig_path)
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