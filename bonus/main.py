"""Punto de entrada de IRONMAN. Ejecuta:  python main.py"""
import sys

# En Windows la salida estándar usa cp1252 cuando se redirige/captura, lo que
# rompe los emojis (🔊, 🎤). Forzamos UTF-8 para que los prints no fallen.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from ironman.assistant import main

if __name__ == "__main__":
    main()
