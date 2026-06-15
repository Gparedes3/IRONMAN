"""Valida el prompt de código de la Parte A: extrae la función is_balanced
de cada respuesta en results/quality_outputs.json y la ejecuta sobre 5 casos.

Uso:  python benchmarks/eval_code.py
"""
import json
import re
from pathlib import Path

CASES = [
    ("([]{})", True),
    ("(]", False),
    ("", True),
    ("((()))[]{}", True),
    ("([)]", False),
]

outputs = json.loads(
    (Path(__file__).parent / "results" / "quality_outputs.json")
    .read_text(encoding="utf-8"))

for quant, answers in outputs.items():
    for item in answers:
        if item["id"] != "code":
            continue
        m = re.search(r"```(?:python)?\n(.*?)```", item["answer"], re.S)
        code = m.group(1) if m else item["answer"]
        ns = {}
        try:
            exec(code, ns)  # código generado por el modelo, ejecución local
            fn = ns["is_balanced"]
            passed = sum(1 for s, exp in CASES if fn(s) == exp)
            print(f"{quant}: is_balanced pasa {passed}/{len(CASES)} casos")
        except Exception as e:
            print(f"{quant}: el código no ejecuta -> {type(e).__name__}: {e}")
