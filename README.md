# Consul MCP Server

A Model Context Protocol (MCP) server for interacting with HashiCorp Consul. This server enables AI assistants and other MCP clients to manage Consul services, key-value stores, and cluster information through a standardized protocol interface.

## Features

- **MCP Protocol Support**: Full implementation of Model Context Protocol with SSE (Server-Sent Events) transport
- **Service Management**: Register, deregister, and query Consul services
- **Key-Value Store**: Read, write, list, and delete operations on Consul KV store
- **Cluster Information**: Query nodes and service health status
- **Service Metadata & Tags**: Manage service instance metadata and tags
- **Docker Support**: Easy deployment with Docker Compose
- **Health Checks**: Built-in health check endpoint for monitoring

## Requirements

- Python 3.11+
- HashiCorp Consul (local or remote instance)
- Docker & Docker Compose (optional, for containerized deployment)

## Installation

### Using Docker Compose (Recommended)

The easiest way to get started is using Docker Compose, which will start both Consul and the MCP server:

```bash
docker-compose up -d
```

This will:
- Start a Consul instance in dev mode on port 8500
- Start the Consul MCP Server on port 8080
- Configure networking between the containers

### Manual Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd consul-mcp
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables (optional):
```bash
export CONSUL_HOST=localhost
export CONSUL_PORT=8500
export CONSUL_TOKEN=your-token  # Optional
export CONSUL_DC=dc1  # Optional
export PORT=8080
export HOST=0.0.0.0
export LOG_LEVEL=INFO
```

4. Run the server:
```bash
python server.py
```

## Configuration

The server can be configured using environment variables:

### Consul Configuration

- `CONSUL_HOST`: Consul host address (default: `localhost`)
- `CONSUL_PORT`: Consul port (default: `8500`)
- `CONSUL_TOKEN`: Consul ACL token (optional)
- `CONSUL_DC`: Consul datacenter (optional)

### Server Configuration

- `HOST`: Server bind address (default: `0.0.0.0`)
- `PORT`: Server port (default: `8080`)
- `SSE_ENDPOINT`: SSE endpoint path (default: `/sse`)
- `MESSAGES_ENDPOINT`: Messages endpoint path (default: `/messages`)
- `HEALTH_ENDPOINT`: Health check endpoint path (default: `/health`)

### Logging Configuration

- `LOG_LEVEL`: Logging level (default: `INFO`)
- `LOG_FILE_ENABLE`: Enable file logging (default: `false`)
- `LOG_FILE`: Log file path (optional)

## API Endpoints

### Health Check

```bash
GET /health
```

Returns the health status of the server and Consul connection.

**Response:**
```json
{
  "status": "healthy",
  "consul": "connected"
}
```

### SSE Endpoint

```
GET /sse
```

Server-Sent Events endpoint for MCP protocol communication.

### Messages Endpoint

```
POST /messages
```

Endpoint for sending messages to the MCP server.

## MCP Tools

The server provides the following MCP tools for Consul operations:

### Service Management

- **`list_services`**: List all services registered in Consul
- **`get_service`**: Get detailed information about a specific service
- **`register_service`**: Register a new service in Consul
- **`deregister_service`**: Deregister a service from Consul
- **`get_service_health`**: Get health status of a service

### Service Metadata & Tags

- **`get_service_meta`**: Get all metadata for a service instance
- **`set_service_meta_key`**: Set or update one metadata key for a service instance
- **`set_service_meta_bulk`**: Set or update multiple metadata keys for a service instance
- **`delete_service_meta_key`**: Delete one metadata key for a service instance
- **`list_service_meta_keys`**: List all metadata keys for a service instance
- **`get_service_tags`**: Get tags for a service instance
- **`set_service_tags`**: Overwrite tags for a service instance

### Key-Value Store

- **`get_kv`**: Get a key-value pair from Consul KV store
- **`put_kv`**: Store a key-value pair in Consul KV store
- **`list_kv`**: List all keys in Consul KV store (optionally with prefix)
- **`delete_kv`**: Delete a key from Consul KV store

### Cluster Information

- **`get_nodes`**: Get list of nodes in Consul cluster

## MCP Resources

The server provides MCP resources for accessing Consul data. See `mcp_resources.py` for available resources.

## MCP Prompts

The server provides MCP prompts for common Consul operations. See `mcp_prompts.py` for available prompts.

## Usage Examples

### Using with MCP Client

Connect to the server using an MCP-compatible client:

```python
# Example MCP client connection
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client

# Connect via SSE
async with sse_client("http://localhost:8080/sse") as (read, write):
    async with ClientSession(read, write) as session:
        # List available tools
        tools = await session.list_tools()
        print(f"Available tools: {[t.name for t in tools.tools]}")
        
        # Call a tool
        result = await session.call_tool("list_services", {})
        print(result)
```

### Direct HTTP Usage

You can also interact with the server directly via HTTP:

```bash
# Health check
curl http://localhost:8080/health

# List services (via MCP protocol)
curl -X POST http://localhost:8080/messages \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'
```

## Development

### Project Structure

```
consul-mcp/
├── server.py              # Main server application
├── config.py              # Configuration management
├── consul_client.py       # Consul client wrapper
├── mcp_tools.py           # MCP tools definitions
├── mcp_resources.py       # MCP resources definitions
├── mcp_prompts.py         # MCP prompts definitions
├── sse_handler.py         # SSE transport handler
├── logging_config.py      # Logging configuration
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker image definition
└── docker-compose.yml    # Docker Compose configuration
```

### Running Tests

```bash
# Run health check
curl http://localhost:8080/health
```

### Building Docker Image

```bash
docker build -t consul-mcp-server .
```

## Troubleshooting

### Connection Issues

If the server cannot connect to Consul:

1. Verify Consul is running:
```bash
curl http://localhost:8500/v1/status/leader
```

2. Check environment variables:
```bash
echo $CONSUL_HOST
echo $CONSUL_PORT
```

3. Check server logs for connection errors

### SSE Transport Issues

If SSE transport is not available:

- Ensure `mcp` package version >= 1.0.0 is installed
- Check that `sse-starlette` is installed
- Review server logs for transport initialization errors

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Acknowledgments

- Built with [Model Context Protocol](https://modelcontextprotocol.io/)
- Uses [python-consul](https://github.com/cablehead/python-consul) for Consul integration
- Powered by [FastAPI](https://fastapi.tiangolo.com/) and [Uvicorn](https://www.uvicorn.org/)
