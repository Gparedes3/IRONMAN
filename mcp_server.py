"""
mcp_server.py  —  PARTE D del trabajo (herramientas vía MCP)
============================================================
MCP (Model Context Protocol) es un estándar para que un asistente de IA use
"herramientas" externas. Este archivo es un SERVIDOR MCP: publica 6 herramientas
que cualquier cliente MCP (nuestro jarvis.py, o Claude Desktop) puede usar.

Las 6 herramientas:
  - fetch_recent_emails : lee los últimos correos (Gmail por IMAP)
  - send_email          : envía un correo (Gmail por SMTP)
  - open_app            : abre una aplicación del PC (calculadora, chrome...)
  - open_website        : abre una página web en el navegador
  - web_search          : busca algo en internet
  - search_docs         : busca en el corpus local (RAG, Parte C)

Cómo se ejecuta:
  - Normalmente NO lo arrancas tú: jarvis.py lo lanza por debajo.
  - Para probarlo suelto (debug):  python mcp_server.py
"""
import imaplib
import smtplib
import email
import os
import subprocess
import urllib.parse
import webbrowser
from email.header import decode_header
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Carga las credenciales del archivo .env (correo, etc.). Nunca van en el código.
load_dotenv()
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS", "").strip()
EMAIL_APP_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD", "").strip()
IMAP_HOST = os.environ.get("IMAP_HOST", "imap.gmail.com").strip()
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com").strip()
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))

# Crea el servidor MCP. El nombre es solo una etiqueta.
mcp = FastMCP("ironman-tools")


# =========================== herramientas de CORREO =========================
def _decode(value) -> str:
    """Decodifica cabeceras de correo (que vienen codificadas en raro)."""
    if value is None:
        return ""
    out = []
    for text, enc in decode_header(value):
        if isinstance(text, bytes):
            out.append(text.decode(enc or "utf-8", errors="ignore"))
        else:
            out.append(text)
    return "".join(out)


@mcp.tool()
def fetch_recent_emails(count: int = 5) -> str:
    """Lee los correos más recientes del usuario y devuelve remitente y asunto."""
    try:
        imap = imaplib.IMAP4_SSL(IMAP_HOST)
        imap.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        imap.select("INBOX")
        status, data = imap.search(None, "ALL")
        if status != "OK" or not data[0]:
            imap.logout()
            return "No hay correos en la bandeja de entrada."
        ids = data[0].split()[-count:][::-1]  # los más recientes primero
        lineas = []
        for i, msg_id in enumerate(ids, 1):
            status, msg_data = imap.fetch(msg_id, "(RFC822.HEADER)")
            if status != "OK":
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            lineas.append(f"{i}. De: {_decode(msg.get('From'))} | "
                          f"Asunto: {_decode(msg.get('Subject'))}")
        imap.logout()
        return "Correos recientes:\n" + "\n".join(lineas) if lineas \
            else "No se pudieron leer los correos."
    except Exception as e:
        return f"Error al leer el correo: {e}"


@mcp.tool()
def send_email(to: str, subject: str, body: str) -> str:
    """Envía un correo electrónico desde la cuenta configurada."""
    try:
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = EMAIL_ADDRESS, to, subject
        msg.set_content(body)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
            server.send_message(msg)
        return f"Correo enviado correctamente a {to}."
    except Exception as e:
        return f"Error al enviar el correo: {e}"


# =========================== herramientas de SISTEMA ========================
# Nombres comunes de apps de Windows -> comando para abrirlas.
APPS = {
    "navegador": "start chrome", "chrome": "start chrome", "edge": "start msedge",
    "explorador": "explorer", "bloc de notas": "notepad", "notepad": "notepad",
    "calculadora": "calc", "calculator": "calc", "cmd": "start cmd",
    "terminal": "start cmd", "spotify": "start spotify:", "word": "start winword",
    "excel": "start excel",
}


@mcp.tool()
def open_app(name: str) -> str:
    """Abre una aplicación del PC por su nombre (ej: calculadora, chrome)."""
    clave = name.lower().strip()
    try:
        comando = APPS.get(clave, f"start {clave}")  # si no está, intento genérico
        subprocess.Popen(comando, shell=True)
        return f"Abriendo {name}."
    except Exception as e:
        return f"No pude abrir {name}: {e}"


@mcp.tool()
def open_website(url: str) -> str:
    """Abre una página web concreta en el navegador por su URL."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    return f"Abriendo {url}."


@mcp.tool()
def web_search(query: str) -> str:
    """Busca algo en internet abriendo Google con la consulta."""
    webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
    return f"Buscando '{query}' en internet."


# =========================== herramienta de RAG ============================
@mcp.tool()
def search_docs(query: str) -> str:
    """Busca en la base de conocimiento local (docs de Ollama y llama.cpp) y
    devuelve los fragmentos más relevantes. Úsala para preguntas técnicas sobre
    Ollama, llama.cpp, GGUF, cuantización o configuración."""
    from parte_c_rag import retrieve  # import aquí para no cargar el RAG si no se usa
    hits = retrieve(query, k=4)
    if not hits:
        return "No se encontró nada relevante en la base de conocimiento."
    return "\n\n---\n\n".join(f"[{h['source']}]\n{h['text']}" for h in hits)


if __name__ == "__main__":
    mcp.run()  # arranca el servidor por stdio (entrada/salida estándar)
