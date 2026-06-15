"""Cliente del modelo de lenguaje local (Ollama) con soporte de herramientas.

El modelo decide, en función de lo que pides, si responder con texto o
llamar a una "herramienta" (resumir correo, enviar correo, abrir app, etc.).
"""
import json

import ollama

from ironman import config

SYSTEM_PROMPT = (
    "Eres IRONMAN, un asistente personal de voz. Eres bilingüe: responde "
    "SIEMPRE en el mismo idioma en que te habla el usuario (español o inglés). "
    "Tus respuestas se leerán en voz alta, así que sé breve, natural y claro. "
    "No uses markdown, listas con asteriscos ni emojis en tus respuestas habladas. "
    "Cuando el usuario pida algo sobre su correo o sobre abrir aplicaciones o "
    "buscar en internet, usa la herramienta adecuada en vez de inventar la respuesta."
)


# CPU-only: el enunciado prohíbe GPU dedicada en el camino de inferencia.
OPTIONS = {"num_gpu": 0}


class LLM:
    def __init__(self, tools=None, tool_handlers=None):
        self.client = ollama.Client(host=config.OLLAMA_HOST)
        self.model = config.OLLAMA_MODEL
        self.tools = tools or []
        self.tool_handlers = tool_handlers or {}
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.total_tokens = 0        # prompt + generados, acumulado
        self.last_tools_called = []  # nombres de tools de la última petición

    def reset(self):
        self.history = self.history[:1]

    def _count(self, response):
        self.total_tokens += (response.get("prompt_eval_count", 0)
                              + response.get("eval_count", 0))

    @staticmethod
    def _tool_call_in_text(content: str):
        """llama3.1 a veces emite la llamada a herramienta como texto JSON
        en lugar de en el campo tool_calls. Lo detectamos aquí.
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
        """Envía el mensaje del usuario, ejecuta herramientas si hace falta,
        y devuelve la respuesta final en texto."""
        self.history.append({"role": "user", "content": user_text})
        self.last_tools_called = []

        response = self.client.chat(
            model=self.model,
            messages=self.history,
            tools=self.tools,
            options=OPTIONS,
        )
        self._count(response)
        message = response["message"]
        tool_calls = message.get("tool_calls")

        # Plan B: ¿llamada a herramienta colada como texto JSON?
        if not tool_calls:
            parsed = self._tool_call_in_text(message.get("content", ""))
            if parsed:
                name, args = parsed
                if name in self.tool_handlers:
                    # Es una herramienta real: la convertimos en tool_call normal.
                    tool_calls = [{"function": {"name": name, "arguments": args}}]
                    message = {"role": "assistant", "content": ""}
                else:
                    # Herramienta inventada: re-preguntamos SIN tools para
                    # obtener una respuesta natural en texto.
                    clean = self.client.chat(model=self.model, messages=self.history,
                                             options=OPTIONS)
                    self._count(clean)
                    message = clean["message"]

        # ¿El modelo quiere llamar a una herramienta?
        if tool_calls:
            self.history.append(message)
            for call in tool_calls:
                fn = call["function"]["name"]
                args = call["function"].get("arguments", {}) or {}
                self.last_tools_called.append(fn)
                handler = self.tool_handlers.get(fn)
                result = handler(**args) if handler else f"Herramienta '{fn}' no existe."
                self.history.append({"role": "tool", "content": str(result)})

            # Segunda pasada: el modelo redacta la respuesta final con el resultado
            response = self.client.chat(model=self.model, messages=self.history,
                                        options=OPTIONS)
            self._count(response)
            message = response["message"]

        self.history.append({"role": "assistant", "content": message["content"]})
        return message["content"].strip()
