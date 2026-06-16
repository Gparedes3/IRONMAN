"""
parte_c_rag.py  —  PARTE C del trabajo (RAG = Retrieval Augmented Generation)
=============================================================================
RAG = "buscar antes de responder". En vez de que el modelo se invente datos,
primero busca trozos relevantes en un corpus de documentos y se los da como
contexto para que responda con hechos reales.

Corpus: documentación oficial de Ollama y llama.cpp (carpeta corpus/, ~200
páginas). Buena elección porque tiene datos concretos (variables de entorno,
flags, formatos) que un modelo de 3B NO sabe de memoria -> así se nota el RAG.

Pipeline en 2 fases:
  INGESTA (una vez):  trocear los .md -> embeber cada trozo con nomic-embed-text
                      (local) -> guardar texto + vector en index.db (sqlite-vec).
  CONSULTA (siempre): embeber la pregunta -> buscar los K trozos más parecidos
                      -> meterlos en el prompt -> generar la respuesta.

Cómo se ejecuta:
  python parte_c_rag.py ingest                 # construye index.db (fase 1)
  python parte_c_rag.py "tu pregunta aquí"     # pregunta con RAG (fase 2)
  python parte_c_rag.py compare                # compara CON vs SIN RAG (C.3)
"""
import json
import sqlite3
import struct
import sys
import time
from pathlib import Path

import ollama
import sqlite_vec

HERE = Path(__file__).resolve().parent   # carpeta rag/
ROOT = HERE.parent                       # raíz del proyecto
CORPUS = HERE / "corpus"            # los documentos .md (dentro de rag/)
DB_PATH = HERE / "index.db"         # la base de datos vectorial (dentro de rag/)
RESULTS_DIR = ROOT / "resultados"

EMBED_MODEL = "nomic-embed-text"    # modelo de embeddings LOCAL (768 dimensiones)
GEN_MODEL = "llama3.2:3b-instruct-q4_K_M"  # el modelo que redacta la respuesta
DIM = 768                           # tamaño del vector que produce el embedder
CHUNK_CHARS = 1000                  # tamaño de cada trozo (~1 párrafo largo)
OVERLAP_CHARS = 150                 # solape entre trozos para no cortar ideas
TOP_K = 4                           # cuántos trozos se recuperan por pregunta

# Plantilla que obliga al modelo a responder SOLO con lo recuperado.
# NOTA: la plantilla y las preguntas van en INGLÉS a propósito, porque el corpus
# (docs de Ollama y llama.cpp) está en inglés. Consultar un corpus en su propio
# idioma es la prueba justa del RAG; preguntar en español sobre documentos en
# inglés degrada la recuperación (lo verificamos: ver informe, Parte C).
RAG_TEMPLATE = """Answer the question using ONLY the documentation excerpts below.
If the excerpts do not contain the answer, say you don't know.

{context}

Question: {question}
Answer:"""


# ------------------------------- utilidades --------------------------------
def serialize(vec: list[float]) -> bytes:
    """Convierte una lista de floats al formato binario que guarda sqlite-vec."""
    return struct.pack(f"{len(vec)}f", *vec)


def open_db() -> sqlite3.Connection:
    """Abre index.db cargando la extensión sqlite-vec (búsqueda vectorial)."""
    db = sqlite3.connect(DB_PATH)
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)
    return db


def chunk_text(text: str) -> list[str]:
    """Trocea un documento en pedazos de ~1000 caracteres respetando párrafos,
    con 150 de solape. Los párrafos enormes (código/tablas) se parten a la
    fuerza para no pasarnos del límite del embedder."""
    paras = []
    for p in (p.strip() for p in text.split("\n\n") if p.strip()):
        while len(p) > CHUNK_CHARS:
            paras.append(p[:CHUNK_CHARS])
            p = p[CHUNK_CHARS - OVERLAP_CHARS:]
        paras.append(p)
    chunks, current = [], ""
    for p in paras:
        if len(current) + len(p) > CHUNK_CHARS and current:
            chunks.append(current)
            current = current[-OVERLAP_CHARS:]  # arrastra solape
        current = (current + "\n\n" + p).strip()
    if current:
        chunks.append(current)
    return [c for c in chunks if len(c) > 50]


# ------------------------------- FASE 1: ingesta ---------------------------
def ingest():
    """Construye index.db desde cero a partir de los .md de corpus/."""
    client = ollama.Client()
    if DB_PATH.exists():
        DB_PATH.unlink()  # empezar limpio
    db = open_db()
    db.execute("CREATE TABLE chunks (id INTEGER PRIMARY KEY, source TEXT, text TEXT)")
    db.execute(f"CREATE VIRTUAL TABLE chunks_vec USING vec0(embedding float[{DIM}])")

    files = sorted(CORPUS.rglob("*.md"))
    if not files:
        sys.exit("corpus/ vacío: ejecuta setup.ps1 para descargar la documentación.")

    n = 0
    for f in files:
        rel = f.relative_to(CORPUS).as_posix()
        for chunk in chunk_text(f.read_text(encoding="utf-8", errors="replace")):
            # "search_document:" es el prefijo que recomienda nomic-embed-text
            emb = client.embeddings(model=EMBED_MODEL,
                                    prompt=f"search_document: {chunk}",
                                    options={"num_gpu": 0})["embedding"]
            n += 1
            db.execute("INSERT INTO chunks (id, source, text) VALUES (?, ?, ?)",
                       (n, rel, chunk))
            db.execute("INSERT INTO chunks_vec (rowid, embedding) VALUES (?, ?)",
                       (n, serialize(emb)))
        print(f"  {rel}: indexado")
    db.commit()
    print(f"\n{n} trozos de {len(files)} ficheros -> {DB_PATH}")


# ------------------------------- FASE 2: consulta --------------------------
def retrieve(question: str, k: int = TOP_K) -> list[dict]:
    """Busca los k trozos más parecidos a la pregunta. Devuelve fuente + texto."""
    client = ollama.Client()
    emb = client.embeddings(model=EMBED_MODEL,
                            prompt=f"search_query: {question}",  # prefijo de consulta
                            options={"num_gpu": 0})["embedding"]
    db = open_db()
    rows = db.execute(
        """SELECT c.source, c.text, v.distance
           FROM chunks_vec v JOIN chunks c ON c.id = v.rowid
           WHERE v.embedding MATCH ? AND v.k = ?
           ORDER BY v.distance""",
        (serialize(emb), k)).fetchall()
    return [{"source": s, "text": t, "distance": d} for s, t, d in rows]


def answer(question: str, use_rag: bool = True, num_ctx: int = 4096) -> dict:
    """Responde la pregunta. Si use_rag=True, primero recupera contexto."""
    client = ollama.Client()
    sources = []
    if use_rag:
        hits = retrieve(question)
        sources = [h["source"] for h in hits]
        context = "\n\n---\n\n".join(f"[{h['source']}]\n{h['text']}" for h in hits)
        prompt = RAG_TEMPLATE.format(context=context, question=question)
    else:
        prompt = question  # sin RAG: la pregunta a secas
    resp = client.chat(
        model=GEN_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"num_gpu": 0, "num_ctx": num_ctx, "temperature": 0, "seed": 42},
    )
    return {"answer": resp["message"]["content"], "sources": sources}


# ------------------------------- C.3: comparación --------------------------
COMPARE_QUESTIONS = [
    {"q": "Which environment variable changes the directory where Ollama stores its models?",
     "check": "OLLAMA_MODELS (faq.md)."},
    {"q": "How do you allow Ollama to listen on all network interfaces instead of only localhost?",
     "check": "OLLAMA_HOST=0.0.0.0 (faq.md)."},
    {"q": "According to the llama.cpp docs, what does the -ngl / --n-gpu-layers flag control?",
     "check": "Cuántas capas del modelo se descargan a la GPU."},
    {"q": "How long does Ollama keep a model loaded in memory by default, and how can you change it?",
     "check": "5 minutos; keep_alive / OLLAMA_KEEP_ALIVE (faq.md)."},
    {"q": "What file format does Ollama use for model weights and what is a Modelfile for?",
     "check": "GGUF; el Modelfile define modelo base, plantilla, system prompt y parámetros."},
]


def compare():
    """Responde 5 preguntas CON y SIN RAG y guarda todo para puntuar a mano."""
    RESULTS_DIR.mkdir(exist_ok=True)
    results = []
    for item in COMPARE_QUESTIONS:
        q = item["q"]
        print(f"\nQ: {q}")
        row = {"question": q, "check": item["check"]}
        for mode, use_rag in [("with_rag", True), ("without_rag", False)]:
            t0 = time.perf_counter()
            r = answer(q, use_rag=use_rag)
            dt = round(time.perf_counter() - t0, 1)
            row[mode] = {"answer": r["answer"], "sources": r["sources"],
                         "latency_s": dt, "score": None}  # <-- puntúalo tú
            print(f"  [{mode}] {dt}s: {r['answer'][:100]}...")
        results.append(row)
    out = RESULTS_DIR / "compare_results.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado en {out} — puntúa 0-3 con rubrica.md")


# ------------------------------- punto de entrada --------------------------
if __name__ == "__main__":
    arg = " ".join(sys.argv[1:]).strip()
    if arg == "ingest":
        ingest()
    elif arg == "compare":
        compare()
    elif arg:
        r = answer(arg)
        print(r["answer"])
        print("\nFuentes:", ", ".join(dict.fromkeys(r["sources"])))
    else:
        print("Uso: python parte_c_rag.py [ingest | compare | \"tu pregunta\"]")
