"""Ensambla voz + LLM + habilidades y ejecuta el bucle del asistente."""
from ironman import config
from ironman.llm import LLM
from ironman.voice.stt import SpeechToText
from ironman.voice.tts import TextToSpeech
from ironman.skills import email_skill, system_skill

# --- Definición de herramientas que el modelo puede invocar ---
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "fetch_recent_emails",
            "description": "Lee y resume los correos más recientes de la bandeja de entrada del usuario.",
            "parameters": {
                "type": "object",
                "properties": {
                    "count": {"type": "integer", "description": "Cuántos correos leer (por defecto 5)."}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Envía un correo electrónico en nombre del usuario.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Dirección del destinatario."},
                    "subject": {"type": "string", "description": "Asunto del correo."},
                    "body": {"type": "string", "description": "Cuerpo del mensaje."},
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Abre una aplicación instalada en el ordenador (ej: calculadora, chrome, spotify).",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Busca algo en internet abriendo el navegador.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_website",
            "description": "Abre una página web concreta por su URL.",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        },
    },
]

HANDLERS = {
    "fetch_recent_emails": email_skill.fetch_recent_emails,
    "send_email": email_skill.send_email,
    "open_app": system_skill.open_app,
    "web_search": system_skill.web_search,
    "open_website": system_skill.open_website,
}

# Frases para terminar la sesión
EXIT_WORDS = {"adiós", "adios", "hasta luego", "apágate", "apagate",
              "goodbye", "exit", "stop", "para"}


class Assistant:
    def __init__(self):
        self.tts = TextToSpeech()
        self.stt = SpeechToText()
        self.llm = LLM(tools=TOOLS, tool_handlers=HANDLERS)

    def greet(self):
        self.tts.say(f"Hola, soy {config.ASSISTANT_NAME}. ¿En qué puedo ayudarte?", "es")

    def run(self):
        self.greet()
        while True:
            print("\n🎤 Escuchando... (habla ahora)")
            texto, idioma = self.stt.listen()

            if not texto:
                continue
            print(f"🗣️  Tú ({idioma}): {texto}")

            if texto.lower().strip(" .!?") in EXIT_WORDS:
                self.tts.say("Hasta luego." if idioma == "es" else "Goodbye.", idioma)
                break

            try:
                respuesta = self.llm.ask(texto)
            except Exception as e:
                respuesta = f"Hubo un error al procesar la petición: {e}"

            self.tts.say(respuesta, idioma)


def main():
    problemas = config.validate()
    if problemas:
        print("⚠️  Avisos de configuración:")
        for p in problemas:
            print(f"   - {p}")
        print("   (El correo no funcionará hasta que configures .env)\n")

    asistente = Assistant()
    asistente.run()


if __name__ == "__main__":
    main()
