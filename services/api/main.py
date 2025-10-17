from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .models import BidChange, RAGRequest, RAGResponse
from .utils import get_conn
from . import rag

app = FastAPI(title="AmazonManageMyAd — Local API")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/rag", response_model=RAGResponse)
def rag_endpoint(req: RAGRequest):
    ctx = rag.retrieve(req.category_id, req.question, req.top_k)
    summary, items = rag.generate_answer(req.category_id, req.question, ctx)
    # store
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "insert into recommendations(category_id, payload) values (%s,%s)",
                (req.category_id, {"summary": summary, "items": items}),
            )
            return {"summary": summary, "items": items}


@app.post("/bids/preview")
def preview_bid_changes(changes: list[BidChange]):
    # This is a preview endpoint (no writeback). You can wire actual write calls later.
    return {"count": len(changes), "changes": [c.model_dump() for c in changes]}
