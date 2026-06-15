"""Jarvis en modo texto: LLM local (Ollama) + herramientas vía servidor MCP.

Es el mismo cerebro que el modo voz (main.py), pero las herramientas llegan
por el Model Context Protocol en lugar de llamadas directas: el cliente MCP
descubre las tools del servidor (mcp_server/server.py) y se las pasa al LLM.

Uso:  python jarvis.py
"""
from ironman.llm import LLM
from ironman.mcp_client import MCPClient


def main():
    print("Conectando al servidor MCP local...")
    mcp = MCPClient()
    print("Herramientas MCP disponibles:",
          ", ".join(t.name for t in mcp.tools))

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
            respuesta = llm.ask(texto)
            print(f"Jarvis: {respuesta}\n")
    finally:
        mcp.close()


if __name__ == "__main__":
    main()
