"""
models.py — Pydantic request/response models for the NutriBot API.
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


# ── Request models ────────────────────────────────────────────────────────────

class Message(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="User question")
    conversation_history: list[Message] = Field(
        default_factory=list,
        description="Previous messages for multi-turn context (last 6)",
    )
    top_k: Optional[int] = Field(
        default=None, ge=1, le=15, description="Number of chunks to retrieve"
    )
    doc_id: Optional[str] = Field(
        default=None, description="Filter retrieval to a specific document"
    )

    model_config = {"json_schema_extra": {"example": {
        "query": "What are the best protein sources for muscle building?",
        "conversation_history": []
    }}}


# ── Response models ───────────────────────────────────────────────────────────

class SourceChunk(BaseModel):
    content: str
    page: Optional[int] = None
    source: Optional[str] = None
    similarity: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    model: str
    query: str
    tokens_used: Optional[int] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    embed_model: str
    llm_model: str
    supabase_connected: bool
