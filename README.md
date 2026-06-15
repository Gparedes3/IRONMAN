# IRONMAN — Jarvis local (Applied ML: Local LLM Systems)

Asistente personal **100% local** en modo texto: responde con un LLM pequeño
servido por Ollama (CPU-only), recupera información de un corpus técnico vía
**RAG**, y ejecuta herramientas (correo, control del PC, búsqueda en docs)
expuestas con un servidor **MCP** propio. Sin ninguna API de LLM en la nube.

> Proyecto para *Applied Machine Learning — Local LLM Systems*
> ("Build Your Own Local Jarvis"). Reporte técnico en
> [`report/report.md`](report/report.md). Plan de ejecución en
> [`PLAN_IRONMAN.md`](PLAN_IRONMAN.md).
> Vídeo de demo: [📹 enlace pendiente](#demo).

## Arquitectura

![Arquitectura del sistema](docs/img/arquitectura.png)

El usuario interactúa por texto con `jarvis.py`, que orquesta la inferencia
local (Ollama), la llamada a herramientas (MCP) y la recuperación (RAG).
Ningún componente de inferencia sale a la nube.

<details>
<summary>Diagramas de los subsistemas (RAG y MCP)</summary>

**Pipeline RAG** — indexado offline + consulta online, embeddings 100% locales:

![Pipeline RAG](docs/img/flujo_rag.png)

**Llamada a herramienta vía MCP** — el LLM decide, el cliente MCP ejecuta, el
resultado vuelve al modelo:

![Flujo MCP](docs/img/flujo_mcp.png)

</details>

| Componente | Tecnología (local) |
|---|---|
| LLM | Ollama + llama3.2 3B (Q8_0 / Q4_K_M / Q3_K_M comparados en la Parte A) |
| Embeddings | nomic-embed-text (768d, vía Ollama) |
| Vector DB | sqlite-vec (un fichero, `rag/index.db`) |
| Herramientas | Servidor MCP propio (SDK oficial Python, stdio) |

**Hardware de referencia:** ASUS ROG Strix G614JV, i7-13650HX (14C/20T),
15.6 GB RAM, Windows 11. La RTX 4060 **no se usa**: todas las llamadas de
inferencia llevan `num_gpu: 0` (restricción del enunciado).

## Instalación (un comando)

Requisitos previos: [Ollama](https://ollama.com) instalado, Python 3.13, git.

```powershell
.\setup.ps1     # crea venv, instala deps fijadas, descarga modelos, construye el índice RAG
```

Para el correo (opcional): copia `.env.example` a `.env` y pon una
**contraseña de aplicación** de Google (https://myaccount.google.com/apppasswords).

## Uso

```powershell
.\.venv\Scripts\Activate.ps1
python jarvis.py                                                  # Jarvis de texto: LLM + herramientas vía MCP (Parte D)
python rag\rag.py "How do I change where Ollama stores models?"   # RAG directo (Parte C)
```

## Reproducir los experimentos del reporte

```powershell
# Parte A — estudio de cuantización (3 niveles, tok/s, RAM, calidad)
python benchmarks\bench_quant.py        # → measurements.csv + benchmarks/results/
python benchmarks\eval_code.py          # valida el prompt de código

# Parte B — KV cache (contextos 512/2048/8192/16384)
python benchmarks\bench_kv.py           # KV f16
.\benchmarks\run_kv_quant.ps1           # repetición con KV cache q8_0

# Gráficas del reporte
python benchmarks\plots.py              # → report/plot_quant.png, plot_kv.png

# Parte C — comparación con/sin RAG (5 preguntas)
python rag\compare_rag.py               # → rag/compare_results.json

# Parte E — test set completo (21 prompts, 5 categorías)
python evaluation\run_tests.py          # → evaluation/results.json + tablas
```

La rúbrica de calidad 0–3 está en [`benchmarks/RUBRIC.md`](benchmarks/RUBRIC.md).
Los fallos de tool calling se documentan en [`mcp_server/FAILURES.md`](mcp_server/FAILURES.md).

## Estructura del repo

```
ironman/            núcleo: LLM (Ollama), cliente MCP, skills (correo + sistema)
mcp_server/         servidor MCP propio (stdio) — Parte D
rag/                ingesta, índice sqlite-vec, comparación — Parte C
benchmarks/         cuantización y KV cache — Partes A y B
evaluation/         test_set.json + runner — Parte E
report/             reporte técnico + gráficas
bonus/              extras fuera del alcance del núcleo (voz, GUI) — para más adelante
measurements.csv    datos crudos de todos los benchmarks (D5)
jarvis.py           punto de entrada (texto)
```

## Demo

📹 *(enlace al vídeo de 3-5 min aquí)* — tareas: pregunta RAG sobre la
documentación, resumen de correos, y tarea multi-paso (buscar en docs +
enviar correo).

## Notas

- Corpus RAG: documentación oficial de Ollama (web + repo) y llama.cpp
  (~202 páginas). Ver justificación en `rag/ingest.py`.
- `setup.ps1` fija todas las versiones (`requirements.txt`) para reproducibilidad.
- La carpeta `bonus/` guarda el asistente de voz (Whisper + TTS), la GUI y los
  lanzadores: material extra que no forma parte del núcleo evaluado.
