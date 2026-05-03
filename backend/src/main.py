"""
main.py — FastAPI application entry-point for NutriBot RAG backend.

Endpoints:
  GET  /health          → readiness / status check
  POST /api/v1/chat     → RAG chat (embed → retrieve → generate)
"""

from __future__ import annotations
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import APP_TITLE, APP_VERSION, CORS_ORIGINS, GROQ_MODEL, EMBED_MODEL_NAME
from .models import ChatRequest, ChatResponse, HealthResponse
from .embeddings import get_embed_model
from .retriever import retrieve, check_supabase_connection
from .llm import generate_answer

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan: warm-up on startup ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting NutriBot RAG API…")
    # Pre-load embedding model so first request isn't slow
    get_embed_model()
    logger.info("✅ Embedding model ready")
    yield
    logger.info("🛑 Shutting down NutriBot RAG API")


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=(
        "Production-level RAG chatbot for nutrition questions. "
        "Uses SentenceTransformers embeddings + Supabase pgvector + Groq LLM."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["Meta"])
async def health():
    """Liveness & readiness check."""
    return HealthResponse(
        status="ok",
        version=APP_VERSION,
        embed_model=EMBED_MODEL_NAME,
        llm_model=GROQ_MODEL,
        supabase_connected=check_supabase_connection(),
    )


@app.post("/api/v1/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(req: ChatRequest):
    """
    Main RAG endpoint.

    1. Embed the user query locally (SentenceTransformers)
    2. Retrieve top-K relevant chunks from Supabase pgvector
    3. Generate an answer via Groq (free tier) with the chunks as context
    """
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # ── Step 1 & 2: Retrieve ─────────────────────────────────────────────────
    try:
        chunks = retrieve(
            query=query,
            top_k=req.top_k or 5,
            doc_id=req.doc_id,
        )
    except Exception as exc:
        logger.error(f"Retrieval failed: {exc}")
        raise HTTPException(status_code=502, detail=f"Vector search failed: {exc}")

    # ── Step 3: Generate ─────────────────────────────────────────────────────
    try:
        answer, tokens = generate_answer(
            query=query,
            chunks=chunks,
            history=req.conversation_history,
        )
    except Exception as exc:
        logger.error(f"LLM generation failed: {exc}")
        raise HTTPException(status_code=502, detail=f"LLM generation failed: {exc}")

    return ChatResponse(
        answer=answer,
        sources=chunks,
        model=GROQ_MODEL,
        query=query,
        tokens_used=tokens,
    )
