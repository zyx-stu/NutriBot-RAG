"""
config.py — Central configuration for NutriBot RAG backend.
All services are cloud-based — no heavy local installs needed.
"""

import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=True))

# ── Supabase ──────────────────────────────────────────────────────────────────
SUPABASE_URL: str              = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

# ── Groq — free LLM API (console.groq.com) ───────────────────────────────────
GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL: str   = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")

# ── HuggingFace Inference API — free embeddings (huggingface.co/settings/tokens)
HF_TOKEN: str     = os.environ.get("HF_TOKEN", "")
HF_EMBED_MODEL    = "sentence-transformers/all-MiniLM-L6-v2"
HF_EMBED_URL: str = f"https://api-inference.huggingface.co/models/{HF_EMBED_MODEL}"
EMBED_DIMS: int   = 384

# ── Ingestion ─────────────────────────────────────────────────────────────────
PDF_PATH: str   = os.environ.get("PDF_PATH", "human-nutrition-text.pdf")
DOC_ID: str     = "nutrition-v1"
BATCH_INSERT: int = 200

# ── Retrieval ─────────────────────────────────────────────────────────────────
TOP_K: int                  = int(os.environ.get("TOP_K", "5"))
SIMILARITY_THRESHOLD: float = float(os.environ.get("SIMILARITY_THRESHOLD", "0.35"))

# ── App ───────────────────────────────────────────────────────────────────────
APP_TITLE: str    = "NutriBot RAG API"
APP_VERSION: str  = "2.0.0"
CORS_ORIGINS: list[str] = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://*.vercel.app",
    "https://*.render.com",
]
