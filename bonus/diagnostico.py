"""Diagnostico de audio para IRONMAN: voces TTS, dispositivos y captura de mic."""
import sys
for s in (sys.stdout, sys.stderr):
    try:
        s.reconfigure(encoding="utf-8")
    except Exception:
        pass

print("=" * 50)
print("1) VOCES TTS (SAPI) INSTALADAS")
print("=" * 50)
try:
    import pyttsx3
    eng = pyttsx3.init()
    voices = eng.getProperty("voices")
    for v in voices:
        print(f"  - {v.name}  | id={v.id} | langs={getattr(v,'languages','')}")
    print(">> Reproduciendo frase de prueba por los ALTAVOCES...")
    eng.say("Prueba de voz de IRONMAN. Si escuchas esto, los altavoces funcionan.")
    eng.runAndWait()
    print(">> Frase de prueba enviada.")
except Exception as e:
    print(f"  ERROR TTS: {e}")

print()
print("=" * 50)
print("2) DISPOSITIVOS DE AUDIO")
print("=" * 50)
try:
    import sounddevice as sd
    print(sd.query_devices())
    print()
    try:
        din, dout = sd.default.device
        print(f">> Entrada por defecto (mic): index {din}")
        print(f">> Salida por defecto (altavoz): index {dout}")
    except Exception as e:
        print(f"  No hay default device claro: {e}")
except Exception as e:
    print(f"  ERROR dispositivos: {e}")

print()
print("=" * 50)
print("3) CAPTURA DE MICROFONO (3 segundos)")
print("=" * 50)
print(">> HABLA AHORA durante 3 segundos...")
try:
    import numpy as np
    import sounddevice as sd
    fs = 16000
    audio = sd.rec(int(3 * fs), samplerate=fs, channels=1, dtype="float32")
    sd.wait()
    rms = float(np.sqrt(np.mean(audio ** 2)))
    peak = float(np.max(np.abs(audio)))
    print(f">> Nivel RMS captado: {rms:.5f}  (umbral de IRONMAN = 0.01)")
    print(f">> Pico maximo: {peak:.5f}")
    if rms < 0.005:
        print(">> RESULTADO: casi NO se captó sonido. El micro no graba o esta mudo/mal seleccionado.")
    elif rms < 0.01:
        print(">> RESULTADO: se captó algo MUY bajo. IRONMAN podria no detectarlo (sube el volumen del mic o acercate).")
    else:
        print(">> RESULTADO: micro OK, capta sonido suficiente.")
except Exception as e:
    print(f"  ERROR captura mic: {e}")

print()
print("Diagnostico terminado.")
