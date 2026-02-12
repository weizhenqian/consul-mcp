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
                },
                {
                    "name": "datacenter",
                    "description": "Datacenter to query (optional)",
                    "required": False
                }
            ]
        ),
        Prompt(
            name="monitoring_summary",
            description="Get monitoring statistics: per-service instance counts and total. Use for counting monitoring entries (e.g. node_exporter, redis_exporter) without loading full data.",
            arguments=[
                {
                    "name": "datacenter",
                    "description": "Datacenter to query (optional)",
                    "required": False
                }
            ]
        ),
        Prompt(
            name="monitoring_agent_instructions",
            description="Get system instructions for the monitoring AI agent: how to count monitoring entries without exceeding context (use summary tools).",
            arguments=[]
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
            elif name == "monitoring_summary":
                return await self._handle_monitoring_summary(arguments)
            elif name == "monitoring_agent_instructions":
                return await self._handle_monitoring_agent_instructions(arguments)
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
        dc = arguments.get("datacenter")
        logger.debug(f"Checking health for service '{service_name}' (datacenter={dc})")
        entries = self.consul_client.get_service_health(service_name, dc)
        # Each entry: {Node: {...}, Service: {...}, Checks: [{Status: 'passing'|'warning'|'critical'}, ...]}
        def is_passing(entry: Dict[str, Any]) -> bool:
            for c in entry.get("Checks", []):
                if c.get("Status") == "passing":
                    return True
            return False
        healthy_count = sum(1 for e in entries if is_passing(e))
        total_count = len(entries)
        node_names = [e.get("Node", {}).get("Node", "?") if isinstance(e.get("Node"), dict) else str(e.get("Node", "?")) for e in entries]
        details = "\n".join(
            f"- {node}: {'passing' if is_passing(e) else 'not passing'}"
            for node, e in zip(node_names, entries)
        )
        text = (
            f"Service: {service_name}\n"
            f"Health Status: {healthy_count}/{total_count} instances passing\n"
            f"Details:\n{details}"
        )
        logger.info(f"Health check completed for '{service_name}': {healthy_count}/{total_count} passing")
        return GetPromptResult(
            description=f"Health check for {service_name}",
            messages=[TextContent(type="text", text=text)]
        )

    async def _handle_monitoring_summary(self, arguments: Dict[str, Any]) -> GetPromptResult:
        """Return current monitoring summary (per-service instance counts and totals)."""
        dc = arguments.get("datacenter")
        logger.debug(f"Getting monitoring summary (datacenter={dc})")
        summary = self.consul_client.get_services_summary(dc)
        services = summary.get("services", {})
        total_services = summary.get("total_services", 0)
        total_instances = summary.get("total_instances", 0)
        lines = [f"- {name}: {count} 个实例" for name, count in sorted(services.items())]
        text = (
            f"## 监控统计\n\n"
            f"**服务类型数**: {total_services}\n"
            f"**监控实例总数**: {total_instances}\n\n"
            f"**各类型实例数**:\n" + "\n".join(lines)
        )
        logger.info(f"Monitoring summary: {total_services} services, {total_instances} instances")
        return GetPromptResult(
            description="监控统计结果",
            messages=[TextContent(type="text", text=text)]
        )

    async def _handle_monitoring_agent_instructions(self, arguments: Dict[str, Any]) -> GetPromptResult:
        """Return system instructions for the monitoring AI agent."""
        text = """你是一个基于 Consul 的 Prometheus 服务发现监控统计助手。Consul 中每个 service 代表一类监控（如 node_exporter、redis_exporter），每个 service 下的实例代表不同的监控 agent（如 "IP:9100"）。

**统计监控条目时的规则（避免超出上下文）：**

1. **优先使用汇总接口，不要拉取完整实例列表**
   - 调用 **get_monitoring_summary** 获取：各 service 的实例数量 + 总服务类型数 + 总实例数。返回体小，不会撑爆上下文。
   - 仅当用户明确需要“某类监控的实例列表”时，再对**单个** service 使用 **get_service**；不要对全部 service 逐个调用 get_service。

2. **按需使用单服务计数**
   - 若只需某一类监控的条数，使用 **get_service_instance_count**（参数：service_name），不要使用 get_service 再自己数。

3. **禁止的做法**
   - 不要先 list_services 再对每一个 service 调用 get_service 来“统计”，这会返回大量实例详情导致上下文溢出。
   - 统计类问题（如“一共有多少监控项”“每类有多少”）一律先用 get_monitoring_summary。

4. **推荐流程**
   - 用户问“统计监控条目”/“有多少监控”/“每类 exporter 各多少” → 只调用 get_monitoring_summary，根据返回的 services 与 total_instances 作答。
   - 用户问“某类监控的实例列表” → 先可用 get_service_instance_count 看数量，再视需要调用 get_service 获取该 service 的实例列表。"""
        return GetPromptResult(
            description="监控 AI Agent 使用说明",
            messages=[TextContent(type="text", text=text)]
        )

