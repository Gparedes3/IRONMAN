# Parte D.3 — Tool calling: qué funciona y qué falla

Observaciones con `llama3.2:3b-instruct-q4_K_M` (CPU-only) conectado al
servidor MCP propio. Evidencia: `evaluation/results.json` (ids citados).

## Prompts que funcionan de forma fiable

| Prompt | Herramienta | Notas |
|---|---|---|
| "Abre la calculadora." | open_app | Imperativo directo: prácticamente 100%. |
| "Open the website ollama.com" | open_website | URL explícita → argumentos correctos. |
| "Resume mis últimos 5 correos." | fetch_recent_emails | El número se mapea bien a `count`. |
| "Send an email to X with subject Y saying Z" | send_email | Si el prompt da los 3 campos, los rellena bien. |
| "Search the local docs: …" | search_docs | El verbo "search the docs" ancla la elección. |

## Prompts que fallan (y por qué)

Evidencia real de `evaluation/results.json` (corrida del test set completo):

| id | Prompt | Qué pasó | Causa |
|---|---|---|---|
| `tool-02` | "Open the website ollama.com" | Devolvió `{"name":"open_website","parameters":{"url":"https://ollama.com"}}` como **texto** en `content`; la web no se abrió. | El modelo emite la tool call como JSON plano en vez de usar el campo `tool_calls`. |
| `multi-01` | "Busca en docs la variable… y manda la respuesta por correo" | Encadenó `search_docs`+`send_email`, pero el `send_email` salió con `body` vacío. | Multi-paso: planifica la 2ª tool pero no traslada el resultado de la 1ª como argumento. |
| `multi-03` | "Busca cómo activar flash attention y abre ollama.com" | Solo ejecutó `search_docs`; "olvidó" abrir la web. | Multi-paso: se queda en la primera tool. |
| `chat-02` | "Explícame la fotosíntesis" | Llamó a `search_docs` sin necesidad → excepción y latencia de 126.7 s. | Sobre-uso de herramientas en chat puro. |
| `tool-03`, `tool-04`, `multi-02` | tareas de correo | Invoca la tool pero responde "no puedo acceder a tus correos". | Entorno de pruebas sin contraseña de aplicación de Gmail (`.env`). Límite de configuración. |

## Patrones generales observados

1. **Modelos de 3B son literalistas**: si el prompt no menciona la acción
   ("docs", "correo", "abre"), la probabilidad de elegir la tool correcta cae.
2. **Multi-paso es el punto débil**: encadenar 2 tools en un solo turno
   (buscar → enviar) exige que el modelo planifique; a veces se queda en la
   primera tool y "olvida" la segunda.
3. **Tool calls como texto JSON**: llama3.2 a veces emite la llamada como
   JSON plano en `content` en vez del campo `tool_calls`; el cliente lo
   detecta y lo recupera (`ironman/llm.py::_tool_call_in_text`), sin lo cual
   la tasa de éxito caería notablemente.
4. **Sobre-uso de herramientas**: preguntas de cultura general a veces
   disparan `web_search` innecesariamente.
