"""
medir_comun.py
==============
Funciones de MEDICIÓN que comparten la Parte A (cuantización) y la Parte B
(KV cache). Aquí está TODO el "cómo se mide", para no repetirlo en cada parte.

¿Qué se mide y cómo?
  - tokens/segundo: NO se estima a ojo. Se toman de los contadores que el
    propio Ollama devuelve en cada respuesta:
        eval_count / eval_duration       -> velocidad de GENERACIÓN (decode)
        prompt_eval_count / ..._duration -> velocidad de PREFILL (leer el prompt)
  - RAM pico: un hilo en segundo plano mira cada 0.2 s cuánta memoria usan los
    procesos de Ollama y se queda con el valor máximo (el "pico").
  - CPU-only: en cada llamada se pasa options={"num_gpu": 0} para que NINGUNA
    capa use la GPU. Es la restricción del enunciado (este portátil tiene una
    RTX 4060 que se apaga a propósito).
  - Reproducibilidad: temperature=0 y seed=42 hacen que el modelo responda
    siempre lo mismo, así los números se pueden repetir.
"""
import threading
import time

import ollama
import psutil

# Dirección donde escucha el servidor de Ollama en local.
OLLAMA_HOST = "http://localhost:11434"


def ollama_ram_mb() -> float:
    """Devuelve cuánta RAM (en MB) están usando ahora mismo los procesos de
    Ollama: el servidor y el 'runner' que ejecuta el modelo (llama-server)."""
    total = 0
    for p in psutil.process_iter(["name", "memory_info"]):
        try:
            name = (p.info["name"] or "").lower()
            if "ollama" in name or "llama-server" in name:
                total += p.info["memory_info"].rss  # rss = memoria realmente usada
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return total / (1024 * 1024)  # bytes -> MB


class RamMonitor:
    """Vigila la RAM de Ollama en segundo plano y recuerda el PICO.

    Se usa con 'with': al entrar arranca un hilo que mide cada 0.2 s; al salir
    lo para. Después se lee monitor.peak_mb para saber el máximo observado.
    """

    def __init__(self, interval: float = 0.2):
        self.interval = interval        # cada cuánto mide (segundos)
        self.peak_mb = 0.0              # máximo observado
        self._stop = threading.Event()  # señal para parar el hilo
        self._thread = None

    def __enter__(self):
        self.peak_mb = ollama_ram_mb()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def _run(self):
        while not self._stop.is_set():
            self.peak_mb = max(self.peak_mb, ollama_ram_mb())
            time.sleep(self.interval)

    def __exit__(self, *exc):
        self._stop.set()
        self._thread.join(timeout=2)


def model_file_size_mb(client: ollama.Client, model: str) -> float:
    """Tamaño en MB del fichero del modelo (GGUF) según el registro de Ollama."""
    for m in client.list()["models"]:
        if m["model"] == model:
            return m["size"] / (1024 * 1024)
    raise ValueError(f"Modelo no encontrado localmente: {model}")


def stop_model(model: str):
    """Descarga el modelo de la RAM para que la siguiente medición empiece
    'limpia' (sin memoria sobrante de la prueba anterior)."""
    import subprocess
    subprocess.run(["ollama", "stop", model], capture_output=True)
    time.sleep(2)


def timed_generate(client: ollama.Client, model: str, prompt: str,
                   num_predict: int = 200, num_ctx: int = 2048,
                   system: str | None = None) -> dict:
    """Genera una respuesta CPU-only y devuelve las métricas + el texto.

    Parámetros importantes:
      num_predict : cuántos tokens generar como máximo (200 = medición fija).
      num_ctx     : tamaño de la ventana de contexto (la Parte B lo cambia).

    Devuelve un diccionario con: texto, tokens de prompt y generados,
    velocidades de prefill y generación, segundos totales y RAM pico.
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    t0 = time.perf_counter()
    with RamMonitor() as mon:                # mide la RAM mientras genera
        resp = client.chat(
            model=model,
            messages=messages,
            options={
                "num_gpu": 0,        # CPU-only (requisito del enunciado)
                "num_predict": num_predict,
                "num_ctx": num_ctx,
                "temperature": 0,    # determinista -> reproducible
                "seed": 42,
            },
        )
    wall_s = time.perf_counter() - t0        # tiempo real de pared

    # tokens/s = tokens / (nanosegundos / 1e9). max(...,1) evita dividir por 0.
    eval_tps = resp.get("eval_count", 0) / max(resp.get("eval_duration", 1), 1) * 1e9
    prompt_tps = (resp.get("prompt_eval_count", 0)
                  / max(resp.get("prompt_eval_duration", 1), 1) * 1e9)
    return {
        "text": resp["message"]["content"],
        "prompt_tokens": resp.get("prompt_eval_count", 0),
        "gen_tokens": resp.get("eval_count", 0),
        "prompt_eval_tps": round(prompt_tps, 2),
        "eval_tps": round(eval_tps, 2),
        "wall_s": round(wall_s, 2),
        "peak_ram_mb": round(mon.peak_mb, 1),
    }
