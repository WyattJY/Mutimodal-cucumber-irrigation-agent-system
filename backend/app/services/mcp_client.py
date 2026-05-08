"""MCP client manager for YOLO, TSMixer and RAG tools.

FastMCP/langchain-mcp-adapters are optional at local development time. The
service exposes the same API even when those packages are unavailable so the
Agent graph and FastAPI app remain runnable in mock mode.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

from loguru import logger

from app.core.config import settings
from app.observability.metrics import MCP_TOOL_CALLS, MCP_TOOL_LATENCY, MCP_TOOLS_AVAILABLE


BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
MCP_SERVERS_DIR = BACKEND_DIR / "mcp_servers"

try:
    from langchain_mcp_adapters.client import MultiServerMCPClient  # type: ignore

    MCP_ADAPTERS_AVAILABLE = True
except Exception:
    MultiServerMCPClient = None  # type: ignore
    MCP_ADAPTERS_AVAILABLE = False


class MCPClientService:
    def __init__(self) -> None:
        self._client: Any | None = None
        self._connected = False
        self._tools: dict[str, Any] = {}
        self._error: str | None = None

    async def connect(self) -> None:
        if not settings.enable_mcp:
            self._error = "MCP disabled by ENABLE_MCP=false"
            return
        if not MCP_ADAPTERS_AVAILABLE:
            self._error = "langchain-mcp-adapters is not installed"
            logger.warning(f"[mcp_client] {self._error}")
            return
        if self._connected:
            return

        server_config = {
            "yolo": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(MCP_SERVERS_DIR / "yolo_server.py")],
            },
            "tsmixer": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(MCP_SERVERS_DIR / "tsmixer_server.py")],
            },
            "rag": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(MCP_SERVERS_DIR / "rag_server.py")],
            },
        }
        try:
            self._client = MultiServerMCPClient(server_config)  # type: ignore[misc]
            tools = await self._client.get_tools()
            self._tools = {tool.name: tool for tool in tools}
            MCP_TOOLS_AVAILABLE.set(len(self._tools))
            self._connected = True
            self._error = None
            logger.info(f"[mcp_client] loaded {len(self._tools)} tools")
        except Exception as exc:
            self._client = None
            self._tools = {}
            MCP_TOOLS_AVAILABLE.set(0)
            self._connected = False
            self._error = str(exc)
            logger.warning(f"[mcp_client] unavailable: {exc}")

    async def disconnect(self) -> None:
        self._client = None
        self._tools.clear()
        MCP_TOOLS_AVAILABLE.set(0)
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def available_tools(self) -> list[str]:
        return list(self._tools.keys())

    def get_langchain_tools(self) -> list:
        return list(self._tools.values())

    def get_tool(self, tool_name: str):
        return self._tools.get(tool_name)

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        tool = self._tools.get(tool_name)
        if tool is None:
            MCP_TOOL_CALLS.labels(tool_name=tool_name, status="unavailable").inc()
            return {"success": False, "error": f"MCP tool unavailable: {tool_name}", "mcp_error": self._error}
        started = time.perf_counter()
        try:
            result = await tool.ainvoke(arguments)
            MCP_TOOL_CALLS.labels(tool_name=tool_name, status="success").inc()
            MCP_TOOL_LATENCY.labels(tool_name=tool_name, status="success").observe(time.perf_counter() - started)
            return {"success": True, "result": result}
        except Exception as exc:
            MCP_TOOL_CALLS.labels(tool_name=tool_name, status="error").inc()
            MCP_TOOL_LATENCY.labels(tool_name=tool_name, status="error").observe(time.perf_counter() - started)
            return {"success": False, "error": str(exc)}

    async def health_check(self) -> dict:
        return {
            "connected": self._connected,
            "available_tools": self.available_tools,
            "error": self._error,
            "servers": ["yolo", "tsmixer", "rag"],
        }


mcp_client = MCPClientService()
