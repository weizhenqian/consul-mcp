#!/usr/bin/env python3
"""
SSE (Server-Sent Events) transport handler for MCP Server
"""

import logging
import traceback
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import SSE transport - different versions may have different APIs
SSE_TRANSPORT_AVAILABLE = False
SseServerTransport = None
SSE_TRANSPORT_TYPE = None

try:
    from mcp.server.sse import SseServerTransport
    SSE_TRANSPORT_AVAILABLE = True
    SSE_TRANSPORT_TYPE = "mcp.server.sse"
    logger.info("SSE transport loaded: mcp.server.sse.SseServerTransport")
except ImportError:
    try:
        from mcp.transport.sse import SseServerTransport
        SSE_TRANSPORT_AVAILABLE = True
        SSE_TRANSPORT_TYPE = "mcp.transport.sse"
        logger.info("SSE transport loaded: mcp.transport.sse.SseServerTransport")
    except ImportError:
        logger.warning("SSE transport not available - MCP SDK may not support SSE")
        SSE_TRANSPORT_AVAILABLE = False


def create_sse_transport(messages_endpoint: str = "/messages") -> Optional[object]:
    """
    Create SSE transport instance
    
    Args:
        messages_endpoint: Messages endpoint path
    
    Returns:
        SseServerTransport instance or None
    """
    if not SSE_TRANSPORT_AVAILABLE:
        logger.error("Cannot create SSE transport - transport not available")
        return None
    
    try:
        transport = SseServerTransport(messages_endpoint)
        logger.info(f"SSE transport created with messages endpoint: {messages_endpoint}")
        return transport
    except Exception as e:
        logger.error(f"Failed to create SSE transport: {e}", exc_info=True)
        return None


async def create_sse_asgi_app(transport, mcp_server, scope, receive, send):
    """
    Create ASGI application for SSE endpoint
    
    Args:
        transport: SSE transport instance
        mcp_server: MCP server instance
        scope: ASGI scope
        receive: ASGI receive function
        send: ASGI send function
    """
    client_info = {}
    try:
        if scope.get("type") == "http":
            client_info = {
                "method": scope.get("method", "UNKNOWN"),
                "path": scope.get("path", "UNKNOWN"),
                "client": scope.get("client"),
                "headers": dict(scope.get("headers", []))
            }
            logger.info(f"SSE connection request: {client_info['method']} {client_info['path']}")
            logger.debug(f"Client info: {client_info}")
    except Exception as e:
        logger.warning(f"Could not extract client info: {e}")
    
    if scope["type"] != "http":
        logger.warning(f"Invalid request type: {scope.get('type')}")
        await send({
            "type": "http.response.start",
            "status": 400,
            "headers": [[b"content-type", b"text/plain"]],
        })
        await send({
            "type": "http.response.body",
            "body": b"Invalid request type",
        })
        return
    
    method = scope.get("method", "UNKNOWN")
    if method not in ["GET", "HEAD"]:
        logger.warning(f"Invalid request method: {method}")
        await send({
            "type": "http.response.start",
            "status": 405,
            "headers": [
                [b"content-type", b"text/plain"],
                [b"allow", b"GET, HEAD"]
            ],
        })
        await send({
            "type": "http.response.body",
            "body": b"Method not allowed. Use GET for SSE connection.",
        })
        return
    
    # For HEAD requests, just return headers without establishing connection
    if method == "HEAD":
        logger.info(f"HEAD request for SSE endpoint")
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [
                [b"content-type", b"text/event-stream"],
                [b"cache-control", b"no-cache"],
                [b"connection", b"keep-alive"],
            ],
        })
        await send({
            "type": "http.response.body",
            "body": b"",
        })
        return
    
    if not transport:
        logger.error("SSE transport not available")
        await send({
            "type": "http.response.start",
            "status": 500,
            "headers": [[b"content-type", b"text/plain"]],
        })
        await send({
            "type": "http.response.body",
            "body": b"SSE transport not available",
        })
        return
    
    try:
        client_addr = client_info.get('client', 'unknown')
        if isinstance(client_addr, tuple):
            client_addr = f"{client_addr[0]}:{client_addr[1]}"
        
        logger.info(f"Establishing SSE connection for client: {client_addr}")
        logger.debug(f"Scope details: type={scope.get('type')}, method={scope.get('method')}, path={scope.get('path')}")
        logger.debug(f"Starting SSE transport connection...")
        
        # Log headers for debugging
        headers_dict = client_info.get('headers', {})
        if headers_dict:
            logger.debug(f"Request headers: {list(headers_dict.keys())}")
        
        logger.debug(f"Calling transport.connect_sse()...")
        try:
            async with transport.connect_sse(scope, receive, send) as (read_stream, write_stream):
                logger.info(f"SSE connection established successfully for client: {client_addr}")
                logger.debug(f"SSE streams ready, running MCP server...")
                
                try:
                    init_options = mcp_server.create_initialization_options()
                    logger.debug(f"MCP server initialization options created")
                    await mcp_server.run(
                        read_stream,
                        write_stream,
                        init_options
                    )
                    logger.info(f"SSE connection closed normally for client: {client_addr}")
                except Exception as run_error:
                    logger.error(f"MCP server run error for client {client_addr}: {run_error}", exc_info=True)
                    logger.error(f"MCP server run traceback: {traceback.format_exc()}")
                    raise
        except Exception as connect_error:
            logger.error(f"Error establishing SSE connection for client {client_addr}: {connect_error}", exc_info=True)
            logger.error(f"SSE connection error traceback: {traceback.format_exc()}")
            raise
    
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"Error in SSE connection handler: {error_type}: {error_msg}", exc_info=True)
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Try to send error response, but don't fail if we can't
        try:
            await send({
                "type": "http.response.start",
                "status": 500,
                "headers": [
                    [b"content-type", b"text/plain; charset=utf-8"],
                    [b"x-error-type", error_type.encode()],
                ],
            })
            await send({
                "type": "http.response.body",
                "body": f"SSE connection error: {error_msg}".encode('utf-8'),
            })
        except Exception as send_error:
            logger.error(f"Failed to send error response: {send_error}", exc_info=True)


def create_sse_endpoint_handler(transport, mcp_server):
    """
    Create SSE endpoint handler function
    
    Args:
        transport: SSE transport instance
        mcp_server: MCP server instance
    
    Returns:
        ASGI application function
    """
    async def sse_endpoint(scope, receive, send):
        """SSE endpoint ASGI application"""
        await create_sse_asgi_app(transport, mcp_server, scope, receive, send)
    
    return sse_endpoint

