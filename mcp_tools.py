#!/usr/bin/env python3
"""
MCP Tools definitions for Consul operations
"""

import json
import logging
from typing import Any, Dict, List
from mcp.types import Tool, TextContent
from consul_client import ConsulClient


logger = logging.getLogger(__name__)


def get_tool_definitions() -> List[Tool]:
    """Get list of all available tools"""
    return [
        Tool(
            name="list_services",
            description="List all services registered in Consul",
            inputSchema={
                "type": "object",
                "properties": {
                    "datacenter": {
                        "type": "string",
                        "description": "Datacenter to query (optional)"
                    }
                }
            }
        ),
        Tool(
            name="get_service",
            description="Get detailed information about a specific service",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Name of the service"
                    },
                    "datacenter": {
                        "type": "string",
                        "description": "Datacenter to query (optional)"
                    }
                },
                "required": ["service_name"]
            }
        ),
        Tool(
            name="get_service_instance_count",
            description="Get only the number of instances for a service (lightweight; use this for statistics/summary to avoid large responses)",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Name of the service"
                    },
                    "datacenter": {
                        "type": "string",
                        "description": "Datacenter to query (optional)"
                    }
                },
                "required": ["service_name"]
            }
        ),
        Tool(
            name="get_monitoring_summary",
            description="Get monitoring statistics: per-service instance counts and totals. Use this for counting monitoring entries (e.g. node_exporter, redis_exporter) without loading full instance lists. Returns only counts to avoid context overflow.",
            inputSchema={
                "type": "object",
                "properties": {
                    "datacenter": {
                        "type": "string",
                        "description": "Datacenter to query (optional)"
                    }
                }
            }
        ),
        Tool(
            name="register_service",
            description="Register a new service in Consul",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Service name"
                    },
                    "service_id": {
                        "type": "string",
                        "description": "Unique service ID"
                    },
                    "address": {
                        "type": "string",
                        "description": "Service address"
                    },
                    "port": {
                        "type": "integer",
                        "description": "Service port"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Service tags"
                    },
                    "check_http": {
                        "type": "string",
                        "description": "HTTP health check URL (optional)"
                    },
                    "check_interval": {
                        "type": "string",
                        "description": "Health check interval (e.g., '10s')"
                    }
                },
                "required": ["name", "address", "port"]
            }
        ),
        Tool(
            name="deregister_service",
            description="Deregister a service from Consul",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_id": {
                        "type": "string",
                        "description": "Service ID to deregister"
                    }
                },
                "required": ["service_id"]
            }
        ),
        Tool(
            name="get_kv",
            description="Get a key-value pair from Consul KV store",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Key to retrieve"
                    },
                    "datacenter": {
                        "type": "string",
                        "description": "Datacenter to query (optional)"
                    }
                },
                "required": ["key"]
            }
        ),
        Tool(
            name="put_kv",
            description="Store a key-value pair in Consul KV store",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Key to store"
                    },
                    "value": {
                        "type": "string",
                        "description": "Value to store"
                    },
                    "datacenter": {
                        "type": "string",
                        "description": "Datacenter to write to (optional)"
                    }
                },
                "required": ["key", "value"]
            }
        ),
        Tool(
            name="list_kv",
            description="List all keys in Consul KV store (optionally with prefix)",
            inputSchema={
                "type": "object",
                "properties": {
                    "prefix": {
                        "type": "string",
                        "description": "Key prefix to filter (optional)"
                    },
                    "datacenter": {
                        "type": "string",
                        "description": "Datacenter to query (optional)"
                    }
                }
            }
        ),
        Tool(
            name="delete_kv",
            description="Delete a key from Consul KV store",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Key to delete"
                    },
                    "datacenter": {
                        "type": "string",
                        "description": "Datacenter to delete from (optional)"
                    }
                },
                "required": ["key"]
            }
        ),
        Tool(
            name="get_nodes",
            description="Get list of nodes in Consul cluster",
            inputSchema={
                "type": "object",
                "properties": {
                    "datacenter": {
                        "type": "string",
                        "description": "Datacenter to query (optional)"
                    }
                }
            }
        ),
        Tool(
            name="get_service_health",
            description="Get health status of a service",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Name of the service"
                    },
                    "datacenter": {
                        "type": "string",
                        "description": "Datacenter to query (optional)"
                    }
                },
                "required": ["service_name"]
            }
        ),
        # Service instance meta & tags (under Services -> instance Tags & Meta)
        Tool(
            name="get_service_meta",
            description="Get all Meta for a service instance (Services API)",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_id": {"type": "string", "description": "Service instance ID"},
                    "datacenter": {"type": "string", "description": "Datacenter (optional)"}
                },
                "required": ["service_id"]
            }
        ),
        Tool(
            name="set_service_meta_key",
            description="Set or update one Meta key for a service instance (Services API)",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_id": {"type": "string", "description": "Service instance ID"},
                    "key": {"type": "string", "description": "Meta key"},
                    "value": {"type": "string", "description": "Meta value"},
                    "datacenter": {"type": "string", "description": "Datacenter (optional)"}
                },
                "required": ["service_id", "key", "value"]
            }
        ),
        Tool(
            name="delete_service_meta_key",
            description="Delete one Meta key for a service instance (Services API)",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_id": {"type": "string", "description": "Service instance ID"},
                    "key": {"type": "string", "description": "Meta key"},
                    "datacenter": {"type": "string", "description": "Datacenter (optional)"}
                },
                "required": ["service_id", "key"]
            }
        ),
        Tool(
            name="set_service_meta_bulk",
            description="Set or update multiple Meta keys for a service instance (Services API)",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_id": {"type": "string", "description": "Service instance ID"},
                    "meta": {"type": "object", "description": "Key-value object of meta entries"},
                    "datacenter": {"type": "string", "description": "Datacenter (optional)"}
                },
                "required": ["service_id", "meta"]
            }
        ),
        Tool(
            name="list_service_meta_keys",
            description="List all Meta keys for a service instance (Services API)",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_id": {"type": "string", "description": "Service instance ID"},
                    "datacenter": {"type": "string", "description": "Datacenter (optional)"}
                },
                "required": ["service_id"]
            }
        ),
        Tool(
            name="get_service_tags",
            description="Get Tags for a service instance (Services API)",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_id": {"type": "string", "description": "Service instance ID"}
                },
                "required": ["service_id"]
            }
        ),
        Tool(
            name="set_service_tags",
            description="Overwrite Tags for a service instance (Services API)",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_id": {"type": "string", "description": "Service instance ID"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags list"}
                },
                "required": ["service_id", "tags"]
            }
        ),
    ]


class ToolHandler:
    """Handler for MCP tool calls"""
    
    def __init__(self, consul_client: ConsulClient):
        """
        Initialize tool handler
        
        Args:
            consul_client: Consul client instance
        """
        self.consul_client = consul_client
    
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Handle a tool call
        
        Args:
            name: Tool name
            arguments: Tool arguments
        
        Returns:
            List of TextContent results
        """
        logger.info(f"Tool call received: {name}")
        logger.debug(f"Tool '{name}' arguments: {arguments}")
        
        try:
            if name == "list_services":
                return await self._handle_list_services(arguments)
            elif name == "get_service":
                return await self._handle_get_service(arguments)
            elif name == "get_service_instance_count":
                return await self._handle_get_service_instance_count(arguments)
            elif name == "get_monitoring_summary":
                return await self._handle_get_monitoring_summary(arguments)
            elif name == "register_service":
                return await self._handle_register_service(arguments)
            elif name == "deregister_service":
                return await self._handle_deregister_service(arguments)
            elif name == "get_kv":
                return await self._handle_get_kv(arguments)
            elif name == "put_kv":
                return await self._handle_put_kv(arguments)
            elif name == "list_kv":
                return await self._handle_list_kv(arguments)
            elif name == "delete_kv":
                return await self._handle_delete_kv(arguments)
            elif name == "get_nodes":
                return await self._handle_get_nodes(arguments)
            elif name == "get_service_health":
                return await self._handle_get_service_health(arguments)
            elif name == "get_service_meta":
                return await self._handle_get_service_meta(arguments)
            elif name == "set_service_meta_key":
                return await self._handle_set_service_meta_key(arguments)
            elif name == "delete_service_meta_key":
                return await self._handle_delete_service_meta_key(arguments)
            elif name == "set_service_meta_bulk":
                return await self._handle_set_service_meta_bulk(arguments)
            elif name == "list_service_meta_keys":
                return await self._handle_list_service_meta_keys(arguments)
            elif name == "get_service_tags":
                return await self._handle_get_service_tags(arguments)
            elif name == "set_service_tags":
                return await self._handle_set_service_tags(arguments)
            else:
                logger.warning(f"Unknown tool: {name}")
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Unknown tool: {name}"
                    }, indent=2)
                )]
        
        except Exception as e:
            logger.error(f"Error executing tool '{name}': {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "tool": name
                }, indent=2)
            )]
    
    async def _handle_list_services(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle list_services tool call"""
        dc = arguments.get("datacenter")
        service_list = self.consul_client.list_services(dc)
        return [TextContent(
            type="text",
            text=json.dumps({
                "services": service_list,
                "count": len(service_list)
            }, indent=2)
        )]
    
    async def _handle_get_service(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle get_service tool call"""
        service_name = arguments.get("service_name")
        dc = arguments.get("datacenter")
        nodes = self.consul_client.get_service(service_name, dc)
        return [TextContent(
            type="text",
            text=json.dumps({
                "service": service_name,
                "instances": nodes,
                "count": len(nodes)
            }, indent=2, default=str)
        )]

    async def _handle_get_service_instance_count(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle get_service_instance_count tool call (lightweight, for statistics)."""
        service_name = arguments.get("service_name")
        dc = arguments.get("datacenter")
        count = self.consul_client.get_service_instance_count(service_name, dc)
        return [TextContent(
            type="text",
            text=json.dumps({
                "service": service_name,
                "count": count
            }, indent=2)
        )]

    async def _handle_get_monitoring_summary(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle get_monitoring_summary: return per-service instance counts and totals only (no instance details)."""
        dc = arguments.get("datacenter")
        summary = self.consul_client.get_services_summary(dc)
        return [TextContent(
            type="text",
            text=json.dumps(summary, indent=2)
        )]
    
    async def _handle_register_service(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle register_service tool call"""
        self.consul_client.register_service(
            name=arguments.get("name"),
            service_id=arguments.get("service_id"),
            address=arguments.get("address"),
            port=arguments.get("port"),
            tags=arguments.get("tags", []),
            check_http=arguments.get("check_http"),
            check_interval=arguments.get("check_interval", "10s")
        )
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "success",
                "message": f"Service {arguments.get('name')} registered successfully"
            }, indent=2)
        )]
    
    async def _handle_deregister_service(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle deregister_service tool call"""
        service_id = arguments.get("service_id")
        self.consul_client.deregister_service(service_id)
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "success",
                "message": f"Service {service_id} deregistered successfully"
            }, indent=2)
        )]
    
    async def _handle_get_kv(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle get_kv tool call"""
        key = arguments.get("key")
        dc = arguments.get("datacenter")
        data = self.consul_client.get_kv(key, dc)
        if data:
            return [TextContent(
                type="text",
                text=json.dumps(data, indent=2)
            )]
        else:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "key": key,
                    "value": None,
                    "message": "Key not found"
                }, indent=2)
            )]
    
    async def _handle_put_kv(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle put_kv tool call"""
        key = arguments.get("key")
        value = arguments.get("value")
        dc = arguments.get("datacenter")
        result = self.consul_client.put_kv(key, value, dc)
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "success" if result else "failed",
                "key": key,
                "value": value
            }, indent=2)
        )]
    
    async def _handle_list_kv(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle list_kv tool call"""
        prefix = arguments.get("prefix", "")
        dc = arguments.get("datacenter")
        key_list = self.consul_client.list_kv(prefix, dc)
        return [TextContent(
            type="text",
            text=json.dumps({
                "prefix": prefix,
                "keys": key_list,
                "count": len(key_list)
            }, indent=2)
        )]
    
    async def _handle_delete_kv(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle delete_kv tool call"""
        key = arguments.get("key")
        dc = arguments.get("datacenter")
        result = self.consul_client.delete_kv(key, dc)
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "success" if result else "failed",
                "key": key,
                "message": f"Key {key} deleted"
            }, indent=2)
        )]
    
    async def _handle_get_nodes(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle get_nodes tool call"""
        dc = arguments.get("datacenter")
        nodes = self.consul_client.get_nodes(dc)
        return [TextContent(
            type="text",
            text=json.dumps({
                "nodes": nodes,
                "count": len(nodes)
            }, indent=2, default=str)
        )]
    
    async def _handle_get_service_health(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle get_service_health tool call"""
        service_name = arguments.get("service_name")
        dc = arguments.get("datacenter")
        checks = self.consul_client.get_service_health(service_name, dc)
        return [TextContent(
            type="text",
            text=json.dumps({
                "service": service_name,
                "health_checks": checks,
                "count": len(checks)
            }, indent=2, default=str)
        )]

    # -------- Service meta handlers --------
    async def _handle_get_service_meta(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle get_service_meta tool call"""
        service_id = arguments.get("service_id")
        meta = self.consul_client.get_service_instance_meta(service_id)
        return [TextContent(
            type="text",
            text=json.dumps({
                "service_id": service_id,
                "meta": meta,
                "count": len(meta)
            }, indent=2)
        )]

    async def _handle_set_service_meta_key(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle set_service_meta_key tool call"""
        service_id = arguments.get("service_id")
        key = arguments.get("key")
        value = arguments.get("value")
        # Use set_service_instance_meta with a single key-value pair
        updated_meta = self.consul_client.set_service_instance_meta(service_id, {key: value})
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "success",
                "service_id": service_id,
                "key": key,
                "updated_meta": updated_meta
            }, indent=2)
        )]

    async def _handle_delete_service_meta_key(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle delete_service_meta_key tool call"""
        service_id = arguments.get("service_id")
        key = arguments.get("key")
        # Use delete_service_instance_meta_keys with a list
        updated_meta = self.consul_client.delete_service_instance_meta_keys(service_id, [key])
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "success",
                "service_id": service_id,
                "deleted_key": key,
                "updated_meta": updated_meta
            }, indent=2)
        )]

    async def _handle_set_service_meta_bulk(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle set_service_meta_bulk tool call"""
        service_id = arguments.get("service_id")
        meta = arguments.get("meta") or {}
        if not isinstance(meta, dict):
            raise ValueError("meta must be a dictionary/object")
        # Use set_service_instance_meta with the full meta dict
        updated_meta = self.consul_client.set_service_instance_meta(service_id, meta)
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "success",
                "service_id": service_id,
                "updated_meta": updated_meta,
                "keys_updated": list(meta.keys())
            }, indent=2)
        )]

    async def _handle_list_service_meta_keys(self, arguments: Dict[str, Any]) -> List[TextContent]:
        service_id = arguments.get("service_id")
        dc = arguments.get("datacenter")
        meta = self.consul_client.get_service_instance_meta(service_id)
        keys = list(meta.keys())
        return [TextContent(type="text", text=json.dumps({"service_id": service_id, "keys": keys, "count": len(keys)}, indent=2))]

    async def _handle_get_service_tags(self, arguments: Dict[str, Any]) -> List[TextContent]:
        service_id = arguments.get("service_id")
        tags = self.consul_client.get_service_instance_tags(service_id)
        return [TextContent(type="text", text=json.dumps({"service_id": service_id, "tags": tags, "count": len(tags)}, indent=2))]

    async def _handle_set_service_tags(self, arguments: Dict[str, Any]) -> List[TextContent]:
        service_id = arguments.get("service_id")
        tags = arguments.get("tags") or []
        updated = self.consul_client.set_service_instance_tags(service_id, tags)
        return [TextContent(type="text", text=json.dumps({"status": "success", "service_id": service_id, "tags": updated}, indent=2))]

