# Rúbrica de calidad 0–3 (Parte A.3 y C.3)

Cada respuesta del modelo a los 5 prompts estandarizados (matemáticas, código,
resumen, memoria factual, razonamiento) se puntúa con esta escala. La misma
rúbrica se reutiliza en la Parte C para comparar con/sin RAG.

| Puntos | Criterio |
|--------|----------|
| **3** | Respuesta **correcta y completa**. Cumple además las restricciones de formato del prompt (p. ej. "exactamente 3 bullets", "solo código", "una frase"). En código: la función pasa los 5 casos de prueba. |
| **2** | Respuesta **correcta en lo esencial** pero con un defecto menor: formato incumplido, verbosidad innecesaria, un caso borde fallido en código, o un paso intermedio erróneo que no cambia la conclusión. |
| **1** | Respuesta **parcialmente correcta**: la idea general va bien encaminada pero el resultado final es erróneo (p. ej. aritmética mal hecha, código que no compila, conclusión equivocada del razonamiento). |
| **0** | Respuesta **incorrecta, irrelevante o alucinada**; o el modelo se niega / divaga sin responder. |

## Procedimiento

1. `bench_quant.py` genera las respuestas con `temperature=0, seed=42`
   (deterministas) y las guarda en `results/quality_outputs.json`.
2. Un humano (el autor) puntúa cada respuesta con la tabla anterior usando el
   campo `check` de `prompts.py` como clave de corrección.
3. Para el prompt de código, además se ejecuta la función generada sobre
   5 casos de prueba (`eval_code.py` lo automatiza).
4. La media de los 5 prompts es la columna `quality_avg` de `measurements.csv`.

Puntuar con clave de corrección + ejecución real del código reduce la
subjetividad; aun así dos defectos conocidos son: (a) un solo corrector,
(b) n=5 prompts. Ambos se discuten en el reporte (Parte F).
