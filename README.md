# mcp-prtg

MCP Server for PRTG Network Monitor (read-only).

Allows Claude to query sensors, devices, groups, channels, historical data, and system status from your PRTG instance via the **classic PRTG HTTP API** (v1). Supports self-signed SSL certificates.

> **Note:** This server uses the classic PRTG API (`/api/table.json`, `/api/historicdata.json`, etc.), which is available in all PRTG versions. PRTG also offers a newer REST API v2 (available since v21.4.73 on port 1616) that is not yet supported by this server.

## Authentication

This server authenticates using **username + passhash**. API tokens and plaintext passwords are not supported.

### Getting your passhash

Open this URL in your browser (replace with your PRTG server, user, and password):

```
https://prtg.example.com/api/getpasshash.htm?username=myuser&password=mypassword
```

## HTTP Transport with Bearer Auth

The server can run over MCP Streamable HTTP at `/mcp` and requires a static
Bearer token when HTTP mode is enabled.

Required HTTP variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `MCP_TRANSPORT` | Yes | Use `streamable-http` or `http` for HTTP mode. Use `stdio` for local stdio mode. |
| `MCP_BEARER_TOKEN` | Yes for HTTP | Bearer token expected in the `Authorization` header. Use a long random value. |
| `MCP_HOST` | No | Bind address. Defaults to `0.0.0.0` in Docker. |
| `MCP_PORT` | No | Listen port. Defaults to `8000`. |
| `MCP_PATH` | No | MCP endpoint path. Defaults to `/mcp`. |
| `MCP_STATELESS_HTTP` | No | Use stateless Streamable HTTP sessions. Defaults to `true`. |
| `MCP_PUBLIC_URL` | No | Public base URL used in MCP auth metadata. Defaults to `http://localhost:8000`. |
| `MCP_AUTH_ISSUER_URL` | No | Issuer URL reported in auth metadata. Defaults to `MCP_PUBLIC_URL`. |
| `MCP_AUTH_SCOPES` | No | Comma-separated scopes. Defaults to `prtg:read`. |

HTTP endpoint:

```
http://localhost:8000/mcp
```

Clients must send:

```
Authorization: Bearer <MCP_BEARER_TOKEN>
```

The container also exposes an unauthenticated health check:

```
GET http://localhost:8000/health
```

## Docker

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` with your PRTG credentials and a strong `MCP_BEARER_TOKEN`, then run:

```bash
docker compose up --build
```

Or build and run manually:

```bash
docker build -t mcp-prtg .
docker run --rm -p 8000:8000 \
  -e MCP_BEARER_TOKEN="replace-with-a-long-random-token" \
  -e PRTG_URL="https://prtg.example.com" \
  -e PRTG_USERNAME="apiuser" \
  -e PRTG_PASSHASH="1234567890" \
  mcp-prtg
```

## Configuration in Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "prtg": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-prtg", "run", "server.py"],
      "env": {
        "PRTG_URL": "https://prtg.example.com",
        "PRTG_USERNAME": "apiuser",
        "PRTG_PASSHASH": "1234567890"
      }
    }
  }
}
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PRTG_URL` | Yes | URL of your PRTG server (e.g., `https://prtg.example.com`) |
| `PRTG_USERNAME` | Yes | PRTG username for authentication |
| `PRTG_PASSHASH` | Yes | Passhash for the PRTG user |

## Available Tools

| Tool | Description |
|------|-------------|
| `get_sensors` | List sensors with filters (status, tags, parent ID, text) |
| `get_sensor_details` | Full details for a specific sensor |
| `get_channels` | List channels for a sensor |
| `get_devices` | List devices with filters |
| `get_groups` | List groups (used to organize devices) |
| `get_sensor_history` | Historic monitoring data for a sensor |
| `get_server_status` | Overall PRTG server health and sensor counts |
| `get_messages` | System log messages with optional date range filter |
| `search` | Search objects by name across sensors, devices, or groups |

## Development

```bash
# Install dependencies
uv sync

# Run the server locally
PRTG_URL=https://prtg.local PRTG_USERNAME=admin PRTG_PASSHASH=12345 uv run server.py

# Run locally over HTTP
MCP_TRANSPORT=streamable-http MCP_BEARER_TOKEN=secret \
  PRTG_URL=https://prtg.local PRTG_USERNAME=admin PRTG_PASSHASH=12345 \
  uv run server.py

# Test with MCP Inspector
npx @modelcontextprotocol/inspector uv run server.py
```

## License

MIT
