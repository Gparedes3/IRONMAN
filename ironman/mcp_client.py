"""Cliente MCP síncrono para el asistente.

Lanza el servidor MCP local (mcp_server/server.py) por stdio, descubre sus
herramientas y las traduce al formato de tools de Ollama. El bucle asyncio
del SDK MCP vive en un hilo de fondo; el asistente lo usa de forma síncrona.
"""
import asyncio
import sys
import threading
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parent.parent
SERVER_PARAMS = StdioServerParameters(
    command=sys.executable,
    args=[str(ROOT / "mcp_server" / "server.py")],
)


class MCPClient:
    """Conexión persistente a un servidor MCP por stdio, con API síncrona."""

    def __init__(self, params: StdioServerParameters = SERVER_PARAMS):
        self.params = params
        self._loop = asyncio.new_event_loop()
        self._ready = threading.Event()
        self._closing = asyncio.Event()
        self.tools = []  # lista de mcp.types.Tool
        thread = threading.Thread(target=self._run_loop, daemon=True)
        thread.start()
        self._ready.wait(timeout=30)
        if not self.tools:
            raise RuntimeError("No se pudo conectar al servidor MCP")

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._session_main())

    async def _session_main(self):
        async with stdio_client(self.params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                self._session = session
                self.tools = (await session.list_tools()).tools
                self._ready.set()
                await self._closing.wait()  # mantener viva la sesión

    def call_tool(self, name: str, arguments: dict) -> str:
        """Invoca una herramienta MCP y devuelve su texto."""
        async def _call():
            result = await self._session.call_tool(name, arguments)
            return "\n".join(c.text for c in result.content
                             if getattr(c, "text", None))
        fut = asyncio.run_coroutine_threadsafe(_call(), self._loop)
        return fut.result(timeout=120)

    def ollama_tools(self) -> list[dict]:
        """Esquemas MCP -> formato de tools del API de Ollama."""
        return [{
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description or "",
                "parameters": t.inputSchema,
            },
        } for t in self.tools]

    def handlers(self) -> dict:
        """name -> callable, compatible con LLM(tool_handlers=...)."""
        return {t.name: (lambda _n: lambda **kw: self.call_tool(_n, kw))(t.name)
                for t in self.tools}

    def close(self):
        self._loop.call_soon_threadsafe(self._closing.set)
