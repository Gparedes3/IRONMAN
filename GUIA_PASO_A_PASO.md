# Guía paso a paso para cerrar todos los entregables

Esta guía es un **runbook lineal**. Hazla en orden, en **tu portátil ASUS ROG**
(PowerShell + Ollama). Cada paso dice qué comando correr, qué deberías ver, y
qué entregable cierra. Lo que **no puedo hacer yo** desde aquí va marcado con
`>> MANUAL`.

Estado de partida (lo que YA está hecho en el repo):
- Parte A: velocidades de las 3 cuantizaciones medidas (3 filas en `measurements.csv`)
  y respuestas de calidad generadas (`benchmarks/results/quality_outputs.json`).
- Parte B: 4 longitudes de contexto medidas (4 filas en `measurements.csv`).
- Parte C: corpus descargado e índice vectorial construido (`rag/index.db`).
- Falta: puntuar calidad, fila KV-q8, comparación RAG, evaluación, gráficas,
  rellenar el informe, PDF, git/GitHub y vídeo. Eso es lo que cierra esta guía.

---

## PASO 0 — Limpiar el `.git` roto  `>> MANUAL`

Intenté inicializar git desde mi entorno y OneDrive corrompió la carpeta `.git`
(quedó a medias y no pude borrarla). **Bórrala tú primero**, si no, `git init`
fallará.

Abre PowerShell y ve a la carpeta del proyecto:

```powershell
cd "$env:USERPROFILE\OneDrive\Documentos\IRONMAN"
Remove-Item -Recurse -Force .git
```

Comprueba que ya no existe (no debe imprimir nada):

```powershell
Test-Path .git    # debe decir: False
```

> Si `Remove-Item` se queja de que un archivo está en uso, pausa OneDrive
> (icono de la nube → engranaje → "Pausar sincronización 2 horas") y repite.

---

## PASO 1 — Entorno + modelos (setup de un comando)

Si ya corriste `setup.ps1` antes y tienes `.venv` y los modelos descargados,
**puedes saltarte este paso**. Para verificar:

```powershell
ollama list          # deben aparecer q8_0, q4_K_M, q3_K_M y nomic-embed-text
Test-Path .venv      # True
```

Si falta algo, corre el setup completo (tarda: descarga ~7 GB de modelos y clona
el corpus):

```powershell
.\setup.ps1
```

Activa el entorno para los pasos siguientes:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## PASO 2 — Parte A: puntuar la calidad  `>> MANUAL` (cierra A.3 + columna quality_avg)

Las respuestas ya están generadas. Tienes que **puntuarlas tú** (0–3) con la
rúbrica. Esto es manual a propósito: el enunciado exige que defiendas cada nota.

1. Abre la rúbrica `benchmarks\RUBRIC.md` y tenla al lado.
2. Abre `benchmarks\results\quality_outputs.json`. Verás 3 bloques (`Q8_0`,
   `Q4_K_M`, `Q3_K_M`), cada uno con 5 respuestas y un campo `"score": null`.
3. Para el prompt de **código**, no juzgues a ojo: ejecútalo de verdad:

   ```powershell
   python benchmarks\eval_code.py
   ```

   Te dice si la función pasa los 5 casos (eso fija su nota: 3 si pasa todos).
4. Pon en cada `"score"` un entero 0–3 según la rúbrica y el campo `"check"`.
   Guarda el archivo.

Ahora calcula la media por cuantización (copia y pega tal cual):

```powershell
python -c "import json;d=json.load(open(r'benchmarks/results/quality_outputs.json'));[print(q, round(sum(x['score'] for x in v)/len(v),2)) for q,v in d.items()]"
```

Te imprimirá tres líneas, p. ej. `Q8_0 2.6`. **Escribe esos tres números** en la
columna `quality_avg` de `measurements.csv`, en las 3 filas de PartA (las que
tienen `context_length=2048` y notes `PartA...`). Edita el CSV con un editor de
texto (no Excel, para no romper el formato).

---

## PASO 3 — Parte B.4: KV cache cuantizado a Q8  (cierra B.4 + D5)

Esto arranca un servidor temporal de Ollama con el KV cache en q8_0 y repite UNA
configuración para medir el ahorro de RAM. **Cierra todas tus sesiones de Ollama
antes** (el script para la app de bandeja):

```powershell
.\benchmarks\run_kv_quant.ps1
```

Al terminar tendrás filas nuevas en `measurements.csv` con `kv_cache_type=q8_0`.
Compara su `peak_ram_mb` con la fila f16 del mismo contexto: la diferencia es el
ahorro que reportarás. Reabre la app normal de Ollama después si la quieres.

Con esto `measurements.csv` queda completo → **D5 cerrado.**

---

## PASO 4 — Gráficas (Partes A y B)

```powershell
python benchmarks\plots.py
```

Genera `benchmarks\results\plot_quant.png` y `plot_kv.png`. Los insertarás en el
informe.

---

## PASO 5 — Parte C: comparar RAG vs sin RAG  (cierra C.3)

```powershell
python rag\compare_rag.py
```

Genera un JSON con las respuestas a 5 preguntas en los dos modos. **Puntúalas tú
con la misma rúbrica** (igual que el Paso 2): abre el JSON que indica la consola,
añade un `score` 0–3 a cada respuesta, y calcula la media con/ sin RAG. Esos dos
promedios van en la tabla del informe (sección C).

---

## PASO 6 — Parte E: evaluación automática  (cierra D3 + tablas de E)

Arranca el servidor MCP y corre el set de pruebas en vivo:

```powershell
python evaluation\run_tests.py --live
```

Imprime una tabla con éxito/parcial/fallo, latencia y tokens **por categoría**, y
guarda el detalle en un JSON. Copia esa tabla y el resumen para el informe.
`test_set.json` (21 pruebas) ya cumple **D3**.

> Si alguna prueba `tool-required` falla, **no lo escondas**: anota el caso en
> `mcp_server\FAILURES.md`. Los fallos analizados puntúan (Parte D.3 y F).

---

## PASO 7 — Rellenar el informe  (cierra D2, parte 1)

Abre `report\report.md`. Tiene 11 marcadores `{{...}}` que debes sustituir con
los números reales que acabas de generar:

| Marcador | Qué poner |
|----------|-----------|
| `{{ABSTRACT_RESULT_SENTENCE}}` | 1 frase con tu hallazgo principal (p. ej. "Q4_K_M da ~1.7× tok/s vs Q8_0 perdiendo solo 0.X de calidad"). |
| `{{N_CHUNKS}}` | nº de fragmentos del índice RAG (mira lo que imprimió `ingest.py`, o cuéntalos en `index.db`). |
| `{{A_ANALYSIS}}` | 1 párrafo interpretando la gráfica tamaño/velocidad/calidad. |
| `{{B_TABLE}}` | tabla con las filas PartB de `measurements.csv` (contexto, tok/s, RAM). |
| `{{B_ANALYSIS}}` | 1 párrafo: el KV cache crece ~lineal con el contexto; cita el ahorro q8. |
| `{{C_TABLE}}` | tabla con/ sin RAG y sus medias de calidad (Paso 5). |
| `{{C_ANALYSIS}}` | 1 párrafo comparando con/sin RAG. |
| `{{D_FAILURES_SUMMARY}}` | resumen de prompts que funcionan y los que fallan (de FAILURES.md). |
| `{{E_TABLE}}` | tabla por categoría del Paso 6 (éxito %, latencia media). |
| `{{E_ANALYSIS}}` | 1 párrafo interpretando la evaluación. |
| `{{F_LIMITS}}` | "Límites honestos": 2-3 ejemplos concretos de tu test_set donde Jarvis falla, + 2 mejoras factibles con más RAM/GPU. |

Comprueba que no quede ninguno sin rellenar:

```powershell
Select-String -Path report\report.md -Pattern "{{"
```

No debe devolver nada.

---

## PASO 8 — Exportar el informe a PDF  (cierra D2)

El enunciado pide PDF de 4-6 páginas. Avísame cuando tengas el `report.md`
relleno y **yo te genero el PDF con formato** (puedo usar la herramienta de PDF).
Alternativa rápida por tu cuenta con pandoc (entra a `report\` para que
encuentre los diagramas de `docs/img/`):

```powershell
cd report
pandoc report.md -o report.pdf --resource-path=".;.."
cd ..
```

---

## PASO 9 — Git + GitHub  `>> MANUAL` (cierra D1)

Con el `.git` roto ya borrado (Paso 0), inicializa limpio:

```powershell
cd "$env:USERPROFILE\OneDrive\Documentos\IRONMAN"
git init
git add -A
git status                       # revisa que NO aparezca .env (debe estar ignorado)
git commit -m "Jarvis local: estudio cuantizacion, KV cache, RAG, MCP y eval"
```

> **Importante:** confirma que `.env` (con tu contraseña de Gmail) NO está en la
> lista. Está en `.gitignore`, pero verifícalo antes de subir.

Crea un repo vacío en GitHub (web → New repository, **sin** README) y conéctalo:

```powershell
git remote add origin https://github.com/TU_USUARIO/IRONMAN.git
git branch -M main
git push -u origin main
```

Comparte el repo con el instructor si lo dejas privado.

---

## PASO 10 — Vídeo de demostración  `>> MANUAL` (cierra D4)

Graba 3-5 min (OBS, Xbox Game Bar con `Win+G`, o el móvil) mostrando a Jarvis en
vivo en **3 tareas distintas**, p. ej.:

1. Chat puro: `python jarvis.py` y una pregunta de razonamiento.
2. RAG: una pregunta que solo se responde con el corpus (p. ej. sobre la API de
   Ollama) — se ve que cita el documento.
3. Herramienta MCP: "resume mis correos no leídos de esta semana" o "abre tal
   web / busca en la web".

Sube el vídeo (YouTube no listado o Drive) y **pega el enlace en el README**
(sección Demo). Eso cierra **D4**.

---

## Resumen de qué cierra cada paso

| Paso | Entregable |
|------|-----------|
| 2, 3 | D5 (`measurements.csv` completo) |
| 6 | D3 (`test_set.json` ya estaba; aquí lo ejecutas) |
| 7, 8 | D2 (informe PDF) |
| 9 | D1 (repo en GitHub, README con repro de un comando) |
| 10 | D4 (vídeo) |

## Preguntas que te harán en la defensa (ten la respuesta lista)

- **¿Por qué Q4_K_M y no Q5_K_M?** → mira tu tabla: tok/s vs quality_avg; Q4_K_M
  es el mejor equilibrio velocidad/calidad en CPU con 16 GB.
- **¿Cuánto pesa tu KV cache en 8K contexto y por qué?** → diferencia de
  `peak_ram_mb` entre 8192 y 512 en las filas PartB; crece ~lineal con el contexto.
- **Muéstrame un caso donde falla tu herramienta.** → ten abierto
  `mcp_server\FAILURES.md` con un ejemplo real del Paso 6.
