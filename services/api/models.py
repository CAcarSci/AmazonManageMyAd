from pydantic import BaseModel
from typing import Optional, List, Literal, Any

class BidChange(BaseModel):
    entity_type: Literal["keyword","target"]
    entity_id: int
    action: Literal["increase","decrease","set"]
    percent: Optional[float] = None
    new_bid: Optional[float] = None
    reason: str

class RAGRequest(BaseModel):
    category_id: str
    top_k: int = 12
    question: str = "High-impact keywords and actions"

class RAGResponse(BaseModel):
    summary: str
    items: List[Any]
