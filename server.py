"""MCP server for PRTG Network Monitor — read-only."""

import json
import os
import ssl
from typing import Any, Optional

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("prtg")

PRTG_URL = os.environ.get("PRTG_URL", "https://localhost")
PRTG_USERNAME = os.environ.get("PRTG_USERNAME")
PRTG_PASSHASH = os.environ.get("PRTG_PASSHASH")

# Build auth params
_AUTH: dict[str, str] = {}
if PRTG_USERNAME and PRTG_PASSHASH:
    _AUTH["username"] = PRTG_USERNAME
    _AUTH["passhash"] = PRTG_PASSHASH

# SSL context that accepts self-signed certs
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

STATUS_MAP = {
    "up": [3], "down": [5], "warning": [4],
    "paused": [7, 8, 9, 12], "unknown": [1], "unusual": [10],
    "down_acknowledged": [13], "down_partial": [14],
}


async def _request(endpoint: str, params: Optional[dict] = None) -> Any:
    merged = {**(params or {}), **_AUTH}
    merged = {k: v for k, v in merged.items() if v is not None}
    url = f"{PRTG_URL.rstrip('/')}{endpoint}"
    async with httpx.AsyncClient(verify=_SSL_CTX, timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(url, params=merged)
        resp.raise_for_status()
        ct = resp.headers.get("content-type", "")
        if "json" in ct or endpoint.endswith(".json"):
            return resp.json()
        return resp.text


async def _table(content: str, columns: str, **kwargs: Any) -> dict:
    params: dict[str, Any] = {
        "content": content, "columns": columns,
        "count": kwargs.pop("count", 500),
    }
    for key in ("id", "start", "sortby", "filter_tags", "filter_name", "filter_drel", "noraw"):
        if key in kwargs and kwargs[key] is not None:
            params[key] = kwargs[key]
    statuses = kwargs.get("filter_status")
    if statuses:
        for i, s in enumerate(statuses):
            params[f"filter_status[{i}]"] = s
    return await _request("/api/table.json", params)


def _json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


# --- Tools ---

@mcp.tool()
async def get_sensors(
    id: Optional[int] = None, status: Optional[str] = None,
    tags: Optional[str] = None, text_filter: Optional[str] = None,
    count: int = 500,
) -> str:
    """List PRTG sensors with optional filters.

    Args:
        id: Parent object ID (device or group) to filter sensors under.
        status: Filter by status: up, down, warning, paused, unknown, unusual, down_acknowledged, down_partial.
        tags: Filter by tag, e.g. @tag(mytag).
        text_filter: Filter sensors whose name contains this text.
        count: Max results (default 500).
    """
    return _json(await _table(
        "sensors",
        "objid,name,status,message,lastvalue,device,group,probe,priority,tags,type,active,downtimesince,lastcheck,parentid",
        id=id, count=count,
        filter_status=STATUS_MAP.get(status) if status else None,
        filter_tags=tags,
        filter_name=f"@sub({text_filter})" if text_filter else None,
    ))


@mcp.tool()
async def get_sensor_details(id: int) -> str:
    """Get full details for a specific sensor.

    Args:
        id: The sensor object ID.
    """
    return _json(await _request("/api/getsensordetails.json", {"id": id}))


@mcp.tool()
async def get_channels(id: int) -> str:
    """List all channels for a specific sensor.

    Args:
        id: The sensor object ID.
    """
    return _json(await _table("channels", "objid,name,lastvalue,minimum,maximum", id=id, noraw=1))


@mcp.tool()
async def get_devices(
    id: Optional[int] = None, text_filter: Optional[str] = None, count: int = 500,
) -> str:
    """List PRTG devices with optional filters.

    Args:
        id: Parent group ID to list devices under.
        text_filter: Filter devices whose name contains this text.
        count: Max results (default 500).
    """
    return _json(await _table(
        "devices",
        "objid,name,status,host,group,probe,upsens,downsens,warnsens,pausedsens,totalsens,location,tags,active",
        id=id, count=count,
        filter_name=f"@sub({text_filter})" if text_filter else None,
    ))


@mcp.tool()
async def get_groups(id: Optional[int] = None, count: int = 500) -> str:
    """List PRTG groups (used to organize devices).

    Args:
        id: Parent group ID to list sub-groups under.
        count: Max results (default 500).
    """
    return _json(await _table(
        "groups",
        "objid,name,status,probe,upsens,downsens,warnsens,pausedsens,totalsens,active",
        id=id, count=count,
    ))


@mcp.tool()
async def get_sensor_history(
    id: int, sdate: str, edate: str, avg: int = 0, count: int = 500,
) -> str:
    """Get historic monitoring data for a sensor.

    Args:
        id: The sensor object ID.
        sdate: Start date/time as YYYY-MM-DD-HH-MM-SS.
        edate: End date/time as YYYY-MM-DD-HH-MM-SS.
        avg: Averaging interval in seconds. 0=raw, 300=5min, 3600=1h, 86400=1day.
        count: Max data points (default 500).
    """
    return _json(await _request("/api/historicdata.json", {
        "id": id, "sdate": sdate, "edate": edate,
        "avg": avg, "count": count, "sortby": "-datetime",
    }))


@mcp.tool()
async def get_server_status() -> str:
    """Get overall PRTG server health and sensor counts."""
    try:
        return _json(await _request("/api/getstatus.htm", {"id": 0}))
    except Exception:
        data = await _table("sensors", "objid,status", count=50000)
        sensors = data.get("sensors", [])
        summary = {
            "total": len(sensors),
            "up": sum(1 for s in sensors if s.get("status_raw") == 3),
            "down": sum(1 for s in sensors if s.get("status_raw") == 5),
            "warning": sum(1 for s in sensors if s.get("status_raw") == 4),
            "paused": sum(1 for s in sensors if s.get("status_raw") in (7, 8, 9, 12)),
            "unusual": sum(1 for s in sensors if s.get("status_raw") == 10),
        }
        return _json({"sensor_summary": summary})


@mcp.tool()
async def get_messages(
    id: Optional[int] = None, count: int = 100, date_range: Optional[str] = None,
) -> str:
    """Get PRTG system log messages.

    Args:
        id: Object ID to filter messages for.
        count: Max messages (default 100).
        date_range: Relative date filter: today, yesterday, 7days, 30days, 6months, 12months.
    """
    return _json(await _table(
        "messages", "objid,datetime,parent,type,name,status,message",
        id=id, count=count, filter_drel=date_range, sortby="-datetime",
    ))


@mcp.tool()
async def search(query: str, type: str = "sensors", count: int = 50) -> str:
    """Search PRTG objects by name.

    Args:
        query: Text to search for in object names.
        type: Object type: sensors, devices, or groups.
        count: Max results (default 50).
    """
    cols = {
        "sensors": "objid,name,status,type,tags,device,group,lastvalue",
        "devices": "objid,name,status,host,group,tags",
        "groups": "objid,name,status,totalsens",
    }
    return _json(await _table(
        type, cols.get(type, cols["sensors"]),
        count=count, filter_name=f"@sub({query})",
    ))


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
