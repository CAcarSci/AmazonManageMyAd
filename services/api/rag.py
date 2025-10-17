import os
import json
from typing import List, Tuple
from .utils import get_conn
import requests

OLLAMA = os.getenv("OLLAMA_BASE", "http://ollama:11434")
GEN_MODEL = os.getenv("OLLAMA_GEN_MODEL", "llama3.1:8b")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

SYSTEM = "You are an Amazon Ads strategist. Use only given facts. Be concise and action-oriented."


def embed(text: str) -> List[float]:
    r = requests.post(
        f"{OLLAMA}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["embedding"]


def retrieve(
    category_id: str, query: str, top_k: int = 12
) -> List[Tuple[str, dict, float]]:
    vec = embed(query)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select chunk, meta, 1 - (embedding <=> %s::vector) as score
                from keyword_chunks
                where category_id = %s
                order by embedding <=> %s::vector
                limit %s
                """,
                (vec, category_id, vec, top_k),
            )
            return cur.fetchall()


def generate_answer(
    category_id: str, question: str, contexts: List[Tuple[str, dict, float]]
):
    ctx = "\n\n".join(
        [
            f"[Score {round(s,3)}] {c}\nMETA: {json.dumps(m)[:400]}"
            for c, m, s in contexts
        ]
    )
    prompt = f"SYSTEM:\n{SYSTEM}\n\nUSER:\nCategory={category_id}. Question={question}.\n\nCONTEXT:\n{ctx}\n\nTASK:\n1) Shortlist 10–20 keywords with tags [generic|attribute|branded|competitor|long-tail].\n2) Actions: SP [new exact|bid up|bid down|negative], SB/SD if relevant.\n3) Return JSON under key 'items' + a short summary."
    r = requests.post(
        f"{OLLAMA}/api/generate",
        json={"model": GEN_MODEL, "prompt": prompt, "stream": False},
        timeout=120,
    )
    r.raise_for_status()

    resp = r.json().get("response", "{}")
    # naive JSON block extraction
    start = resp.find("{")
    items_json = None
    if start != -1:
        try:
            items_json = json.loads(resp[start:])
        except Exception:
            items_json = {"items": []}
            summary = resp[:start].strip() if start != -1 else resp
            return summary, items_json.get("items", [])
