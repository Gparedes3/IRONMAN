# Plan de ejecución IRONMAN — Jarvis local (Applied ML)

> Guía para **terminar** la asignación usando **Claude Code en tu portátil**.
> Tu repo ya tiene casi todo el código escrito y sin errores de sintaxis
> (verificado con `py_compile` en los 27 ficheros). Lo que falta **no es
> arreglar código roto**: es **ejecutar los experimentos con Ollama, puntuar
> con la rúbrica y rellenar resultados**. Esos números deben salir de TU
> hardware — nadie puede inventarlos por ti (integridad académica: "debes poder
> defender cada cifra").

---

## 0. Estado actual (qué hay hecho vs. qué falta)

| Parte | Código | Datos / resultados | Falta |
|---|---|---|---|
| **A** Cuantización | ✅ `benchmarks/bench_quant.py` | ⚠️ `measurements.csv` tiene velocidad/RAM/tamaño de las 3 cuantizaciones, pero **`quality_avg` vacío** y `quality_outputs.json` con `score: null` | Puntuar las 5 respuestas × 3 cuant. con la rúbrica; rellenar `quality_avg` |
| **B** KV cache | ✅ `benchmarks/bench_kv.py` + `run_kv_quant.ps1` | ⚠️ filas f16 (512/2048/8192/16384) hechas; **falta la fila KV q8_0** (B.4) | Correr `run_kv_quant.ps1` y anotar el ahorro |
| **C** RAG | ✅ `rag/` completo, índice `index.db` construido | ❌ **falta `rag/compare_results.json`** (5 preguntas con/sin RAG) | Correr `compare_rag.py` y puntuar |
| **D** MCP | ✅ `mcp_server/server.py` + cliente | ⚠️ `FAILURES.md` con la sección "prompts que fallan" **vacía** | Correr tests, documentar 2+ tareas E2E y fallos reales |
| **E** Evaluación | ✅ `evaluation/run_tests.py`, `test_set.json` (21 prompts, 5 categorías) | ❌ **falta `evaluation/results.json`** | Correr `run_tests.py` |
| **F** Reflexión | — | — | Escribir "límites honestos" + 2 mejoras (en el reporte) |
| **Gráficas** | ✅ `benchmarks/plots.py` | ❌ **faltan `report/plot_quant.png`, `plot_kv.png`** | Correr `plots.py` |
| **Reporte** | ✅ `report/report.md` (estructura IEEE) | ❌ **10 placeholders `{{...}}` sin rellenar** + abstract | Rellenar con tus datos, exportar a PDF |
| **D1 GitHub** | — | ❌ **la carpeta NO es repo git** | `git init` + push a GitHub |
| **D4 Vídeo** | — | ❌ falta | Grabar 3-5 min, enlace en README |

**Arreglo ya aplicado:** `ironman/config.py` tenía como modelo por defecto
`llama3.1` (incoherente con el proyecto). Lo cambié a
`llama3.2:3b-instruct-q4_K_M` para que un clon limpio sin `.env` no apunte al
modelo equivocado.

**Nota técnica:** NO añadas `rag/__init__.py`. Los imports funcionan por
manipulación de `sys.path` (`from rag import retrieve` resuelve a `rag/rag.py`);
un `__init__.py` haría ambiguo el import y lo rompería.

---

## 1. Orden de ejecución recomendado (en tu portátil)

Hazlo en este orden porque cada paso alimenta al siguiente (y al reporte):

```
setup.ps1  →  A (bench_quant + puntuar)  →  B (bench_kv + KV q8)
           →  C (compare_rag + puntuar)  →  E (run_tests)
           →  D (rellenar FAILURES.md con results.json)
           →  plots.py  →  rellenar report.md  →  PDF
           →  git init + push  →  grabar vídeo
```

Antes de nada, comprobación de entorno (1 comando):

```powershell
cd C:\Users\guill\OneDrive\Documentos\IRONMAN
.\setup.ps1
ollama list          # deben verse las 3 cuantizaciones + nomic-embed-text
.\.venv\Scripts\python.exe jarvis.py   # prueba humo: "Abre la calculadora"
```

---

## 2. Cómo usar Claude Code para cada parte

Para cada parte tienes: **(a)** el comando que corres tú, **(b)** un *prompt*
para pegar en Claude Code cuando algo falle o haya que rellenar, y **(c)** la
pregunta de defensa que el profe puede hacerte.

### Parte A — Cuantización (20 pts)

```powershell
.\.venv\Scripts\python.exe benchmarks\bench_quant.py
.\.venv\Scripts\python.exe benchmarks\eval_code.py
```

Luego **puntúa a mano** las 15 respuestas (`benchmarks/results/quality_outputs.json`)
con `benchmarks/RUBRIC.md` (0-3) y escribe la media en la columna `quality_avg`
de cada fila PartA de `measurements.csv`.

**Prompt para Claude Code (puntuación asistida):**
> Lee `benchmarks/results/quality_outputs.json` y `benchmarks/RUBRIC.md`. Para
> cada respuesta propón una puntuación 0-3 justificándola contra el campo
> `check`, y para el prompt de código ejecuta la función con 5 casos. Devuélveme
> una tabla quant × prompt con la nota sugerida y la media por cuantización.
> NO inventes respuestas: usa solo el texto que ya está en el JSON. Yo reviso y
> decido la nota final.

**Defensa — "¿Por qué Q4_K_M y no Q5_K_M?":** porque en tu tabla Q4_K_M da el
mejor punto: ~la mitad de RAM/tamaño que Q8 con caída de calidad mínima, y Q3
ya degrada. Ten los números de `measurements.csv` a mano.

### Parte B — KV cache (10 pts)

```powershell
.\.venv\Scripts\python.exe benchmarks\bench_kv.py     # f16 (ya lo tienes)
.\benchmarks\run_kv_quant.ps1                          # KV q8_0 (B.4 — FALTA)
```

**Defensa — "¿Cuánto pesa tu KV cache a 8K?":** del propio reporte, KV f16 crece
~linealmente (~57 MB a 512 → ~1.79 GB a 16 384 tokens). A 8K son ~0.9 GB.
Sabe explicar por qué: 2 (K y V) × capas × dim × tokens × bytes.

### Parte C — RAG (20 pts)

```powershell
.\.venv\Scripts\python.exe rag\compare_rag.py     # genera rag/compare_results.json
```

Puntúa las 5 preguntas con/sin RAG con la misma rúbrica.

**Prompt para Claude Code (justificar corpus + comparación):**
> Tengo `rag/compare_results.json` con 5 preguntas respondidas con y sin RAG.
> Ayúdame a puntuar cada par 0-3 según `benchmarks/RUBRIC.md` y a redactar 4-5
> frases para la sección C del reporte explicando dónde RAG ayuda y dónde no.
> Usa solo el contenido del JSON.

### Parte D — MCP (20 pts)

Las 2+ tareas E2E que **requieren** herramienta (graba estas en el vídeo):
1. *"Busca en los docs cómo cambiar dónde Ollama guarda los modelos y resume"*
   → `search_docs`.
2. *"Resume mis últimos 5 correos"* → `fetch_recent_emails`.
3. Multi-paso: *"Busca X en los docs y mándamelo por correo"* → `search_docs` + `send_email`.

```powershell
.\.venv\Scripts\python.exe evaluation\run_tests.py     # produce results.json
```

**Prompt para Claude Code (rellenar FAILURES.md con datos reales):**
> A partir de `evaluation/results.json`, completa la sección "Prompts que
> fallan (y por qué)" de `mcp_server/FAILURES.md`: lista los tests con verdict
> `fail`/`partial`, qué herramienta esperaba vs. cuál invocó, y la causa
> probable. No inventes: cita los `id` reales del JSON.

**Defensa — "Muéstrame un caso donde falla tu tool calling":** ten localizado en
`results.json` un `fail` de categoría multi-step o adversarial y explica por qué
(modelos 3B son literalistas / encadenan mal 2 tools — ya está en FAILURES.md).

### Parte E — Evaluación (15 pts)

Ya cubierto por `run_tests.py` (arriba). Imprime tasa de éxito global, por
categoría y latencia media, y guarda `results.json`. Para enviar correos de
verdad en vez de dry-run: `run_tests.py --live` (cuidado, manda emails).

### Parte F — Reflexión (10 pts)

**Prompt para Claude Code:**
> Con `evaluation/results.json` y `mcp_server/FAILURES.md`, ayúdame a redactar la
> sección F del reporte: (1) "Límites honestos" citando 2-3 ejemplos concretos
> con su `id` donde Jarvis falla, comparando cualitativamente con un LLM en la
> nube; (2) dos mejoras concretas factibles con el doble de RAM o una GPU
> pequeña (p. ej. modelo 7-8B Q4, KV cache mayor, reranker en el RAG). Tono
> técnico, honesto.

---

## 3. Gráficas + reporte

```powershell
.\.venv\Scripts\python.exe benchmarks\plots.py    # → report/plot_quant.png, plot_kv.png
```

Rellena los 10 placeholders de `report/report.md`:
`{{ABSTRACT_RESULT_SENTENCE}}`, `{{N_CHUNKS}}`, `{{A_ANALYSIS}}`, `{{B_TABLE}}`,
`{{B_ANALYSIS}}`, `{{C_TABLE}}`, `{{C_ANALYSIS}}`, `{{D_FAILURES_SUMMARY}}`,
`{{E_TABLE}}`, `{{E_ANALYSIS}}`, `{{F_LIMITS}}`.

`{{N_CHUNKS}}` = nº de filas en el índice:
```powershell
.\.venv\Scripts\python.exe -c "import sqlite3;print(sqlite3.connect('rag/index.db').execute('select count(*) from chunks').fetchone())"
```

**Exportar a PDF (4-6 págs, IEEE):**
```powershell
pandoc report\report.md -o report\report.pdf
```
Si no tienes pandoc, abre `report.md` en VS Code y usa la extensión *Markdown PDF*.

> En Cowork puedo ayudarte a montar el PDF final con plantilla limpia usando la
> skill `pdf`/`docx` una vez tengas el `report.md` relleno. Súbeme el `.md`
> completo y lo dejo presentable.

**No olvides** la **"Declaración de uso de IA"** al final del reporte (qué
asistente, qué secciones, cómo). Es obligatoria; omitirla cuenta como plagio.

---

## 4. GitHub (D1) — convertir la carpeta en repo

Tu carpeta **no es un repo git todavía**. En Claude Code / PowerShell:

```powershell
cd C:\Users\guill\OneDrive\Documentos\IRONMAN
git init
git add -A
git status            # confirma que .venv/ y .env NO aparecen (están en .gitignore)
git commit -m "IRONMAN: Jarvis local (partes A-F)"
gh repo create ironman-jarvis-local --public --source=. --push
```

⚠️ Antes del primer commit verifica que `.gitignore` excluye `.venv/`, `.env`,
`__pycache__/` y `rag/index.db` si pesa mucho. **Nunca subas `.env`** (tiene tu
app password de Gmail).

---

## 5. Vídeo demo (D4)

3-5 min mostrando **3 tareas distintas en vivo**: (1) pregunta RAG sobre los
docs, (2) resumen de correos (`fetch_recent_emails`), (3) tarea multi-paso
(buscar en docs + enviar correo). Sube a YouTube/Drive y pon el enlace en el
README (sustituye `enlace pendiente`).

---

## 6. Bonus (hasta +10)

Lo más rentable con tu base: **segunda familia de modelos** (Qwen2.5-7B o
Phi-4-mini) corriendo `bench_quant.py` con esos modelos y una sección de
comparación. Ya tienes voz (Whisper+TTS) guardada en `bonus/` — reactívala y documéntala como
bonus parcial.

---

## 7. Checklist final (mapeado a la rúbrica /100)

- [ ] A: 3 cuant. medidas + `quality_avg` rellenado + gráfica + análisis (20)
- [ ] B: 4 contextos + gráficas + fila KV q8 con ahorro (10)
- [ ] C: `compare_results.json` + puntuación con/sin RAG + justificación corpus (20)
- [ ] D: servidor MCP + 2 tareas E2E + `FAILURES.md` con fallos reales (20)
- [ ] E: `results.json` + tablas éxito/latencia por categoría (15)
- [ ] F: límites honestos con evidencia + 2 mejoras (10)
- [ ] Repro: `setup.ps1` un comando + versiones fijadas + repo git (5)
- [ ] Reporte PDF 4-6 págs sin placeholders + Declaración de uso de IA
- [ ] Vídeo 3-5 min enlazado en README
