#!/usr/bin/env python3
"""
Consul client wrapper for Consul MCP Server
"""

import logging
import consul
from typing import Optional, Dict, Any, List, Tuple
import json
from config import ConsulConfig


logger = logging.getLogger(__name__)


class ConsulClient:
    """Wrapper around python-consul client with enhanced logging"""
    
    def __init__(self, config: ConsulConfig):
        """
        Initialize Consul client
        
        Args:
            config: Consul configuration
        """
        self.config = config
        self.client: Optional[consul.Consul] = None
        self._connect()
    
    def _connect(self) -> None:
        """Connect to Consul"""
        try:
            logger.info(f"Connecting to Consul at {self.config.host}:{self.config.port}")
            logger.debug(f"Consul configuration: {self.config}")
            
            self.client = consul.Consul(
                host=self.config.host,
                port=self.config.port,
                token=self.config.token,
                dc=self.config.dc
            )
            
            # Test connection
            self.client.agent.self()
            logger.info(f"Successfully connected to Consul at {self.config.host}:{self.config.port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Consul: {e}", exc_info=True)
            self.client = None
            raise
    
    def is_connected(self) -> bool:
        """Check if client is connected"""
        if self.client is None:
            return False
        try:
            self.client.agent.self()
            return True
        except Exception:
            return False
    
    def list_services(self, datacenter: Optional[str] = None) -> List[str]:
        """List all services"""
        logger.debug(f"Listing services (datacenter={datacenter})")
        try:
            index, services = self.client.catalog.services(dc=datacenter)
            service_list = list(services.keys())
            logger.info(f"Found {len(service_list)} services")
            logger.debug(f"Services: {service_list}")
            return service_list
        except Exception as e:
            logger.error(f"Error listing services: {e}", exc_info=True)
            raise
    
    def get_service(self, service_name: str, datacenter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get service instances"""
        logger.debug(f"Getting service '{service_name}' (datacenter={datacenter})")
        try:
            index, nodes = self.client.catalog.service(service_name, dc=datacenter)
            logger.info(f"Found {len(nodes)} instances for service '{service_name}'")
            logger.debug(f"Service instances: {nodes}")
            return nodes
        except Exception as e:
            logger.error(f"Error getting service '{service_name}': {e}", exc_info=True)
            raise

    def get_service_instance_count(self, service_name: str, datacenter: Optional[str] = None) -> int:
        """Get only the instance count for a service (lightweight, for statistics)."""
        logger.debug(f"Getting instance count for service '{service_name}' (datacenter={datacenter})")
        try:
            index, nodes = self.client.catalog.service(service_name, dc=datacenter)
            count = len(nodes)
            logger.info(f"Service '{service_name}' has {count} instances")
            return count
        except Exception as e:
            logger.error(f"Error getting count for service '{service_name}': {e}", exc_info=True)
            raise

    def get_services_summary(self, datacenter: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of all services: service name -> instance count. Lightweight for monitoring stats (no instance details)."""
        logger.debug(f"Getting services summary (datacenter={datacenter})")
        try:
            names = self.list_services(datacenter)
            summary: Dict[str, int] = {}
            total_instances = 0
            for name in names:
                cnt = self.get_service_instance_count(name, datacenter)
                summary[name] = cnt
                total_instances += cnt
            result = {
                "services": summary,
                "total_services": len(summary),
                "total_instances": total_instances,
            }
            logger.info(f"Services summary: {result['total_services']} services, {result['total_instances']} total instances")
            return result
        except Exception as e:
            logger.error(f"Error getting services summary: {e}", exc_info=True)
            raise

    def register_service(
        self,
        name: str,
        address: str,
        port: int,
        service_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        check_http: Optional[str] = None,
        check_interval: str = "10s"
    ) -> None:
        """Register a service"""
        logger.info(f"Registering service '{name}' at {address}:{port}")
        logger.debug(f"Service details: id={service_id}, tags={tags}, check={check_http}")
        try:
            check = None
            if check_http:
                check = consul.Check.http(check_http, interval=check_interval)
            
            self.client.agent.service.register(
                name=name,
                service_id=service_id or name,
                address=address,
                port=port,
                tags=tags or [],
                check=check
            )
            logger.info(f"Successfully registered service '{name}'")
        except Exception as e:
            logger.error(f"Error registering service '{name}': {e}", exc_info=True)
            raise
    
    def deregister_service(self, service_id: str) -> None:
        """Deregister a service"""
        logger.info(f"Deregistering service '{service_id}'")
        try:
            self.client.agent.service.deregister(service_id)
            logger.info(f"Successfully deregistered service '{service_id}'")
        except Exception as e:
            logger.error(f"Error deregistering service '{service_id}': {e}", exc_info=True)
            raise
    
    def get_kv(self, key: str, datacenter: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get key-value pair"""
        logger.debug(f"Getting KV key '{key}' (datacenter={datacenter})")
        try:
            index, data = self.client.kv.get(key, dc=datacenter)
            if data:
                value = data['Value'].decode('utf-8') if data['Value'] else None
                logger.debug(f"Retrieved KV key '{key}', value length: {len(value) if value else 0}")
                return {
                    "key": key,
                    "value": value,
                    "flags": data.get('Flags', 0),
                    "create_index": data.get('CreateIndex'),
                    "modify_index": data.get('ModifyIndex')
                }
            else:
                logger.debug(f"KV key '{key}' not found")
                return None
        except Exception as e:
            logger.error(f"Error getting KV key '{key}': {e}", exc_info=True)
            raise
    
    def put_kv(self, key: str, value: str, datacenter: Optional[str] = None) -> bool:
        """Store key-value pair"""
        logger.info(f"Storing KV key '{key}' (value length: {len(value)})")
        logger.debug(f"KV value: {value[:100]}..." if len(value) > 100 else f"KV value: {value}")
        try:
            result = self.client.kv.put(key, value, dc=datacenter)
            logger.info(f"Successfully stored KV key '{key}'")
            return result
        except Exception as e:
            logger.error(f"Error storing KV key '{key}': {e}", exc_info=True)
            raise
    
    def list_kv(self, prefix: str = "", datacenter: Optional[str] = None) -> List[str]:
        """List keys"""
        logger.debug(f"Listing KV keys with prefix '{prefix}' (datacenter={datacenter})")
        try:
            index, keys = self.client.kv.get(prefix, keys=True, dc=datacenter)
            key_list = [k.decode('utf-8') if isinstance(k, bytes) else k for k in (keys or [])]
            logger.info(f"Found {len(key_list)} KV keys with prefix '{prefix}'")
            logger.debug(f"Keys: {key_list[:10]}..." if len(key_list) > 10 else f"Keys: {key_list}")
            return key_list
        except Exception as e:
            logger.error(f"Error listing KV keys: {e}", exc_info=True)
            raise
    
    def delete_kv(self, key: str, datacenter: Optional[str] = None) -> bool:
        """Delete key"""
        logger.info(f"Deleting KV key '{key}'")
        try:
            result = self.client.kv.delete(key, dc=datacenter)
            logger.info(f"Successfully deleted KV key '{key}'")
            return result
        except Exception as e:
            logger.error(f"Error deleting KV key '{key}': {e}", exc_info=True)
            raise
    
    def get_nodes(self, datacenter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get nodes"""
        logger.debug(f"Getting nodes (datacenter={datacenter})")
        try:
            index, nodes = self.client.catalog.nodes(dc=datacenter)
            logger.info(f"Found {len(nodes)} nodes")
            logger.debug(f"Nodes: {nodes}")
            return nodes
        except Exception as e:
            logger.error(f"Error getting nodes: {e}", exc_info=True)
            raise
    
    def get_service_health(self, service_name: str, datacenter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get service health checks"""
        logger.debug(f"Getting health checks for service '{service_name}' (datacenter={datacenter})")
        try:
            index, checks = self.client.health.service(service_name, dc=datacenter)
            logger.info(f"Found {len(checks)} health checks for service '{service_name}'")
            logger.debug(f"Health checks: {checks}")
            return checks
        except Exception as e:
            logger.error(f"Error getting health checks for service '{service_name}': {e}", exc_info=True)
            raise

    # ----------------------
    # Service instance Tags/Meta via Services API (Agent)
    # ----------------------
    def _get_agent_service(self, service_id: str) -> Dict[str, Any]:
        services = self.client.agent.services()
        if service_id not in services:
            raise ValueError(f"Service ID '{service_id}' not found on agent")
        return services[service_id]

    def get_service_instance_meta(self, service_id: str) -> Dict[str, Any]:
        svc = self._get_agent_service(service_id)
        meta = svc.get('Meta') or {}
        return dict(meta)

    def get_service_instance_tags(self, service_id: str) -> List[str]:
        svc = self._get_agent_service(service_id)
        tags = svc.get('Tags') or []
        return list(tags)

    def _register_service_definition(self, definition: Dict[str, Any]) -> None:
        """Re-register service with updated definition"""
        logger.debug(f"Re-registering service with definition: {definition}")
        try:
            # Build registration parameters
            register_kwargs = {
                'name': definition.get('Name'),
                'service_id': definition.get('ID'),
                'address': definition.get('Address', ''),
                'port': definition.get('Port', 0),
                'tags': definition.get('Tags', []),
                'enable_tag_override': definition.get('EnableTagOverride', False)
            }
            
            # Add Meta if present (python-consul may support this)
            meta = definition.get('Meta')
            if meta:
                register_kwargs['meta'] = meta
            
            # Add Check if present
            check = definition.get('Check')
            if check:
                register_kwargs['check'] = check
            
            # Register the service
            self.client.agent.service.register(**register_kwargs)
            logger.debug(f"Successfully re-registered service {definition.get('ID')}")
        except TypeError as e:
            # If meta parameter is not supported, try without it and use HTTP directly
            if 'meta' in str(e).lower() or 'unexpected keyword' in str(e).lower():
                logger.debug("Meta parameter not supported, using HTTP API directly")
                self._register_service_definition_via_http(definition)
            else:
                raise
        except Exception as e:
            logger.error(f"Error re-registering service: {e}", exc_info=True)
            raise
    
    def _register_service_definition_via_http(self, definition: Dict[str, Any]) -> None:
        """Fallback: Register service via HTTP API when meta parameter not supported"""
        import httpx
        consul_url = f"http://{self.config.host}:{self.config.port}"
        url = f"{consul_url}/v1/agent/service/register"
        
        headers = {'Content-Type': 'application/json'}
        if self.config.token:
            headers['X-Consul-Token'] = self.config.token
        
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.put(url, json=definition, headers=headers)
                if resp.status_code not in (200, 201):
                    raise RuntimeError(f"Failed to register service via HTTP: {resp.status_code} - {resp.text}")
                logger.debug(f"Successfully registered service {definition.get('ID')} via HTTP API")
        except Exception as e:
            logger.error(f"HTTP API registration failed: {e}", exc_info=True)
            raise

    def _build_registration_from_agent(self, svc: Dict[str, Any], new_meta: Optional[Dict[str, str]] = None, new_tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Build service registration definition from agent service info"""
        # Map agent service fields to registration payload
        reg: Dict[str, Any] = {
            'ID': svc.get('ID'),
            'Name': svc.get('Service') or svc.get('ServiceName') or svc.get('ID'),
            'Address': svc.get('Address') or '',
            'Port': int(svc.get('Port') or 0),
            'EnableTagOverride': bool(svc.get('EnableTagOverride', False)),
        }
        
        # Merge tags
        existing_tags = svc.get('Tags') or []
        if new_tags is not None:
            reg['Tags'] = new_tags
        elif existing_tags:
            reg['Tags'] = existing_tags
        
        # Merge meta
        existing_meta = svc.get('Meta') or {}
        if new_meta is not None:
            merged = dict(existing_meta)
            merged.update(new_meta)
            reg['Meta'] = merged
        elif existing_meta:
            reg['Meta'] = existing_meta
        
        # Preserve Check if it exists (health check configuration)
        # Note: Check info might be in different format, we try to preserve it
        if 'Check' in svc:
            reg['Check'] = svc['Check']
        elif 'Checks' in svc and svc['Checks']:
            # If multiple checks, use the first one or combine them
            checks = svc['Checks']
            if isinstance(checks, list) and len(checks) > 0:
                reg['Check'] = checks[0]
        
        return reg

    def set_service_instance_meta(self, service_id: str, meta_patch: Dict[str, str]) -> Dict[str, Any]:
        """Merge-and-update Meta on a registered service instance."""
        svc = self._get_agent_service(service_id)
        reg = self._build_registration_from_agent(svc, new_meta=meta_patch)
        logger.info(f"Updating Meta for service_id={service_id}: keys={list(meta_patch.keys())}")
        self._register_service_definition(reg)
        return self.get_service_instance_meta(service_id)

    def replace_service_instance_meta(self, service_id: str, meta_new: Dict[str, str]) -> Dict[str, Any]:
        """Replace Meta entirely for a service instance."""
        svc = self._get_agent_service(service_id)
        reg = self._build_registration_from_agent(svc, new_meta=meta_new)
        logger.info(f"Replacing Meta for service_id={service_id} with {len(meta_new)} keys")
        self._register_service_definition(reg)
        return self.get_service_instance_meta(service_id)

    def delete_service_instance_meta_keys(self, service_id: str, keys: List[str]) -> Dict[str, Any]:
        """Delete specific Meta keys for a service instance (by re-registering without those keys)."""
        svc = self._get_agent_service(service_id)
        current_meta = dict(svc.get('Meta') or {})
        for k in keys:
            current_meta.pop(k, None)
        reg = self._build_registration_from_agent(svc, new_meta=current_meta)
        logger.info(f"Deleting Meta keys for service_id={service_id}: {keys}")
        self._register_service_definition(reg)
        return self.get_service_instance_meta(service_id)

    def set_service_instance_tags(self, service_id: str, tags: List[str]) -> List[str]:
        """Overwrite Tags for a service instance."""
        svc = self._get_agent_service(service_id)
        reg = self._build_registration_from_agent(svc, new_tags=tags)
        logger.info(f"Updating Tags for service_id={service_id}: {tags}")
        self._register_service_definition(reg)
        return self.get_service_instance_tags(service_id)

