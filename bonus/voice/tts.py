"""Síntesis de voz (Text-To-Speech) offline con pyttsx3.

Usa las voces SAPI5 de Windows. Selecciona automáticamente una voz en
español o inglés según el idioma del texto.
"""
import pyttsx3


class TextToSpeech:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 180)  # velocidad de habla
        self._voices = self.engine.getProperty("voices")
        self._es_voice = self._find_voice(("spanish", "español", "helena",
                                           "sabina", "es-", "es_"))
        self._en_voice = self._find_voice(("english", "zira", "david",
                                           "en-", "en_"))

    def _find_voice(self, keywords: tuple[str, ...]):
        for v in self._voices:
            blob = f"{v.id} {v.name} {getattr(v, 'languages', '')}".lower()
            if any(k in blob for k in keywords):
                return v.id
        return None

    def say(self, text: str, language: str = "es"):
        if not text:
            return
        voice = self._es_voice if language.startswith("es") else self._en_voice
        if voice:
            self.engine.setProperty("voice", voice)
        print(f"🔊 {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def list_voices(self):
        """Imprime las voces instaladas (útil para depurar)."""
        for v in self._voices:
            print(f" - {v.name}  [{v.id}]")
