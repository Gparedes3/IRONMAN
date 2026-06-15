"""Parte C.3 — Comparación con/sin RAG sobre 5 preguntas del corpus.

Las preguntas piden hechos concretos de la documentación de Ollama/llama.cpp
que un modelo de 3B no sabe con fiabilidad de memoria. Cada par de respuestas
se puntúa a mano con la misma rúbrica 0-3 de benchmarks/RUBRIC.md.

Uso:  python rag/compare_rag.py   ->  rag/compare_results.json
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rag import answer

QUESTIONS = [
    {
        "q": "Which environment variable changes the directory where Ollama stores its models?",
        "check": "OLLAMA_MODELS (docs/faq.md).",
    },
    {
        "q": "How do you allow Ollama to listen on all network interfaces instead of only localhost?",
        "check": "OLLAMA_HOST=0.0.0.0 (docs/faq.md).",
    },
    {
        "q": "According to the llama.cpp docs, what does the -ngl / --n-gpu-layers flag control?",
        "check": "Cuántas capas del modelo se descargan a la GPU.",
    },
    {
        "q": "How long does Ollama keep a model loaded in memory by default, and how can you change it?",
        "check": "5 minutos; keep_alive / OLLAMA_KEEP_ALIVE (docs/faq.md).",
    },
    {
        "q": "What file format does Ollama use for model weights and what is a Modelfile for?",
        "check": "GGUF; el Modelfile define modelo base, plantilla, system prompt y parámetros.",
    },
]


def main():
    results = []
    for item in QUESTIONS:
        q = item["q"]
        print(f"\nQ: {q}")
        row = {"question": q, "check": item["check"]}
        for mode, use_rag in [("with_rag", True), ("without_rag", False)]:
            t0 = time.perf_counter()
            r = answer(q, use_rag=use_rag)
            dt = round(time.perf_counter() - t0, 1)
            row[mode] = {"answer": r["answer"], "sources": r["sources"],
                         "latency_s": dt, "score": None}  # ← puntuar a mano
            print(f"  [{mode}] {dt}s: {r['answer'][:120]}...")
        results.append(row)

    out = Path(__file__).parent / "compare_results.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\nGuardado en {out} — puntuar con benchmarks/RUBRIC.md")


if __name__ == "__main__":
    main()
