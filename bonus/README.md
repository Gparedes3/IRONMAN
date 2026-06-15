# bonus/ — material extra (fuera del núcleo evaluado)

Aquí se guarda lo que **no** forma parte del núcleo de la asignación, para
recuperarlo más adelante (fase "haz lo más loco posible"). Nada de esto se
necesita para cumplir las Partes A–F.

## Contenido

| Archivo | Qué es | Depende de |
|---|---|---|
| `voice/stt.py` | Reconocimiento de voz (faster-whisper) | `faster-whisper`, `sounddevice`, `numpy` |
| `voice/tts.py` | Síntesis de voz (pyttsx3) | `pyttsx3` |
| `assistant.py` | Bucle del asistente por voz (STT → LLM → TTS) | `ironman.voice`, herramientas directas |
| `main.py` | Punto de entrada del modo voz | `ironman.assistant` |
| `diagnostico.py` | Diagnóstico de audio (micro/altavoces) | `pyttsx3`, `sounddevice`, `numpy` |
| `gui.py` | Interfaz gráfica | — |
| `chat_texto.py` | Chat de texto antiguo (sustituido por `jarvis.py`) | — |
| `IRONMAN.bat`, `IRONMAN_VENTANA.bat` | Lanzadores de Windows | — |

## Cómo volver a activar la voz (más adelante)

1. Reinstalar las deps de voz:
   ```powershell
   .\.venv\Scripts\pip.exe install faster-whisper==1.2.1 sounddevice==0.5.5 pyttsx3==2.99
   ```
2. Mover `voice/` de vuelta a `ironman/voice/` y `assistant.py` a `ironman/`.
3. Restaurar en `ironman/config.py` y `.env.example` las variables de voz
   (`WHISPER_MODEL`, `DEFAULT_LANGUAGE`, `ASSISTANT_NAME`, `MIC_DEVICE`).
4. Ejecutar `python main.py`.
