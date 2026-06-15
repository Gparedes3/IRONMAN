"""Reconocimiento de voz (Speech-To-Text) local con faster-whisper.

Graba del micrófono hasta detectar silencio y transcribe el audio.
Funciona offline y soporta español e inglés (autodetección).
"""
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from ironman import config

SAMPLE_RATE = 16000          # Whisper trabaja a 16 kHz
BLOCK_DURATION = 0.5         # segundos por bloque de análisis
SILENCE_THRESHOLD = 0.01     # nivel RMS por debajo del cual hay "silencio"
SILENCE_BLOCKS = 3           # bloques seguidos de silencio para cortar (~1.5 s)
MAX_DURATION = 15            # corte de seguridad en segundos


def _resolve_input_device():
    """Elige el micrófono a usar. Evita dispositivos virtuales (Camo, mezcla
    estéreo, etc.) que no captan voz. Respeta config.MIC_DEVICE si se fija."""
    devices = sd.query_devices()
    inputs = [(i, d) for i, d in enumerate(devices)
              if d["max_input_channels"] > 0]

    pref = config.MIC_DEVICE
    if pref:
        if pref.isdigit():
            return int(pref)
        for i, d in inputs:
            if pref.lower() in d["name"].lower():
                return i

    AVOID = ("camo", "virtual", "mezcla", "stereo mix", "estéreo",
             "vb-audio", "voicemeeter", "primario", "asignador",
             "microsoft", "mapper", "controlador")
    PREFER = ("realtek", "microphone", "micrófono")

    for i, d in inputs:                       # 1) micro real preferido
        name = d["name"].lower()
        if any(a in name for a in AVOID):
            continue
        if any(p in name for p in PREFER):
            return i
    for i, d in inputs:                       # 2) cualquiera no virtual
        if not any(a in d["name"].lower() for a in AVOID):
            return i
    return None                               # 3) usa el por defecto del sistema


class SpeechToText:
    def __init__(self):
        self.device = _resolve_input_device()
        if self.device is not None:
            name = sd.query_devices(self.device)["name"]
            print(f"[STT] Micrófono seleccionado: [{self.device}] {name}")
        else:
            print("[STT] Usando el micrófono por defecto del sistema.")
        print(f"[STT] Cargando modelo Whisper '{config.WHISPER_MODEL}'...")
        # compute_type int8 = rápido y ligero en CPU
        self.model = WhisperModel(
            config.WHISPER_MODEL, device="cpu", compute_type="int8"
        )
        print("[STT] Modelo listo.")

    def record_until_silence(self) -> np.ndarray:
        """Graba del micrófono hasta detectar silencio prolongado."""
        block_size = int(SAMPLE_RATE * BLOCK_DURATION)
        frames = []
        silent_blocks = 0
        started = False
        max_blocks = int(MAX_DURATION / BLOCK_DURATION)

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                            dtype="float32", blocksize=block_size,
                            device=self.device) as stream:
            for _ in range(max_blocks):
                block, _overflow = stream.read(block_size)
                block = block.flatten()
                frames.append(block)

                rms = float(np.sqrt(np.mean(block ** 2)))
                if rms > SILENCE_THRESHOLD:
                    started = True
                    silent_blocks = 0
                elif started:
                    silent_blocks += 1
                    if silent_blocks >= SILENCE_BLOCKS:
                        break

        if not frames:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(frames)

    def record_while(self, is_active) -> np.ndarray:
        """Graba mientras `is_active()` devuelva True (modo pulsar-para-hablar)."""
        block_size = int(SAMPLE_RATE * BLOCK_DURATION)
        frames = []
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                            dtype="float32", blocksize=block_size,
                            device=self.device) as stream:
            while is_active():
                block, _overflow = stream.read(block_size)
                frames.append(block.flatten())
        if not frames:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(frames)

    def transcribe(self, audio: np.ndarray) -> tuple[str, str]:
        """Transcribe audio. Devuelve (texto, idioma_detectado)."""
        if audio.size == 0:
            return "", "es"
        segments, info = self.model.transcribe(
            audio,
            language=config.DEFAULT_LANGUAGE,   # None = autodetectar es/en
            beam_size=1,
            vad_filter=True,
        )
        texto = " ".join(seg.text for seg in segments).strip()
        return texto, info.language

    def listen(self) -> tuple[str, str]:
        """Graba y transcribe en un solo paso. Devuelve (texto, idioma)."""
        audio = self.record_until_silence()
        return self.transcribe(audio)
