"""Habilidad de sistema: abrir aplicaciones, abrir webs y buscar en internet."""
import os
import subprocess
import urllib.parse
import webbrowser

# Apps comunes en Windows mapeadas a su ejecutable / comando.
APPS = {
    "navegador": "start chrome",
    "chrome": "start chrome",
    "edge": "start msedge",
    "explorador": "explorer",
    "explorador de archivos": "explorer",
    "bloc de notas": "notepad",
    "notepad": "notepad",
    "calculadora": "calc",
    "calculator": "calc",
    "cmd": "start cmd",
    "terminal": "start cmd",
    "spotify": "start spotify:",
    "word": "start winword",
    "excel": "start excel",
}


def open_app(name: str) -> str:
    """Abre una aplicación por su nombre."""
    clave = name.lower().strip()
    comando = APPS.get(clave)
    try:
        if comando:
            subprocess.Popen(comando, shell=True)
            return f"Abriendo {name}."
        # Intento genérico: lanzar por nombre directamente
        subprocess.Popen(f"start {clave}", shell=True)
        return f"Intentando abrir {name}."
    except Exception as e:
        return f"No pude abrir {name}: {e}"


def open_website(url: str) -> str:
    """Abre una URL en el navegador."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    return f"Abriendo {url}."


def web_search(query: str) -> str:
    """Abre una búsqueda en Google con la consulta dada."""
    q = urllib.parse.quote(query)
    webbrowser.open(f"https://www.google.com/search?q={q}")
    return f"Buscando '{query}' en internet."
