#!/usr/bin/env python3
"""
MCP Resources definitions for Consul
"""

import json
import logging
from typing import List
from urllib.parse import urlparse
from mcp.types import Resource
from consul_client import ConsulClient


logger = logging.getLogger(__name__)


def get_resource_definitions() -> List[Resource]:
    """Get list of all available resources"""
    return [
        Resource(
            uri="consul://services",
            name="Consul Services",
            description="All registered services in Consul",
            mimeType="application/json"
        ),
        Resource(
            uri="consul://nodes",
            name="Consul Nodes",
            description="All nodes in Consul cluster",
            mimeType="application/json"
        ),
    ]


class ResourceHandler:
    """Handler for MCP resource operations"""
    
    def __init__(self, consul_client: ConsulClient):
        """
        Initialize resource handler
        
        Args:
            consul_client: Consul client instance
        """
        self.consul_client = consul_client
    
    async def read_resource(self, uri: str) -> str:
        """
        Read a Consul resource
        
        Args:
            uri: Resource URI
        
        Returns:
            Resource content as JSON string
        """
        logger.info(f"Reading resource: {uri}")
        parsed = urlparse(uri)
        
        if parsed.scheme != "consul":
            raise ValueError(f"Unknown URI scheme: {parsed.scheme}")
        
        try:
            if parsed.path == "/services":
                logger.debug("Reading services resource")
                services = self.consul_client.list_services()
                result = {
                    "services": services,
                    "count": len(services)
                }
                logger.info(f"Retrieved {len(services)} services")
                return json.dumps(result, indent=2)
            
            elif parsed.path == "/nodes":
                logger.debug("Reading nodes resource")
                nodes = self.consul_client.get_nodes()
                result = {
                    "nodes": nodes,
                    "count": len(nodes)
                }
                logger.info(f"Retrieved {len(nodes)} nodes")
                return json.dumps(result, indent=2, default=str)
            
            else:
                raise ValueError(f"Unknown resource path: {parsed.path}")
        
        except Exception as e:
            logger.error(f"Error reading resource {uri}: {e}", exc_info=True)
            raise

