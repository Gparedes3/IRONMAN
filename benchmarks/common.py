"""Utilidades compartidas por los benchmarks (Partes A y B).

Metodología de medición:
- tokens/s: tomados de la propia respuesta del API de Ollama
  (eval_count / eval_duration). prompt_eval_* mide el prefill (procesar el
  prompt, dominado por el KV cache); eval_* mide la generación (decode).
- RAM pico: un hilo muestrea cada 200 ms la suma de working-set de todos los
  procesos cuyo nombre contiene "ollama" (servidor + runner del modelo) y
  guarda el máximo observado durante la inferencia.
- CPU-only: todas las peticiones llevan options={"num_gpu": 0} para que
  ninguna capa se descargue a la GPU (este portátil tiene una RTX 4060 que
  NO se usa, para cumplir la restricción del enunciado).
"""
import threading
import time

import ollama
import psutil

OLLAMA_HOST = "http://localhost:11434"


def ollama_ram_mb() -> float:
    """Suma de working-set (MB) del servidor Ollama y su runner de inferencia.
    Desde Ollama ~0.30 el runner es un proceso llamado `llama-server`."""
    total = 0
    for p in psutil.process_iter(["name", "memory_info"]):
        try:
            name = (p.info["name"] or "").lower()
            if "ollama" in name or "llama-server" in name:
                total += p.info["memory_info"].rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return total / (1024 * 1024)


class RamMonitor:
    """Muestrea la RAM de ollama en segundo plano y recuerda el pico."""

    def __init__(self, interval: float = 0.2):
        self.interval = interval
        self.peak_mb = 0.0
        self._stop = threading.Event()
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
    """Tamaño del fichero GGUF según el registro local de Ollama."""
    for m in client.list()["models"]:
        if m["model"] == model:
            return m["size"] / (1024 * 1024)
    raise ValueError(f"Modelo no encontrado localmente: {model}")


def stop_model(model: str):
    """Descarga el modelo de RAM para que la siguiente medición parta de cero."""
    import subprocess
    subprocess.run(["ollama", "stop", model], capture_output=True)
    time.sleep(2)


def timed_generate(client: ollama.Client, model: str, prompt: str,
                   num_predict: int = 200, num_ctx: int = 2048,
                   system: str | None = None) -> dict:
    """Genera una respuesta CPU-only y devuelve métricas + texto."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    t0 = time.perf_counter()
    with RamMonitor() as mon:
        resp = client.chat(
            model=model,
            messages=messages,
            options={
                "num_gpu": 0,          # CPU-only (requisito del enunciado)
                "num_predict": num_predict,
                "num_ctx": num_ctx,
                "temperature": 0,      # determinista → reproducible
                "seed": 42,
            },
        )
    wall_s = time.perf_counter() - t0

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
