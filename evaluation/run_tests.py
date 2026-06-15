"""Parte E — Runner automático del test set.

Ejecuta evaluation/test_set.json contra el Jarvis completo (LLM local +
herramientas MCP) y registra por test: success/partial/fail, latencia y
tokens consumidos. Imprime tablas globales y por categoría y guarda el
detalle en evaluation/results.json.

Por defecto las herramientas CON EFECTOS (enviar correo, abrir apps/webs) se
ejecutan en seco: se registra la llamada y se devuelve un éxito simulado.
Así el test mide la FIABILIDAD del tool calling sin enviar 21 correos reales.
Usa --live para ejecutarlas de verdad.

Criterio de puntuación (automático):
  success : se invocaron todas las tools_required, ninguna forbidden,
            y (si hay keywords_any) alguna aparece en la respuesta.
  partial : la mitad de las condiciones (p. ej. tool correcta pero respuesta
            sin el dato, o dato correcto sin usar la tool requerida).
  fail    : lo demás.

Uso:  python evaluation/run_tests.py [--live] [--only chat,rag]
"""
import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ironman.llm import LLM
from ironman.mcp_client import MCPClient

SIDE_EFFECT_TOOLS = {"send_email", "open_app", "open_website", "web_search"}


def grade(test: dict, answer: str, tools_called: list[str]) -> str:
    exp = test["expected"]
    required = set(exp.get("tools_required", []))
    forbidden = set(exp.get("tools_forbidden", []))
    keywords = exp.get("keywords_any", [])

    called = set(tools_called)
    tools_ok = required.issubset(called)
    clean_ok = not (called & forbidden)
    text_ok = (not keywords) or any(k.lower() in answer.lower() for k in keywords)

    if tools_ok and clean_ok and text_ok:
        return "success"
    if (tools_ok and clean_ok) or (text_ok and clean_ok):
        return "partial"
    return "fail"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true",
                    help="Ejecutar de verdad las tools con efectos secundarios")
    ap.add_argument("--only", default="",
                    help="Lista de categorías separadas por comas")
    args = ap.parse_args()
    only = {c.strip() for c in args.only.split(",") if c.strip()}

    tests = json.loads((Path(__file__).parent / "test_set.json")
                       .read_text(encoding="utf-8"))["tests"]
    if only:
        tests = [t for t in tests if t["category"] in only]

    print("Conectando al servidor MCP...")
    mcp = MCPClient()
    handlers = mcp.handlers()
    if not args.live:
        for name in SIDE_EFFECT_TOOLS & set(handlers):
            handlers[name] = (lambda _n: lambda **kw:
                              f"[dry-run] {_n} ejecutada con {kw}. Éxito.")(name)

    llm = LLM(tools=mcp.ollama_tools(), tool_handlers=handlers)

    results = []
    for t in tests:
        llm.reset()
        tokens_before = llm.total_tokens
        t0 = time.perf_counter()
        try:
            answer = llm.ask(t["prompt"])
        except Exception as e:
            answer = f"[EXCEPTION] {e}"
        latency = round(time.perf_counter() - t0, 1)
        verdict = grade(t, answer, llm.last_tools_called)
        results.append({
            "id": t["id"], "category": t["category"], "prompt": t["prompt"],
            "verdict": verdict, "latency_s": latency,
            "tokens": llm.total_tokens - tokens_before,
            "tools_called": llm.last_tools_called, "answer": answer,
        })
        print(f"  [{verdict.upper():7}] {t['id']} ({latency}s, "
              f"tools={llm.last_tools_called})")

    mcp.close()

    # ---- Tablas resumen ----
    by_cat = defaultdict(list)
    for r in results:
        by_cat[r["category"]].append(r)

    print("\n================ RESUMEN ================")
    header = f"{'categoría':<12}{'n':>3}{'success':>9}{'partial':>9}{'fail':>6}{'éxito %':>9}{'lat. media':>12}"
    print(header)
    total_ok = 0
    for cat, rs in by_cat.items():
        s = sum(1 for r in rs if r["verdict"] == "success")
        p = sum(1 for r in rs if r["verdict"] == "partial")
        f = sum(1 for r in rs if r["verdict"] == "fail")
        lat = sum(r["latency_s"] for r in rs) / len(rs)
        total_ok += s
        print(f"{cat:<12}{len(rs):>3}{s:>9}{p:>9}{f:>6}{100*s/len(rs):>8.0f}%{lat:>10.1f}s")
    lat_all = sum(r["latency_s"] for r in results) / len(results)
    tok_all = sum(r["tokens"] for r in results)
    print("-" * len(header))
    print(f"{'TOTAL':<12}{len(results):>3}{total_ok:>9}{'':>9}{'':>6}"
          f"{100*total_ok/len(results):>8.0f}%{lat_all:>10.1f}s")
    print(f"Tokens consumidos en total: {tok_all}")

    out = Path(__file__).parent / "results.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\nDetalle guardado en {out}")


if __name__ == "__main__":
    main()
