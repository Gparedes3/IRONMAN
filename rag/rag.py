"""Parte C — Recuperación + generación aumentada (RAG).

retrieve(): embebe la pregunta (prefijo "search_query:"), busca los top-K
chunks más cercanos en sqlite-vec y los devuelve.
answer(): inyecta esos chunks en el prompt y genera con el modelo local.

Uso interactivo:  python rag/rag.py "How do I change where Ollama stores models?"
"""
import sys
from pathlib import Path

import ollama

sys.path.insert(0, str(Path(__file__).parent))
from ingest import EMBED_MODEL, open_db, serialize

GEN_MODEL = "llama3.2:3b-instruct-q4_K_M"
TOP_K = 4

RAG_TEMPLATE = """Answer the question using ONLY the documentation excerpts below.
If the excerpts do not contain the answer, say you don't know.

{context}

Question: {question}
Answer:"""


def retrieve(question: str, k: int = TOP_K) -> list[dict]:
    client = ollama.Client()
    emb = client.embeddings(model=EMBED_MODEL,
                            prompt=f"search_query: {question}",
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
    client = ollama.Client()
    sources = []
    if use_rag:
        hits = retrieve(question)
        sources = [h["source"] for h in hits]
        context = "\n\n---\n\n".join(
            f"[{h['source']}]\n{h['text']}" for h in hits)
        prompt = RAG_TEMPLATE.format(context=context, question=question)
    else:
        prompt = question
    resp = client.chat(
        model=GEN_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"num_gpu": 0, "num_ctx": num_ctx, "temperature": 0, "seed": 42},
    )
    return {"answer": resp["message"]["content"], "sources": sources}


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "How do I change where Ollama stores models?"
    r = answer(q)
    print(r["answer"])
    print("\nFuentes:", ", ".join(dict.fromkeys(r["sources"])))
