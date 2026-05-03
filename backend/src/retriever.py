"""
retriever.py — Supabase pgvector semantic search.

Uses the match_chunks RPC function defined in supabase/schema.sql.
Embedding dimensions changed from 1536 (OpenAI) → 384 (MiniLM).
"""

from __future__ import annotations
import logging
from supabase import create_client, Client
from .config import (
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
    TOP_K,
    SIMILARITY_THRESHOLD,
)
from .embeddings import embed_query
from .models import SourceChunk

logger = logging.getLogger(__name__)

_supabase_client: Client | None = None


def get_supabase() -> Client:
    """Return cached Supabase client (singleton)."""
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env"
            )
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        logger.info("Supabase client initialized ✅")
    return _supabase_client


def retrieve(
    query: str,
    top_k: int = TOP_K,
    doc_id: str | None = None,
    threshold: float = SIMILARITY_THRESHOLD,
) -> list[SourceChunk]:
    """
    Perform semantic search against Supabase pgvector.

    Args:
        query:     Natural language query from user.
        top_k:     Maximum number of chunks to return.
        doc_id:    Optional filter to restrict search to one document.
        threshold: Minimum cosine similarity to include a chunk.

    Returns:
        Ranked list of SourceChunk objects.
    """
    sb = get_supabase()

    # Embed the query locally (no API cost)
    query_vector = embed_query(query)

    # Call the match_chunks PostgreSQL RPC function
    params: dict = {
        "query_embedding": query_vector,
        "match_count": top_k,
    }
    if doc_id:
        params["filter_doc_id"] = doc_id

    try:
        result = sb.rpc("match_chunks", params).execute()
    except Exception as exc:
        logger.error(f"Supabase RPC error: {exc}")
        raise

    chunks: list[SourceChunk] = []
    for row in result.data or []:
        sim = float(row.get("similarity", 0.0))
        if sim < threshold:
            continue
        meta = row.get("metadata") or {}
        chunks.append(
            SourceChunk(
                content=row["content"],
                page=meta.get("page"),
                source=meta.get("source", "human-nutrition-text.pdf"),
                similarity=round(sim, 4),
            )
        )

    logger.info(f"Retrieved {len(chunks)} chunks for query: '{query[:60]}...'")
    return chunks


def check_supabase_connection() -> bool:
    """Quick connectivity check used by /health endpoint."""
    try:
        sb = get_supabase()
        sb.table("chunks").select("id").limit(1).execute()
        return True
    except Exception:
        return False
