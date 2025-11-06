#!/usr/bin/env python3
"""
MCP Prompts definitions for Consul
"""

import logging
from typing import Any, Dict, List
from mcp.types import Prompt, GetPromptResult, TextContent
from consul_client import ConsulClient


logger = logging.getLogger(__name__)


def get_prompt_definitions() -> List[Prompt]:
    """Get list of all available prompts"""
    return [
        Prompt(
            name="service_discovery",
            description="Discover and list services in Consul",
            arguments=[
                {
                    "name": "datacenter",
                    "description": "Datacenter to query (optional)",
                    "required": False
                }
            ]
        ),
        Prompt(
            name="service_health_check",
            description="Check health status of a service",
            arguments=[
                {
                    "name": "service_name",
                    "description": "Name of the service to check",
                    "required": True
                }
            ]
        ),
    ]


class PromptHandler:
    """Handler for MCP prompt operations"""
    
    def __init__(self, consul_client: ConsulClient):
        """
        Initialize prompt handler
        
        Args:
            consul_client: Consul client instance
        """
        self.consul_client = consul_client
    
    async def get_prompt(self, name: str, arguments: Dict[str, Any]) -> GetPromptResult:
        """
        Get a prompt result
        
        Args:
            name: Prompt name
            arguments: Prompt arguments
        
        Returns:
            GetPromptResult with prompt content
        """
        logger.info(f"Getting prompt: {name}")
        logger.debug(f"Prompt '{name}' arguments: {arguments}")
        
        try:
            if name == "service_discovery":
                return await self._handle_service_discovery(arguments)
            elif name == "service_health_check":
                return await self._handle_service_health_check(arguments)
            else:
                logger.warning(f"Unknown prompt: {name}")
                raise ValueError(f"Unknown prompt: {name}")
        
        except Exception as e:
            logger.error(f"Error getting prompt '{name}': {e}", exc_info=True)
            return GetPromptResult(
                description="Error",
                messages=[
                    TextContent(
                        type="text",
                        text=f"Error: {str(e)}"
                    )
                ]
            )
    
    async def _handle_service_discovery(self, arguments: Dict[str, Any]) -> GetPromptResult:
        """Handle service_discovery prompt"""
        dc = arguments.get("datacenter")
        logger.debug(f"Discovering services (datacenter={dc})")
        services = self.consul_client.list_services(dc)
        
        service_list_text = "\n".join(f"- {svc}" for svc in services)
        text = f"Found {len(services)} services in Consul:\n{service_list_text}"
        
        logger.info(f"Service discovery completed: {len(services)} services found")
        
        return GetPromptResult(
            description="Service discovery results",
            messages=[
                TextContent(
                    type="text",
                    text=text
                )
            ]
        )
    
    async def _handle_service_health_check(self, arguments: Dict[str, Any]) -> GetPromptResult:
        """Handle service_health_check prompt"""
        service_name = arguments.get("service_name")
        logger.debug(f"Checking health for service '{service_name}'")
        checks = self.consul_client.get_service_health(service_name)
        
        healthy_count = sum(1 for check in checks if check['Status'] == 'passing')
        total_count = len(checks)
        
        details = "\n".join(
            f"- {check['Node']}: {check['Status']}"
            for check in checks
        )
        
        text = (
            f"Service: {service_name}\n"
            f"Health Status: {healthy_count}/{total_count} instances passing\n"
            f"Details:\n{details}"
        )
        
        logger.info(f"Health check completed for '{service_name}': {healthy_count}/{total_count} passing")
        
        return GetPromptResult(
            description=f"Health check for {service_name}",
            messages=[
                TextContent(
                    type="text",
                    text=text
                )
            ]
        )

