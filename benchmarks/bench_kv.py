"""Parte B — Experimento de KV cache.

Mide tokens/s (prefill y generación) y RAM pico con prompts que llenan
contextos de 512, 2048, 8192 y 16384 tokens, usando el mejor modelo de la
Parte A. El tamaño teórico del KV cache crece linealmente con el contexto:

    KV bytes = 2 (K y V) * n_layers * n_kv_heads * head_dim * ctx * bytes/elem

Para llama3.2 3B (28 capas, 8 KV heads, head_dim 128, f16):
    2 * 28 * 8 * 128 * ctx * 2 bytes = 112 KB/token  →  ~1.75 GB a 16K.

Uso:
  python benchmarks/bench_kv.py                 # KV cache f16 (por defecto)
  python benchmarks/bench_kv.py --kv q8_0       # etiqueta filas como q8_0
                                                # (el servidor debe arrancarse
                                                #  con run_kv_quant.ps1)
"""
import argparse
import csv
import sys
from pathlib import Path

import ollama

sys.path.insert(0, str(Path(__file__).parent))
from common import OLLAMA_HOST, stop_model, timed_generate

MODEL = "llama3.2:3b-instruct-q4_K_M"   # mejor equilibrio según Parte A
CONTEXTS = [512, 2048, 8192, 16384]

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "measurements.csv"
CSV_FIELDS = ["model", "quantization", "context_length", "file_size_mb",
              "peak_ram_mb", "prompt_eval_tps", "eval_tps", "wall_s",
              "prompt_tokens", "gen_tokens", "kv_cache_type", "quality_avg",
              "notes"]

# Párrafo neutro (~95 palabras ≈ 125 tokens) que se repite hasta llenar
# el contexto objetivo. El recuento real de tokens lo devuelve Ollama
# (prompt_eval_count) y se guarda en el CSV.
FILLER = (
    "The history of mechanical refrigeration began in the eighteenth century "
    "when early experimenters observed that evaporating volatile liquids "
    "absorbs heat from the surroundings. Throughout the nineteenth century "
    "engineers refined vapor-compression cycles, introducing safer working "
    "fluids and more reliable compressors. By the twentieth century the "
    "domestic refrigerator had transformed food storage, public health and "
    "urban life, enabling households to keep perishable goods for days "
    "instead of hours. Modern units add electronic control, variable speed "
    "compressors and improved insulation, reducing energy consumption while "
    "increasing reliability and capacity for ordinary families everywhere. "
)
TOKENS_PER_FILLER = 125  # aproximado; el valor real se mide y se registra


def build_prompt(target_ctx: int) -> str:
    """Prompt que ocupa ~(target_ctx - 250) tokens, dejando sitio para
    la plantilla de chat y los 200 tokens de generación."""
    target_tokens = max(target_ctx - 250, 100)
    reps = max(target_tokens // TOKENS_PER_FILLER, 1)
    return (FILLER * reps
            + "\n\nSummarize the text above in one short paragraph.")


def append_row(row: dict):
    new_file = not CSV_PATH.exists()
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if new_file:
            w.writeheader()
        w.writerow(row)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kv", default="f16", choices=["f16", "q8_0"],
                    help="Etiqueta del tipo de KV cache del servidor en uso")
    ap.add_argument("--contexts", type=int, nargs="*", default=CONTEXTS)
    args = ap.parse_args()

    client = ollama.Client(host=OLLAMA_HOST)
    for ctx in args.contexts:
        print(f"\n=== ctx={ctx} (KV {args.kv}) ===")
        stop_model(MODEL)  # recargar para que num_ctx y RAM partan de cero
        prompt = build_prompt(ctx)
        r = timed_generate(client, MODEL, prompt,
                           num_predict=200, num_ctx=ctx)
        print(f"  prompt real: {r['prompt_tokens']} tokens | "
              f"prefill {r['prompt_eval_tps']} tok/s | "
              f"gen {r['eval_tps']} tok/s | "
              f"RAM pico {r['peak_ram_mb']} MB | {r['wall_s']} s")
        append_row({
            "model": MODEL, "quantization": "Q4_K_M", "context_length": ctx,
            "file_size_mb": "", "peak_ram_mb": r["peak_ram_mb"],
            "prompt_eval_tps": r["prompt_eval_tps"], "eval_tps": r["eval_tps"],
            "wall_s": r["wall_s"], "prompt_tokens": r["prompt_tokens"],
            "gen_tokens": r["gen_tokens"], "kv_cache_type": args.kv,
            "quality_avg": "", "notes": "PartB",
        })
    stop_model(MODEL)
    print(f"\nFilas anexadas a {CSV_PATH}")


if __name__ == "__main__":
    main()
