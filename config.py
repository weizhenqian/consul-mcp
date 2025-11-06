#!/usr/bin/env python3
"""
Configuration management for Consul MCP Server
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class ConsulConfig:
    """Consul connection configuration"""
    host: str
    port: int
    token: Optional[str] = None
    dc: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'ConsulConfig':
        """Create configuration from environment variables"""
        return cls(
            host=os.getenv("CONSUL_HOST", "localhost"),
            port=int(os.getenv("CONSUL_PORT", "8500")),
            token=os.getenv("CONSUL_TOKEN", None),
            dc=os.getenv("CONSUL_DC", None)
        )
    
    def __str__(self) -> str:
        token_str = "***" if self.token else "None"
        return f"ConsulConfig(host={self.host}, port={self.port}, token={token_str}, dc={self.dc})"


@dataclass
class ServerConfig:
    """Server configuration"""
    host: str
    port: int
    sse_endpoint: str = "/sse"
    messages_endpoint: str = "/messages"
    health_endpoint: str = "/health"
    
    @classmethod
    def from_env(cls) -> 'ServerConfig':
        """Create configuration from environment variables"""
        return cls(
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8080")),
            sse_endpoint=os.getenv("SSE_ENDPOINT", "/sse"),
            messages_endpoint=os.getenv("MESSAGES_ENDPOINT", "/messages"),
            health_endpoint=os.getenv("HEALTH_ENDPOINT", "/health")
        )
    
    def __str__(self) -> str:
        return f"ServerConfig(host={self.host}, port={self.port}, endpoints=[{self.sse_endpoint}, {self.messages_endpoint}, {self.health_endpoint}])"


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str
    enable_file: bool = False
    log_file: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        """Create configuration from environment variables"""
        return cls(
            level=os.getenv("LOG_LEVEL", "INFO"),
            enable_file=os.getenv("LOG_FILE_ENABLE", "false").lower() == "true",
            log_file=os.getenv("LOG_FILE", None)
        )


@dataclass
class AppConfig:
    """Application configuration"""
    consul: ConsulConfig
    server: ServerConfig
    logging: LoggingConfig
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Create application configuration from environment variables"""
        return cls(
            consul=ConsulConfig.from_env(),
            server=ServerConfig.from_env(),
            logging=LoggingConfig.from_env()
        )

