"""Parte C — Ingesta del corpus en el índice vectorial.

Corpus: documentación oficial de Ollama y llama.cpp (rag/corpus/, ~130
páginas). Elección justificada: es la base de conocimiento perfecta para un
Jarvis "experto en LLMs locales" y contiene hechos concretos y verificables
(variables de entorno, flags, formatos GGUF) que el modelo base de 3B NO
sabe de memoria — ideal para medir el efecto del RAG.

Pipeline:
  1. Trocear cada .md en chunks de ~1000 caracteres respetando párrafos,
     con 150 de solape para no cortar ideas.
  2. Embeber cada chunk con nomic-embed-text (LOCAL, vía Ollama, 768 dims),
     con el prefijo "search_document:" que recomienda el modelo.
  3. Guardar texto + vector en sqlite-vec (rag/index.db, 100% local).

Uso:  python rag/ingest.py
"""
import sqlite3
import struct
import sys
from pathlib import Path

import ollama
import sqlite_vec

ROOT = Path(__file__).resolve().parent
CORPUS = ROOT / "corpus"
DB_PATH = ROOT / "index.db"
EMBED_MODEL = "nomic-embed-text"
DIM = 768
CHUNK_CHARS = 1000
OVERLAP_CHARS = 150


def chunk_text(text: str) -> list[str]:
    """Trocea por párrafos acumulando hasta ~CHUNK_CHARS, con solape.
    Los "párrafos" gigantes (bloques de código/tablas sin línea en blanco)
    se parten a tamaño fijo para no exceder el contexto del embedder."""
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
            current = current[-OVERLAP_CHARS:]  # solape con el chunk anterior
        current = (current + "\n\n" + p).strip()
    if current:
        chunks.append(current)
    return [c for c in chunks if len(c) > 50]


def serialize(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def open_db() -> sqlite3.Connection:
    db = sqlite3.connect(DB_PATH)
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)
    return db


def main():
    client = ollama.Client()
    if DB_PATH.exists():
        DB_PATH.unlink()
    db = open_db()
    db.execute("CREATE TABLE chunks (id INTEGER PRIMARY KEY, source TEXT, text TEXT)")
    db.execute(f"CREATE VIRTUAL TABLE chunks_vec USING vec0(embedding float[{DIM}])")

    files = sorted(CORPUS.rglob("*.md"))
    if not files:
        sys.exit("Corpus vacío: ejecuta primero los pasos del README para poblar rag/corpus/")

    n = 0
    for f in files:
        rel = f.relative_to(CORPUS).as_posix()
        for chunk in chunk_text(f.read_text(encoding="utf-8", errors="replace")):
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
    print(f"\n{n} chunks de {len(files)} ficheros -> {DB_PATH}")


if __name__ == "__main__":
    main()
