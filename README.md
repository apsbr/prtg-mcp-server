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

# Test with MCP Inspector
npx @modelcontextprotocol/inspector uv run server.py
```

## License

MIT
