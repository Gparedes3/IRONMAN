"""Genera las gráficas del reporte a partir de measurements.csv.

  - plot_quant.png : tamaño vs tok/s vs calidad (Parte A.4)
  - plot_kv.png    : contexto vs latencia y vs RAM (Parte B.3),
                     con la serie KV q8_0 superpuesta si existe (B.4)

Uso:  python benchmarks/plots.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "report"
OUT.mkdir(exist_ok=True)

df = pd.read_csv(ROOT / "measurements.csv")

# ---------- Parte A ----------
a = df[df["notes"].str.startswith("PartA", na=False)]
if not a.empty:
    fig, ax1 = plt.subplots(figsize=(7, 4.2))
    x = a["file_size_mb"] / 1024
    ax1.plot(x, a["eval_tps"], "o-", color="tab:blue", label="tokens/s (gen)")
    ax1.set_xlabel("Tamaño del modelo (GB)")
    ax1.set_ylabel("tokens/s en generación", color="tab:blue")
    ax2 = ax1.twinx()
    ax2.plot(x, a["quality_avg"], "s--", color="tab:red", label="calidad (0-3)")
    ax2.set_ylabel("calidad media (rúbrica 0-3)", color="tab:red")
    ax2.set_ylim(0, 3.2)
    for _, r in a.iterrows():
        ax1.annotate(r["quantization"], (r["file_size_mb"] / 1024, r["eval_tps"]),
                     textcoords="offset points", xytext=(0, 8), ha="center")
    ax1.set_title("llama3.2 3B en CPU: tamaño vs velocidad vs calidad")
    fig.tight_layout()
    fig.savefig(OUT / "plot_quant.png", dpi=150)
    print(f"OK {OUT / 'plot_quant.png'}")

# ---------- Parte B ----------
b = df[df["notes"] == "PartB"]
if not b.empty:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2))
    for kv, style in [("f16", "o-"), ("q8_0", "s--")]:
        s = b[b["kv_cache_type"] == kv].sort_values("context_length")
        if s.empty:
            continue
        ax1.plot(s["context_length"], s["wall_s"], style, label=f"KV {kv}")
        ax2.plot(s["context_length"], s["peak_ram_mb"] / 1024, style,
                 label=f"KV {kv}")
    ax1.set_xlabel("Longitud de contexto (tokens)")
    ax1.set_ylabel("Latencia total (s, prompt lleno + 200 tokens)")
    ax1.set_title("Contexto vs latencia")
    ax1.legend()
    ax2.set_xlabel("Longitud de contexto (tokens)")
    ax2.set_ylabel("RAM pico de Ollama (GB)")
    ax2.set_title("Contexto vs RAM (crecimiento ~lineal del KV cache)")
    ax2.legend()
    fig.tight_layout()
    fig.savefig(OUT / "plot_kv.png", dpi=150)
    print(f"OK {OUT / 'plot_kv.png'}")
