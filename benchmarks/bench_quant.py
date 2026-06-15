"""Parte A — Estudio de cuantización.

Para cada nivel de cuantización del MISMO modelo base (llama3.2 3B) mide:
  - tamaño de fichero (GGUF, según registro de Ollama)
  - RAM pico de los procesos ollama durante la inferencia
  - tokens/s en una completación fija de 200 tokens (3 repeticiones, media)
  - respuestas a los 5 prompts de calidad (se puntúan a mano con RUBRIC.md)

Salida:
  - results/quality_outputs.json  (respuestas para puntuar)
  - measurements.csv              (una fila por configuración, se va anexando)

Uso:  python benchmarks/bench_quant.py
"""
import csv
import json
import statistics
import sys
from pathlib import Path

import ollama

sys.path.insert(0, str(Path(__file__).parent))
from common import OLLAMA_HOST, model_file_size_mb, stop_model, timed_generate
from prompts import QUALITY_PROMPTS

MODELS = [
    ("llama3.2:3b-instruct-q8_0", "Q8_0"),
    ("llama3.2:3b-instruct-q4_K_M", "Q4_K_M"),
    ("llama3.2:3b-instruct-q3_K_M", "Q3_K_M"),
]

# Prompt fijo para la medición de velocidad: pide texto largo y neutro para
# que el modelo no pare antes de los 200 tokens (num_predict los corta ahí).
SPEED_PROMPT = ("Explain in detail how a refrigerator works, covering the "
                "compressor, condenser, expansion valve and evaporator.")
SPEED_RUNS = 3
NUM_CTX = 2048  # contexto fijo en la Parte A; la Parte B lo varía

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "measurements.csv"
RESULTS_DIR = Path(__file__).parent / "results"
CSV_FIELDS = ["model", "quantization", "context_length", "file_size_mb",
              "peak_ram_mb", "prompt_eval_tps", "eval_tps", "wall_s",
              "prompt_tokens", "gen_tokens", "kv_cache_type", "quality_avg",
              "notes"]


def append_row(row: dict):
    new_file = not CSV_PATH.exists()
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if new_file:
            w.writeheader()
        w.writerow(row)


def main():
    client = ollama.Client(host=OLLAMA_HOST)
    RESULTS_DIR.mkdir(exist_ok=True)
    quality_outputs = {}

    for model, quant in MODELS:
        print(f"\n=== {model} ({quant}) ===")
        size_mb = model_file_size_mb(client, model)
        print(f"  Tamaño de fichero: {size_mb:.0f} MB")
        stop_model(model)  # partir de RAM limpia

        # --- Velocidad: 200 tokens fijos, 3 repeticiones ---
        speed_runs = []
        for i in range(SPEED_RUNS):
            r = timed_generate(client, model, SPEED_PROMPT,
                               num_predict=200, num_ctx=NUM_CTX)
            speed_runs.append(r)
            print(f"  run {i+1}: {r['eval_tps']} tok/s (gen), "
                  f"{r['prompt_eval_tps']} tok/s (prefill), "
                  f"RAM pico {r['peak_ram_mb']} MB")
        eval_tps = statistics.mean(r["eval_tps"] for r in speed_runs)
        prompt_tps = statistics.mean(r["prompt_eval_tps"] for r in speed_runs)
        peak_ram = max(r["peak_ram_mb"] for r in speed_runs)
        wall = statistics.mean(r["wall_s"] for r in speed_runs)

        # --- Calidad: 5 prompts estandarizados ---
        quality_outputs[quant] = []
        for q in QUALITY_PROMPTS:
            r = timed_generate(client, model, q["prompt"],
                               num_predict=512, num_ctx=NUM_CTX)
            quality_outputs[quant].append({
                "id": q["id"], "category": q["category"],
                "prompt": q["prompt"], "check": q["check"],
                "answer": r["text"], "score": None,  # ← puntuar a mano
            })
            print(f"  calidad [{q['id']}] generado ({r['gen_tokens']} tokens)")

        append_row({
            "model": model, "quantization": quant, "context_length": NUM_CTX,
            "file_size_mb": round(size_mb, 1), "peak_ram_mb": peak_ram,
            "prompt_eval_tps": round(prompt_tps, 2),
            "eval_tps": round(eval_tps, 2), "wall_s": round(wall, 2),
            "prompt_tokens": speed_runs[0]["prompt_tokens"],
            "gen_tokens": speed_runs[0]["gen_tokens"],
            "kv_cache_type": "f16", "quality_avg": "",  # se rellena tras puntuar
            "notes": f"PartA speed={SPEED_RUNS} runs avg, temp=0 seed=42",
        })
        stop_model(model)

    out = RESULTS_DIR / "quality_outputs.json"
    out.write_text(json.dumps(quality_outputs, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\nRespuestas de calidad guardadas en {out}")
    print(f"Métricas anexadas a {CSV_PATH}")
    print("Siguiente paso: puntuar con RUBRIC.md y rellenar quality_avg.")


if __name__ == "__main__":
    main()
