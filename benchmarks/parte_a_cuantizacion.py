"""
parte_a_cuantizacion.py  —  PARTE A del trabajo
================================================
Estudia cómo afecta la CUANTIZACIÓN (comprimir el modelo a menos bits).

Baja el MISMO modelo (llama3.2 3B) en tres niveles de compresión y, para cada
uno, mide cuatro cosas:
  1. tamaño del fichero del modelo
  2. RAM pico durante la inferencia
  3. velocidad (tokens/segundo) en una generación fija de 200 tokens (3 veces)
  4. calidad: respuestas a 5 preguntas que TÚ puntúas luego a mano (0-3)

Qué deja escrito:
  - measurements.csv            -> una fila por cuantización (se va anexando)
  - resultados/quality_outputs.json -> las 5 respuestas de cada modelo, con
                                       "score": null para que las puntúes tú.

Cómo se ejecuta (en tu portátil, con Ollama abierto):
  python parte_a_cuantizacion.py
"""
import csv
import json
import statistics
from pathlib import Path

import ollama

# Importamos las funciones de medición compartidas (el "cómo se mide").
from medir_comun import OLLAMA_HOST, model_file_size_mb, stop_model, timed_generate

# ----------------------------------------------------------------------------
# Las 5 preguntas estandarizadas de calidad. Cada una trae "check" = la
# respuesta correcta, que usas como guía al puntuar con rubrica.md.
# ----------------------------------------------------------------------------
QUALITY_PROMPTS = [
    {"id": "math", "category": "matemáticas",
     "prompt": ("Un tren sale a las 14:30 y llega a las 18:05. Se detiene 12 "
                "minutos en total. ¿Cuál es el tiempo real en movimiento, en "
                "minutos? Muestra brevemente tu razonamiento."),
     "check": "Respuesta correcta: 215 - 12 = 203 minutos."},
    {"id": "code", "category": "código",
     "prompt": ("Escribe una función de Python `is_balanced(s)` que devuelva True "
                "si los paréntesis (), [], {} de la cadena están balanceados. "
                "Devuelve solo el código."),
     "check": ("Debe usar una pila y devolver not stack al final. Se valida "
               "ejecutándola sobre 5 casos.")},
    {"id": "summary", "category": "resumen",
     "prompt": ("Resume en exactamente 3 viñetas: 'La arquitectura Transformer "
                "reemplazó la recurrencia por la auto-atención, permitiendo el "
                "entrenamiento paralelo sobre secuencias. Su diseño codificador-"
                "decodificador usa atención multi-cabeza y codificaciones "
                "posicionales. Escalar estos modelos llevó a los LLM modernos, "
                "pero el coste de inferencia crece con la longitud del contexto "
                "porque la atención es cuadrática y la caché KV crece "
                "linealmente.'"),
     "check": "3 viñetas; conservar auto-atención, multi-cabeza, caché KV."},
    {"id": "factual", "category": "memoria factual",
     "prompt": ("¿En qué año se lanzó por primera vez el lenguaje de "
                "programación Python y quién lo creó? Responde en una sola frase."),
     "check": "1991, Guido van Rossum."},
    {"id": "reasoning", "category": "razonamiento",
     "prompt": ("Ana es más alta que Berta. Carla es más baja que Berta. Diana "
                "es más alta que Ana. ¿Quién es la segunda más alta? Explica en "
                "dos frases."),
     "check": "Ana (orden: Diana > Ana > Berta > Carla)."},
]

# Los tres niveles de cuantización del mismo modelo base.
MODELS = [
    ("llama3.2:3b-instruct-q8_0", "Q8_0"),    # 8 bits: más grande y preciso
    ("llama3.2:3b-instruct-q4_K_M", "Q4_K_M"),  # 4 bits: el equilibrio elegido
    ("llama3.2:3b-instruct-q3_K_M", "Q3_K_M"),  # 3 bits: más pequeño, peor
]

# Prompt fijo para medir velocidad: pide texto largo para que no pare antes
# de los 200 tokens.
SPEED_PROMPT = ("Explica en detalle cómo funciona un refrigerador, cubriendo el "
                "compresor, el condensador, la válvula de expansión y el evaporador.")
SPEED_RUNS = 3      # se mide 3 veces y se promedia
NUM_CTX = 2048      # contexto fijo en la Parte A (la Parte B lo varía)

ROOT = Path(__file__).resolve().parent.parent   # raíz del proyecto (subimos desde benchmarks/)
CSV_PATH = ROOT / "measurements.csv"
RESULTS_DIR = ROOT / "resultados"

# Columnas del CSV (las mismas para Parte A y B).
CSV_FIELDS = ["model", "quantization", "context_length", "file_size_mb",
              "peak_ram_mb", "prompt_eval_tps", "eval_tps", "wall_s",
              "prompt_tokens", "gen_tokens", "kv_cache_type", "quality_avg",
              "notes"]


def append_row(row: dict):
    """Añade una fila al final de measurements.csv (crea cabecera si no existe)."""
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
        stop_model(model)  # empezar con la RAM limpia

        # --- 1) Velocidad: 200 tokens fijos, 3 repeticiones ---
        speed_runs = []
        for i in range(SPEED_RUNS):
            r = timed_generate(client, model, SPEED_PROMPT,
                               num_predict=200, num_ctx=NUM_CTX)
            speed_runs.append(r)
            print(f"  run {i+1}: {r['eval_tps']} tok/s gen | "
                  f"{r['prompt_eval_tps']} tok/s prefill | "
                  f"RAM pico {r['peak_ram_mb']} MB")
        eval_tps = statistics.mean(r["eval_tps"] for r in speed_runs)
        prompt_tps = statistics.mean(r["prompt_eval_tps"] for r in speed_runs)
        peak_ram = max(r["peak_ram_mb"] for r in speed_runs)
        wall = statistics.mean(r["wall_s"] for r in speed_runs)

        # --- 2) Calidad: las 5 preguntas (se puntúan a mano después) ---
        quality_outputs[quant] = []
        for q in QUALITY_PROMPTS:
            r = timed_generate(client, model, q["prompt"],
                               num_predict=512, num_ctx=NUM_CTX)
            quality_outputs[quant].append({
                "id": q["id"], "category": q["category"],
                "prompt": q["prompt"], "check": q["check"],
                "answer": r["text"], "score": None,  # <-- lo pones tú con rubrica.md
            })
            print(f"  calidad [{q['id']}] generado")

        # --- 3) Guardar la fila de este modelo en el CSV ---
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

    # Guardar las respuestas de calidad para puntuarlas a mano.
    out = RESULTS_DIR / "quality_outputs.json"
    out.write_text(json.dumps(quality_outputs, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\nRespuestas de calidad -> {out}")
    print(f"Métricas -> {CSV_PATH}")
    print("Siguiente paso: puntuar 0-3 con rubrica.md y escribir quality_avg.")


if __name__ == "__main__":
    main()
