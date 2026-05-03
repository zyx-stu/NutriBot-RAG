"""
embeddings.py — Cloud-based embeddings via HuggingFace Inference API.

NO local torch / sentence-transformers needed.
Model: all-MiniLM-L6-v2 → 384-dim vectors (FREE via HF Inference API)
"""

from __future__ import annotations
import time
import logging
import requests
from .config import HF_TOKEN, HF_EMBED_URL

logger = logging.getLogger(__name__)


def _hf_embed(texts: list[str], retry: int = 3) -> list[list[float]]:
    """Call HF Inference API and return list of 384-dim vectors."""
    headers = {"Content-Type": "application/json"}
    if HF_TOKEN:
        headers["Authorization"] = f"Bearer {HF_TOKEN}"

    for attempt in range(retry):
        resp = requests.post(
            HF_EMBED_URL,
            headers=headers,
            json={"inputs": texts, "options": {"wait_for_model": True}},
            timeout=60,
        )

        if resp.status_code == 503:
            wait = 20 * (attempt + 1)
            logger.warning(f"HF model loading, retrying in {wait}s…")
            time.sleep(wait)
            continue

        resp.raise_for_status()
        data = resp.json()

        # Shape [batch, 384]
        if data and isinstance(data[0], list) and isinstance(data[0][0], float):
            return data  # type: ignore[return-value]

        # Shape [batch, seq_len, 384] — mean-pool over tokens
        if data and isinstance(data[0], list) and isinstance(data[0][0], list):
            pooled = []
            for token_embs in data:
                dim = len(token_embs[0])
                mean_vec = [
                    sum(t[d] for t in token_embs) / len(token_embs)
                    for d in range(dim)
                ]
                pooled.append(mean_vec)
            return pooled

        raise ValueError(f"Unexpected HF response shape: {str(data)[:200]}")

    raise RuntimeError("HF Inference API failed after all retries.")


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of strings. Returns list of 384-dim float vectors."""
    if not texts:
        return []
    logger.info(f"Embedding {len(texts)} texts via HF Inference API…")
    return _hf_embed(texts)


def embed_query(query: str) -> list[float]:
    """Embed a single query string."""
    result = _hf_embed([query])
    return result[0]
