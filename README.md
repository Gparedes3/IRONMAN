# IRONMAN — Jarvis local (Applied ML: Local LLM Systems)

Asistente personal **100 % local**: responde con un LLM pequeño servido por
Ollama (solo CPU), busca en documentos con **RAG** y usa herramientas (correo,
abrir apps, búsqueda) expuestas con un servidor **MCP** propio. Ningún LLM en
la nube en el camino de inferencia.

> Informe técnico: [`report/report.pdf`](report/report.pdf)
> Vídeo de demo: [enlace pendiente](#demo)

## Qué es cada archivo (estructura plana, un archivo por parte)

| Archivo | Para qué sirve | Parte |
|---|---|---|
| `jarvis.py` | El asistente: chat + herramientas + RAG (la demo) | D |
| `mcp_server.py` | Servidor MCP con las 6 herramientas | D |
| `parte_a_cuantizacion.py` | Mide tamaño, RAM, velocidad y calidad de 3 cuantizaciones | A |
| `parte_b_kvcache.py` | Mide el KV cache con 4 longitudes de contexto | B |
| `parte_c_rag.py` | Construye el índice, recupera y compara con/sin RAG | C |
| `parte_e_evaluacion.py` | Corre el test de 21 preguntas | E |
| `medir_comun.py` | Funciones de medición compartidas (A y B) | A, B |
| `graficas.py` | Dibuja las 2 gráficas del informe | A, B |
| `rubrica.md` | Cómo se puntúa la calidad (0–3) | A, C |
| `test_set.json` | Las 21 preguntas de evaluación | E |
| `measurements.csv` | Todos los números medidos | A, B |
| `FAILURES.md` | Casos donde fallan las herramientas | D |
| `corpus/` | Documentos para el RAG (~200 páginas) | C |
| `index.db` | Índice vectorial del RAG | C |
| `resultados/` | Salidas para puntuar (calidad, RAG, evaluación) | A, C, E |
| `report/` | Informe, gráficas y PDF | — |

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

python parte_a_cuantizacion.py          # Parte A  -> measurements.csv + resultados/
python parte_b_kvcache.py               # Parte B (KV f16)
.\run_kv_quant.ps1                      # Parte B.4 (KV q8_0)
python graficas.py                      # gráficas -> report/
python parte_c_rag.py compare           # Parte C  -> resultados/compare_results.json
python parte_e_evaluacion.py            # Parte E  -> resultados/results.json

python jarvis.py                        # la demo interactiva
```

Tras la Parte A y la C hay que **puntuar a mano** las respuestas (0–3) con
`rubrica.md` y escribir las medias donde corresponde.

## Hardware de referencia

ASUS ROG Strix G614JV, i7-13650HX (14C/20T), 15.6 GB RAM, Windows 11. La RTX
4060 **no se usa**: todas las llamadas llevan `num_gpu: 0` (restricción del
enunciado).

## Demo

Vídeo (3–5 min): _enlace pendiente_.
