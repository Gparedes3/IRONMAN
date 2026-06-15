"""Modo de prueba por TEXTO (sin micrófono ni voz).

Útil para verificar que Ollama y las habilidades (correo, sistema) funcionan
antes de probar con voz.  Ejecuta:  python chat_texto.py
"""
from ironman import config
from ironman.llm import LLM
from ironman.assistant import TOOLS, HANDLERS

if __name__ == "__main__":
    problemas = config.validate()
    if problemas:
        print("⚠️  Avisos de configuración:")
        for p in problemas:
            print(f"   - {p}\n")

    llm = LLM(tools=TOOLS, tool_handlers=HANDLERS)
    print(f"Chateando con {config.OLLAMA_MODEL}. Escribe 'salir' para terminar.\n")
    while True:
        try:
            texto = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if texto.lower() in {"salir", "exit", "quit"}:
            break
        if not texto:
            continue
        try:
            print(f"IRONMAN: {llm.ask(texto)}\n")
        except Exception as e:
            print(f"[error] {e}\n")
