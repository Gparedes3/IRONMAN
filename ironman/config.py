"""Carga la configuración desde el archivo .env."""
import os
from dotenv import load_dotenv

load_dotenv()


def _get(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


# --- Correo ---
EMAIL_ADDRESS = _get("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = _get("EMAIL_APP_PASSWORD")
IMAP_HOST = _get("IMAP_HOST", "imap.gmail.com")
SMTP_HOST = _get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(_get("SMTP_PORT", "587"))

# --- LLM (Ollama) ---
OLLAMA_MODEL = _get("OLLAMA_MODEL", "llama3.2:3b-instruct-q4_K_M")
OLLAMA_HOST = _get("OLLAMA_HOST", "http://localhost:11434")


def validate() -> list[str]:
    """Devuelve una lista de problemas de configuración (vacía si todo bien)."""
    problemas = []
    if not EMAIL_ADDRESS or "@" not in EMAIL_ADDRESS:
        problemas.append("EMAIL_ADDRESS no está configurado en .env")
    if not EMAIL_APP_PASSWORD or EMAIL_APP_PASSWORD.startswith("x"):
        problemas.append("EMAIL_APP_PASSWORD no está configurado en .env "
                         "(genera una contraseña de aplicación en Google)")
    return problemas
