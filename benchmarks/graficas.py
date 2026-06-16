"""
graficas.py  —  Dibuja las dos gráficas del informe
===================================================
Lee measurements.csv y produce:
  - report/plot_quant.png : tamaño vs velocidad vs calidad (Parte A)
  - report/plot_kv.png    : contexto vs latencia y vs RAM (Parte B),
                            con la serie KV q8_0 superpuesta si existe (B.4)

Cómo se ejecuta:
  python graficas.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")            # modo sin ventana (solo guarda archivos)
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent   # raíz del proyecto (subimos desde benchmarks/)
OUT = ROOT / "report"
OUT.mkdir(exist_ok=True)

df = pd.read_csv(ROOT / "measurements.csv")

# ---------- Parte A: tamaño vs velocidad vs calidad ----------
a = df[df["notes"].str.startswith("PartA", na=False)]
if not a.empty:
    fig, ax1 = plt.subplots(figsize=(7, 4.2))
    x = a["file_size_mb"] / 1024                       # eje X: tamaño en GB
    ax1.plot(x, a["eval_tps"], "o-", color="tab:blue", label="tokens/s (gen)")
    ax1.set_xlabel("Tamaño del modelo (GB)")
    ax1.set_ylabel("tokens/s en generación", color="tab:blue")
    ax2 = ax1.twinx()                                  # segundo eje Y: calidad
    ax2.plot(x, a["quality_avg"], "s--", color="tab:red", label="calidad (0-3)")
    ax2.set_ylabel("calidad media (0-3)", color="tab:red")
    ax2.set_ylim(0, 3.2)
    for _, r in a.iterrows():                          # etiqueta cada punto
        ax1.annotate(r["quantization"], (r["file_size_mb"] / 1024, r["eval_tps"]),
                     textcoords="offset points", xytext=(0, 8), ha="center")
    ax1.set_title("llama3.2 3B en CPU: tamaño vs velocidad vs calidad")
    fig.tight_layout()
    fig.savefig(OUT / "plot_quant.png", dpi=150)
    print(f"OK {OUT / 'plot_quant.png'}")

# ---------- Parte B: contexto vs latencia y RAM ----------
b = df[df["notes"] == "PartB"]
if not b.empty:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2))
    # Dibuja una línea por tipo de KV cache (f16 y, si existe, q8_0).
    for kv, style in [("f16", "o-"), ("q8_0", "s--")]:
        s = b[b["kv_cache_type"] == kv].sort_values("context_length")
        if s.empty:
            continue
        ax1.plot(s["context_length"], s["wall_s"], style, label=f"KV {kv}")
        ax2.plot(s["context_length"], s["peak_ram_mb"] / 1024, style, label=f"KV {kv}")
    ax1.set_xlabel("Longitud de contexto (tokens)")
    ax1.set_ylabel("Latencia total (s)")
    ax1.set_title("Contexto vs latencia")
    ax1.legend()
    ax2.set_xlabel("Longitud de contexto (tokens)")
    ax2.set_ylabel("RAM pico de Ollama (GB)")
    ax2.set_title("Contexto vs RAM (crecimiento ~lineal del KV cache)")
    ax2.legend()
    fig.tight_layout()
    fig.savefig(OUT / "plot_kv.png", dpi=150)
    print(f"OK {OUT / 'plot_kv.png'}")
