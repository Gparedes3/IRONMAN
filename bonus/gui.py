"""Interfaz gráfica de IRONMAN: botón "pulsar para hablar", indicador de
estado (escuchando / pensando / hablando) y panel con la conversación.

Ejecuta:  python gui.py   (o doble clic en IRONMAN_VENTANA.bat)
"""
import sys
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

import threading
import tkinter as tk
from tkinter import scrolledtext

from ironman import config
from ironman.assistant import TOOLS, HANDLERS
from ironman.llm import LLM
from ironman.voice.stt import SpeechToText
from ironman.voice.tts import TextToSpeech

# --- Colores del tema ---
BG = "#0f1116"
PANEL = "#1a1d27"
TXT = "#e6e6e6"
ACCENT = "#e23b3b"          # rojo "Iron Man"
USER_COLOR = "#4fc3f7"
BOT_COLOR = "#ffd166"

STATES = {
    "cargando":   ("⏳  Cargando IRONMAN...", "#888888"),
    "listo":      ("🟢  Listo — pulsa para hablar", "#3ddc84"),
    "escuchando": ("🔴  Escuchando... (pulsa para terminar)", ACCENT),
    "procesando": ("🟠  Transcribiendo...", "#ffa726"),
    "pensando":   ("🧠  Pensando...", "#ab8bff"),
    "hablando":   ("🔵  Hablando...", "#4fc3f7"),
}


class IronmanGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.recording = False
        self.busy = True          # ocupado hasta que cargue el modelo
        self.stt = None
        self.tts = None
        self.llm = None

        self._build_ui()
        # Carga pesada (Whisper, etc.) en segundo plano para no congelar la ventana
        threading.Thread(target=self._load_engines, daemon=True).start()

    # ---------- Construcción de la interfaz ----------
    def _build_ui(self):
        self.root.title("IRONMAN")
        self.root.configure(bg=BG)
        self.root.geometry("620x560")
        self.root.minsize(480, 420)

        tk.Label(self.root, text="IRONMAN", bg=BG, fg=ACCENT,
                 font=("Segoe UI", 22, "bold")).pack(pady=(16, 2))

        # Indicador de estado
        self.status = tk.Label(self.root, text=STATES["cargando"][0],
                               bg=BG, fg=STATES["cargando"][1],
                               font=("Segoe UI", 13, "bold"))
        self.status.pack(pady=(0, 10))

        # Panel de conversación
        self.chat = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, bg=PANEL, fg=TXT,
            font=("Segoe UI", 12), bd=0, relief=tk.FLAT,
            padx=12, pady=12, state=tk.DISABLED, height=14)
        self.chat.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)
        self.chat.tag_config("user", foreground=USER_COLOR, font=("Segoe UI", 12, "bold"))
        self.chat.tag_config("bot", foreground=BOT_COLOR, font=("Segoe UI", 12, "bold"))
        self.chat.tag_config("sys", foreground="#888888", font=("Segoe UI", 10, "italic"))

        # Botón grande de pulsar para hablar
        self.button = tk.Button(
            self.root, text="🎤  Pulsa para hablar", command=self.on_button,
            bg=ACCENT, fg="white", activebackground="#b52d2d",
            activeforeground="white", font=("Segoe UI", 15, "bold"),
            bd=0, relief=tk.FLAT, height=2, cursor="hand2", state=tk.DISABLED)
        self.button.pack(fill=tk.X, padx=16, pady=(6, 16))

        # Atajo: barra espaciadora para hablar/terminar
        self.root.bind("<space>", lambda e: self.on_button())

    # ---------- Carga de motores ----------
    def _load_engines(self):
        self._add_system("Cargando reconocimiento de voz, voz y modelo...")
        self.tts = TextToSpeech()
        self.stt = SpeechToText()
        self.llm = LLM(tools=TOOLS, tool_handlers=HANDLERS)
        dev = "por defecto" if self.stt.device is None else \
            f"[{self.stt.device}]"
        self._add_system(f"Listo. Micrófono {dev}. Pulsa el botón (o la barra espaciadora) y habla.")
        self.busy = False
        self._set_state("listo")
        self.root.after(0, lambda: self.button.config(state=tk.NORMAL))

    # ---------- Acción del botón ----------
    def on_button(self):
        if self.busy:
            return
        if not self.recording:
            self.recording = True
            self._set_state("escuchando")
            self.root.after(0, lambda: self.button.config(text="⏹  Terminar"))
            threading.Thread(target=self._record_and_process, daemon=True).start()
        else:
            # Segunda pulsación: deja de grabar (el hilo continúa procesando)
            self.recording = False

    def _record_and_process(self):
        audio = self.stt.record_while(lambda: self.recording)
        self.busy = True
        self.root.after(0, lambda: self.button.config(text="🎤  Pulsa para hablar",
                                                      state=tk.DISABLED))
        self._set_state("procesando")

        texto, idioma = self.stt.transcribe(audio)
        if not texto.strip():
            self._add_system("No te he entendido, inténtalo otra vez.")
            self._finish()
            return

        self._add_message("Tú", texto, "user")
        self._set_state("pensando")
        try:
            respuesta = self.llm.ask(texto)
        except Exception as e:
            respuesta = f"Hubo un error al procesar la petición: {e}"

        self._add_message("IRONMAN", respuesta, "bot")
        self._set_state("hablando")
        try:
            self.tts.say(respuesta, idioma)
        except Exception as e:
            self._add_system(f"(No pude reproducir la voz: {e})")
        self._finish()

    def _finish(self):
        self.recording = False
        self.busy = False
        self._set_state("listo")
        self.root.after(0, lambda: self.button.config(state=tk.NORMAL,
                                                      text="🎤  Pulsa para hablar"))

    # ---------- Utilidades de UI (hilo-seguras) ----------
    def _set_state(self, key):
        text, color = STATES[key]
        self.root.after(0, lambda: self.status.config(text=text, fg=color))

    def _add_message(self, quien, texto, tag):
        def append():
            self.chat.config(state=tk.NORMAL)
            self.chat.insert(tk.END, f"{quien}: ", tag)
            self.chat.insert(tk.END, f"{texto}\n\n")
            self.chat.see(tk.END)
            self.chat.config(state=tk.DISABLED)
        self.root.after(0, append)

    def _add_system(self, texto):
        def append():
            self.chat.config(state=tk.NORMAL)
            self.chat.insert(tk.END, f"{texto}\n", "sys")
            self.chat.see(tk.END)
            self.chat.config(state=tk.DISABLED)
        self.root.after(0, append)


def main():
    root = tk.Tk()
    IronmanGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
