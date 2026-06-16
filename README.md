# IRONMAN — Jarvis local (Applied ML: Local LLM Systems)

Asistente personal **100 % local**: responde con un LLM pequeño servido por
Ollama (solo CPU), busca en documentos con **RAG** y usa herramientas (correo,
abrir apps, búsqueda) expuestas con un servidor **MCP** propio. Ningún LLM en
la nube en el camino de inferencia.

> Informe técnico: [`report/report.pdf`](report/report.pdf)
> Vídeo de demo: [enlace pendiente](#demo)

## Estructura del proyecto (una carpeta por parte)

| Carpeta / archivo | Para qué sirve | Parte |
|---|---|---|
| `asistente/jarvis.py` | El asistente: chat + herramientas + RAG (la demo) | D |
| `asistente/mcp_server.py` | Servidor MCP con las 6 herramientas | D |
| `benchmarks/parte_a_cuantizacion.py` | Mide tamaño, RAM, velocidad y calidad de 3 cuantizaciones | A |
| `benchmarks/parte_b_kvcache.py` | Mide el KV cache con 4 longitudes de contexto | B |
| `benchmarks/medir_comun.py` | Funciones de medición compartidas (A y B) | A, B |
| `benchmarks/graficas.py` | Dibuja las 2 gráficas del informe | A, B |
| `benchmarks/run_kv_quant.ps1` | Mide el KV cache cuantizado a Q8 | B.4 |
| `rag/parte_c_rag.py` | Construye el índice, recupera y compara con/sin RAG | C |
| `rag/corpus/` | Documentos para el RAG (~200 páginas) | C |
| `rag/index.db` | Índice vectorial del RAG | C |
| `evaluacion/parte_e_evaluacion.py` | Corre el test de 21 preguntas | E |
| `evaluacion/test_set.json` | Las 21 preguntas de evaluación | E |
| `report/` | Informe, gráficas y PDF | — |
| `resultados/` | Salidas para puntuar (calidad, RAG, evaluación) | A, C, E |
| `docs/` | Diagramas de arquitectura | — |
| `measurements.csv` | Todos los números medidos | A, B |
| `rubrica.md` | Cómo se puntúa la calidad (0–3) | A, C |
| `FAILURES.md` | Casos donde fallan las herramientas | D |

## Requisitos

[Ollama](https://ollama.com) instalado, Python 3.13, git.

## Instalación (un comando)

```powershell
.\setup.ps1     # crea el entorno, instala dependencias, baja modelos, construye el índice RAG
```

Para el correo (opcional): copia `.env.example` a `.env` y pon una
**contraseña de aplicación** de Google.

## Cómo reproducir cada parte

```powershell
.\.venv\Scripts\Activate.ps1            # activar el entorno

python benchmarks\parte_a_cuantizacion.py   # Parte A  -> measurements.csv + resultados/
python benchmarks\parte_b_kvcache.py        # Parte B (KV f16)
.\benchmarks\run_kv_quant.ps1               # Parte B.4 (KV q8_0)
python benchmarks\graficas.py               # gráficas -> report/
python rag\parte_c_rag.py compare           # Parte C  -> resultados/compare_results.json
python evaluacion\parte_e_evaluacion.py     # Parte E  -> resultados/results.json

python asistente\jarvis.py                  # la demo interactiva
```

Tras la Parte A y la C hay que **puntuar a mano** las respuestas (0–3) con
`rubrica.md` y escribir las medias donde corresponde.

## Hardware de referencia

ASUS ROG Strix G614JV, i7-13650HX (14C/20T), 15.6 GB RAM, Windows 11. La RTX
4060 **no se usa**: todas las llamadas llevan `num_gpu: 0` (restricción del
enunciado).

## Demo

Vídeo (3–5 min): _enlace pendiente_.
