"""Parte D — Servidor MCP propio (stdio) para IRONMAN/Jarvis.

Expone las capacidades del asistente como herramientas estándar del
Model Context Protocol, usando el SDK oficial de Python (FastMCP):

  - fetch_recent_emails / send_email  (Gmail vía IMAP/SMTP, credenciales .env)
  - open_app / open_website / web_search (control del PC)
  - search_docs (recuperación RAG sobre el corpus local de la Parte C)

Cualquier cliente MCP (este Jarvis, Claude Desktop, etc.) puede conectarse:
  command: python   args: [mcp_server/server.py]

Uso directo (debug):  python mcp_server/server.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "rag"))

from mcp.server.fastmcp import FastMCP

from ironman.skills import email_skill, system_skill

mcp = FastMCP("ironman-tools")


@mcp.tool()
def fetch_recent_emails(count: int = 5) -> str:
    """Lee los correos más recientes de la bandeja de entrada del usuario
    y devuelve remitente y asunto de cada uno."""
    return email_skill.fetch_recent_emails(count)


@mcp.tool()
def send_email(to: str, subject: str, body: str) -> str:
    """Envía un correo electrónico en nombre del usuario."""
    return email_skill.send_email(to, subject, body)


@mcp.tool()
def open_app(name: str) -> str:
    """Abre una aplicación instalada en el PC (ej: calculadora, chrome, notepad)."""
    return system_skill.open_app(name)


@mcp.tool()
def open_website(url: str) -> str:
    """Abre una página web concreta en el navegador por su URL."""
    return system_skill.open_website(url)


@mcp.tool()
def web_search(query: str) -> str:
    """Busca algo en internet abriendo el navegador con la consulta."""
    return system_skill.web_search(query)


@mcp.tool()
def search_docs(query: str) -> str:
    """Busca en la base de conocimiento local (documentación de Ollama y
    llama.cpp) y devuelve los fragmentos más relevantes. Úsala para preguntas
    técnicas sobre Ollama, llama.cpp, GGUF, cuantización o configuración."""
    from rag import retrieve  # import perezoso: requiere índice construido
    hits = retrieve(query, k=4)
    if not hits:
        return "No se encontró nada relevante en la base de conocimiento."
    return "\n\n---\n\n".join(f"[{h['source']}]\n{h['text']}" for h in hits)


if __name__ == "__main__":
    mcp.run()  # transporte stdio por defecto
