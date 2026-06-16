"""
jarvis.py  —  El asistente (la DEMO en vivo)
============================================
Junta las tres piezas del proyecto:
  - el MODELO local (Ollama, CPU-only)
  - las HERRAMIENTAS vía MCP (mcp_server.py)
  - (el RAG entra como una herramienta más: search_docs)

Tiene dos clases bien separadas para que se entiendan:
  MCPClient : se conecta al servidor MCP y te da sus herramientas.
  LLM       : habla con el modelo y, si hace falta, ejecuta herramientas.

Cómo se ejecuta:
  python jarvis.py
Escribe tu mensaje y pulsa Enter. Escribe "salir" para terminar.
"""
import asyncio
import json
import os
import sys
import threading
from pathlib import Path

import ollama
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# --- Configuración (desde .env en la raíz del proyecto, con valores por defecto) ---
ROOT = Path(__file__).resolve().parent          # carpeta asistente/
load_dotenv(ROOT.parent / ".env")               # .env está en la raíz del proyecto
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b-instruct-q4_K_M").strip()
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").strip()

# El servidor MCP (mcp_server.py) está en esta misma carpeta (asistente/)
SERVER_PARAMS = StdioServerParameters(command=sys.executable,
                                      args=[str(ROOT / "mcp_server.py")])

# Instrucciones fijas para el modelo (cómo debe comportarse).
SYSTEM_PROMPT = (
    "Eres IRONMAN, un asistente personal. Responde SIEMPRE en el mismo idioma "
    "en que te habla el usuario (español o inglés). Sé breve, natural y claro. "
    "Cuando el usuario pida algo sobre su correo, abrir aplicaciones, buscar en "
    "internet o consultar la documentación local, usa la herramienta adecuada "
    "en vez de inventar la respuesta."
)
OPTIONS = {"num_gpu": 0}  # CPU-only (requisito del enunciado)


# ============================================================================
# MCPClient: conexión al servidor MCP.
# El SDK de MCP es ASÍNCRONO (usa async/await). Para usarlo de forma normal
# (síncrona) desde el asistente, lanzamos su bucle asyncio en un hilo aparte
# y le mandamos las peticiones a ese hilo. Eso es todo el "truco".
# ============================================================================
class MCPClient:
    def __init__(self, params: StdioServerParameters = SERVER_PARAMS):
        self.params = params
        self._loop = asyncio.new_event_loop()   # bucle asyncio propio
        self._ready = threading.Event()         # avisa cuando ya conectó
        self._closing = asyncio.Event()         # señal para cerrar
        self.tools = []                         # herramientas del servidor
        threading.Thread(target=self._run_loop, daemon=True).start()
        self._ready.wait(timeout=30)
        if not self.tools:
            raise RuntimeError("No se pudo conectar al servidor MCP")

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._session_main())

    async def _session_main(self):
        # Arranca mcp_server.py y mantiene la sesión abierta hasta que cerremos.
        async with stdio_client(self.params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                self._session = session
                self.tools = (await session.list_tools()).tools
                self._ready.set()
                await self._closing.wait()

    def call_tool(self, name: str, arguments: dict) -> str:
        """Ejecuta una herramienta del servidor y devuelve su texto."""
        async def _call():
            result = await self._session.call_tool(name, arguments)
            return "\n".join(c.text for c in result.content if getattr(c, "text", None))
        return asyncio.run_coroutine_threadsafe(_call(), self._loop).result(timeout=300)

    def ollama_tools(self) -> list[dict]:
        """Traduce las herramientas MCP al formato que entiende Ollama."""
        return [{"type": "function",
                 "function": {"name": t.name, "description": t.description or "",
                              "parameters": t.inputSchema}} for t in self.tools]

    def handlers(self) -> dict:
        """Devuelve {nombre: función} para que el LLM pueda ejecutarlas."""
        return {t.name: (lambda n: lambda **kw: self.call_tool(n, kw))(t.name)
                for t in self.tools}

    def close(self):
        self._loop.call_soon_threadsafe(self._closing.set)


# ============================================================================
# LLM: habla con el modelo y orquesta las herramientas.
# ============================================================================
class LLM:
    def __init__(self, tools=None, tool_handlers=None):
        self.client = ollama.Client(host=OLLAMA_HOST)
        self.model = OLLAMA_MODEL
        self.tools = tools or []
        self.tool_handlers = tool_handlers or {}
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.total_tokens = 0          # tokens acumulados (para la Parte E)
        self.last_tools_called = []    # herramientas usadas en la última pregunta

    def reset(self):
        """Borra el historial menos el system prompt (para empezar de cero)."""
        self.history = self.history[:1]

    def _count(self, response):
        self.total_tokens += (response.get("prompt_eval_count", 0)
                              + response.get("eval_count", 0))

    @staticmethod
    def _tool_call_in_text(content: str):
        """A veces el modelo de 3B escribe la llamada a herramienta como texto
        JSON en lugar de hacerla bien. Esto la detecta y la rescata.
        Devuelve (nombre, argumentos) o None."""
        if not content:
            return None
        text = content.strip()
        if not (text.startswith("{") and text.endswith("}")):
            return None
        try:
            data = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return None
        name = data.get("name")
        args = data.get("parameters") or data.get("arguments") or {}
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except (json.JSONDecodeError, ValueError):
                args = {}
        return (name, args) if name else None

    def ask(self, user_text: str) -> str:
        """Procesa el mensaje del usuario, usa herramientas si hace falta y
        devuelve la respuesta final en texto."""
        self.history.append({"role": "user", "content": user_text})
        self.last_tools_called = []

        # 1) Primera pasada: el modelo decide si responder o usar herramienta.
        response = self.client.chat(model=self.model, messages=self.history,
                                    tools=self.tools, options=OPTIONS)
        self._count(response)
        message = response["message"]
        tool_calls = message.get("tool_calls")

        # 2) Plan B: ¿escribió la llamada como texto JSON? La rescatamos.
        if not tool_calls:
            parsed = self._tool_call_in_text(message.get("content", ""))
            if parsed:
                name, args = parsed
                if name in self.tool_handlers:
                    tool_calls = [{"function": {"name": name, "arguments": args}}]
                    message = {"role": "assistant", "content": ""}
                else:
                    clean = self.client.chat(model=self.model, messages=self.history,
                                             options=OPTIONS)
                    self._count(clean)
                    message = clean["message"]

        # 3) Si hay herramientas que ejecutar, las corremos y devolvemos el
        #    resultado al modelo para que redacte la respuesta final.
        if tool_calls:
            self.history.append(message)
            for call in tool_calls:
                fn = call["function"]["name"]
                args = call["function"].get("arguments", {}) or {}
                self.last_tools_called.append(fn)
                handler = self.tool_handlers.get(fn)
                result = handler(**args) if handler else f"Herramienta '{fn}' no existe."
                self.history.append({"role": "tool", "content": str(result)})
            response = self.client.chat(model=self.model, messages=self.history,
                                        options=OPTIONS)
            self._count(response)
            message = response["message"]

        self.history.append({"role": "assistant", "content": message["content"]})
        return message["content"].strip()


# ============================================================================
# Programa principal: el bucle de chat.
# ============================================================================
def main():
    print("Conectando al servidor MCP local...")
    mcp = MCPClient()
    print("Herramientas disponibles:", ", ".join(t.name for t in mcp.tools))
    llm = LLM(tools=mcp.ollama_tools(), tool_handlers=mcp.handlers())
    print("\nJarvis listo. Escribe tu mensaje ('salir' para terminar).\n")
    try:
        while True:
            try:
                texto = input("Tú: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not texto or texto.lower() in {"salir", "exit", "adios", "adiós"}:
                break
            print(f"Jarvis: {llm.ask(texto)}\n")
    finally:
        mcp.close()


if __name__ == "__main__":
    main()
