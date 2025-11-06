#!/usr/bin/env python3
"""
Consul MCP Server
A Model Context Protocol server for interacting with HashiCorp Consul
using Server-Sent Events (SSE) transport.
"""

# Setup logging FIRST before importing other modules
from logging_config import setup_logging, get_logger
logger = setup_logging()

import uvicorn
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import Response
from starlette.routing import Route, Mount
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse

from mcp.server import Server

# Import modules
from config import AppConfig
from consul_client import ConsulClient
from mcp_tools import get_tool_definitions, ToolHandler
from mcp_resources import get_resource_definitions, ResourceHandler
from mcp_prompts import get_prompt_definitions, PromptHandler
from sse_handler import (
    SSE_TRANSPORT_AVAILABLE,
    create_sse_transport,
    create_sse_endpoint_handler
)

# Load configuration
config = AppConfig.from_env()
logger.info("=" * 60)
logger.info("Consul MCP Server Starting")
logger.info("=" * 60)
logger.info(f"Configuration loaded:")
logger.info(f"  - Consul: {config.consul}")
logger.info(f"  - Server: {config.server}")
logger.info(f"  - Logging: Level={config.logging.level}")

# Initialize Consul client
try:
    consul_client = ConsulClient(config.consul)
    logger.info("Consul client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Consul client: {e}", exc_info=True)
    consul_client = None

# Create MCP server
mcp_server = Server("consul-mcp-server")
logger.info("MCP server instance created")

# Initialize handlers
tool_handler = ToolHandler(consul_client) if consul_client else None
resource_handler = ResourceHandler(consul_client) if consul_client else None
prompt_handler = PromptHandler(consul_client) if consul_client else None

# Create SSE transport if available
sse_transport = None
if SSE_TRANSPORT_AVAILABLE:
    sse_transport = create_sse_transport(config.server.messages_endpoint)
    if sse_transport:
        logger.info("SSE transport created successfully")
    else:
        logger.warning("SSE transport creation failed")
else:
    logger.warning("SSE transport not available - server will run in limited mode")

# Create FastAPI app
app = FastAPI(
    title="Consul MCP Server",
    description="Model Context Protocol server for HashiCorp Consul",
    version="1.0.0"
)
logger.info("FastAPI application created")

# Register SSE endpoint
if sse_transport:
    sse_asgi_app = create_sse_endpoint_handler(sse_transport, mcp_server)
    
    # Create a wrapper function that FastAPI can use
    async def sse_endpoint_wrapper(request: Request):
        """Wrapper to handle SSE endpoint as FastAPI route"""
        # Track if response was sent by ASGI handler (local to this function)
        response_sent = False
        
        # Create a wrapper for send that tracks if response was sent
        async def wrapped_send(message):
            nonlocal response_sent
            if message.get("type") == "http.response.start":
                response_sent = True
            await request._send(message)
        
        # Convert FastAPI Request to ASGI scope/receive/send
        # The ASGI app will handle the response directly via send
        await sse_asgi_app(
            request.scope,
            request.receive,
            wrapped_send
        )
        
        # If response was already sent by ASGI handler, we need to return
        # a response that FastAPI won't try to send again.
        # Since the response was already sent via ASGI send(), we return
        # an empty response that won't be sent (but FastAPI requires a return value)
        if response_sent:
            # Return a response that indicates it was already sent
            # We'll use a custom response class that won't actually send
            class AlreadySentResponse(Response):
                async def __call__(self, scope, receive, send):
                    # Don't send anything, response was already sent
                    pass
            return AlreadySentResponse(status_code=200)
        
        # Fallback response (shouldn't happen normally)
        return Response(status_code=200, content="")
    
    # Register as FastAPI route
    app.add_api_route(
        config.server.sse_endpoint,
        sse_endpoint_wrapper,
        methods=["GET", "HEAD"],
        name="sse"
    )
    logger.info(f"SSE endpoint registered: {config.server.sse_endpoint} (GET, HEAD)")
else:
    logger.warning("SSE endpoint not registered - transport unavailable")


@app.get("/health")
@app.head("/health")
async def health_check():
    """Health check endpoint"""
    logger.debug("Health check requested")
    try:
        if consul_client and consul_client.is_connected():
            status = {"status": "healthy", "consul": "connected"}
            logger.debug("Health check: healthy")
            return status
        else:
            status = {"status": "unhealthy", "consul": "not_connected"}
            logger.warning("Health check: unhealthy - Consul not connected")
            return status
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return {"status": "unhealthy", "error": str(e)}


@app.post("/messages")
async def messages_endpoint(request: Request):
    """POST endpoint for sending messages to MCP server"""
    client_info = {
        "client": request.client.host if request.client else "unknown",
        "method": request.method,
        "path": request.url.path
    }
    logger.info(f"POST /messages request from {client_info['client']}")
    logger.debug(f"Request details: {client_info}")
    
    if not SSE_TRANSPORT_AVAILABLE or not sse_transport:
        logger.error("POST /messages: SSE transport not available")
        return Response(
            content="SSE transport not available. Please check MCP SDK installation.",
            status_code=500
        )
    
    # Track if response was already sent by ASGI handler
    response_sent = False
    
    # Create a wrapper for send that tracks if response was sent
    async def wrapped_send(message):
        nonlocal response_sent
        if message.get("type") == "http.response.start":
            response_sent = True
        await request._send(message)
    
    try:
        logger.debug("Processing POST message through SSE transport")
        # Convert FastAPI Request to ASGI call
        # handle_post_message needs scope, receive, send
        # It will handle the response directly via ASGI send
        await sse_transport.handle_post_message(
            request.scope,
            request.receive,
            wrapped_send
        )
        # The ASGI handler sends the response directly via send()
        logger.info(f"POST /messages: Message processed successfully")
        
        # If response was already sent by ASGI handler, return a response
        # that won't be sent again
        if response_sent:
            class AlreadySentResponse(Response):
                async def __call__(self, scope, receive, send):
                    # Don't send anything, response was already sent
                    pass
            return AlreadySentResponse(status_code=200)
        
        # Fallback: return a response if handler didn't send one
        return Response(status_code=200, content="")
    except Exception as e:
        logger.error(f"POST /messages: Error handling message: {e}", exc_info=True)
        logger.error(f"POST /messages traceback: {traceback.format_exc()}")
        
        # Only return error response if ASGI handler didn't send one
        if not response_sent:
            return Response(
                content=f"Error handling message: {str(e)}",
                status_code=500
            )
        # Response already sent, return a no-op response
        class AlreadySentResponse(Response):
            async def __call__(self, scope, receive, send):
                pass
        return AlreadySentResponse(status_code=500)


# Register MCP tools
@mcp_server.list_tools()
async def handle_list_tools():
    """List available Consul tools"""
    logger.debug("MCP: list_tools called")
    tools = get_tool_definitions()
    logger.info(f"MCP: Returning {len(tools)} tools")
    return tools


@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    """Handle tool calls"""
    logger.info(f"MCP: Tool call received - {name}")
    logger.debug(f"MCP: Tool '{name}' arguments: {arguments}")
    
    if not tool_handler:
        logger.error("Tool handler not available - Consul client not initialized")
        from mcp.types import TextContent
        import json
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": "Consul client not initialized"
            }, indent=2)
        )]
    
    result = await tool_handler.handle_tool_call(name, arguments)
    logger.info(f"MCP: Tool '{name}' completed successfully")
    return result


# Register MCP resources
@mcp_server.list_resources()
async def handle_list_resources():
    """List available Consul resources"""
    logger.debug("MCP: list_resources called")
    resources = get_resource_definitions()
    logger.info(f"MCP: Returning {len(resources)} resources")
    return resources


@mcp_server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a Consul resource"""
    logger.info(f"MCP: Reading resource: {uri}")
    
    if not resource_handler:
        logger.error("Resource handler not available - Consul client not initialized")
        raise RuntimeError("Consul client not initialized")
    
    result = await resource_handler.read_resource(uri)
    logger.info(f"MCP: Resource '{uri}' read successfully")
    return result


# Register MCP prompts
@mcp_server.list_prompts()
async def handle_list_prompts():
    """List available prompts"""
    logger.debug("MCP: list_prompts called")
    prompts = get_prompt_definitions()
    logger.info(f"MCP: Returning {len(prompts)} prompts")
    return prompts


@mcp_server.get_prompt()
async def handle_get_prompt(name: str, arguments: dict):
    """Get a prompt"""
    logger.info(f"MCP: Get prompt requested - {name}")
    logger.debug(f"MCP: Prompt '{name}' arguments: {arguments}")
    
    if not prompt_handler:
        logger.error("Prompt handler not available - Consul client not initialized")
        from mcp.types import GetPromptResult, TextContent
        return GetPromptResult(
            description="Error",
            messages=[
                TextContent(
                    type="text",
                    text="Consul client not initialized"
                )
            ]
        )
    
    result = await prompt_handler.get_prompt(name, arguments)
    logger.info(f"MCP: Prompt '{name}' generated successfully")
    return result


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info(f"Starting Consul MCP Server on {config.server.host}:{config.server.port}")
    logger.info(f"SSE endpoint: http://{config.server.host}:{config.server.port}{config.server.sse_endpoint}")
    logger.info(f"Messages endpoint: http://{config.server.host}:{config.server.port}{config.server.messages_endpoint}")
    logger.info(f"Health endpoint: http://{config.server.host}:{config.server.port}{config.server.health_endpoint}")
    logger.info("=" * 60)
    
    uvicorn.run(
        app,
        host=config.server.host,
        port=config.server.port,
        log_config=None  # We're using our own logging
    )
