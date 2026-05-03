"""
ingest_data.py — NutriBot PDF ingestion pipeline.

Embedding strategy (auto-detected, best available):
  1. LOCAL (Colab/machine with torch) → sentence-transformers  [FASTEST, RECOMMENDED]
  2. HF Inference API                 → cloud, no torch needed [FALLBACK]

Google Colab quick-start:
  !pip install pymupdf supabase sentence-transformers python-dotenv tqdm
  !python ingest_data.py

Minimal local (no torch):
  !pip install pymupdf supabase requests python-dotenv tqdm
  !python ingest_data.py      ← uses HF API automatically

Steps:
  1. Fill .env with SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, HF_TOKEN
  2. Run supabase/init_schema.sql in Supabase SQL Editor
  3. python ingest_data.py
"""

import os, re, sys, time
import fitz                              # PyMuPDF
from tqdm import tqdm
from dotenv import load_dotenv, find_dotenv
from supabase import create_client, Client

# ── Load environment ──────────────────────────────────────────────────────────
load_dotenv(find_dotenv(usecwd=True))

SUPABASE_URL              = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
HF_TOKEN                  = os.environ.get("HF_TOKEN", "")

# ── Config ────────────────────────────────────────────────────────────────────
PDF_PATH        = os.environ.get("PDF_PATH", "human-nutrition-text.pdf")
DOC_ID          = "nutrition-v1"
EMBED_MODEL     = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_DIMS      = 384
BATCH_EMBED     = 64    # local: larger batches are fine; API: keep ≤32
BATCH_INSERT    = 200

# Chunking
SENTS_PER_CHUNK = 12
SENT_OVERLAP    = 2
MAX_WORDS       = 350
MIN_WORDS       = 20


# ── Auto-detect embedding backend ─────────────────────────────────────────────

def _try_load_local_model():
    """Try to import sentence-transformers (works in Colab / machines with torch)."""
    try:
        from sentence_transformers import SentenceTransformer
        print(f"🔍 Detected torch — using local sentence-transformers model.")
        model = SentenceTransformer(EMBED_MODEL)
        print(f"✅ Model loaded: {EMBED_MODEL}\n")
        return model
    except ImportError:
        return None

LOCAL_MODEL = _try_load_local_model()
USE_LOCAL   = LOCAL_MODEL is not None

# Updated HF Inference API URL (new 2024+ format)
HF_EMBED_URL = (
    f"https://api-inference.huggingface.co/pipeline/feature-extraction/{EMBED_MODEL}"
)


# ── Text utilities ────────────────────────────────────────────────────────────

def clean_text(t: str) -> str:
    t = t.replace("\r", " ")
    t = re.sub(r"-\s*\n\s*", "", t)
    t = re.sub(r"\s+\n", "\n", t)
    t = re.sub(r"[ \t]+", " ", t)
    return t.replace("\n", " ").strip()


def split_sentences(text: str) -> list:
    sents = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sents if s.strip()]


def chunk_text(text, sents_per=SENTS_PER_CHUNK, overlap=SENT_OVERLAP,
               max_words=MAX_WORDS, min_words=MIN_WORDS):
    sents = split_sentences(text)
    step  = max(1, sents_per - overlap)
    i = 0
    while i < len(sents):
        piece = sents[i:i + sents_per]
        if not piece:
            break
        chunk = " ".join(piece)
        while len(chunk.split()) > max_words and len(piece) > 1:
            piece = piece[:-1]
            chunk = " ".join(piece)
        if len(chunk.split()) >= min_words:
            yield chunk
        i += step


def pdf_pages(path: str):
    doc = fitz.open(path)
    try:
        for i in range(len(doc)):
            txt = doc[i].get_text("text") or ""
            yield (i + 1, clean_text(txt))
    finally:
        doc.close()


# ── Embedding functions ───────────────────────────────────────────────────────

def embed_local(texts: list) -> list:
    """Embed using local sentence-transformers (Colab / torch available)."""
    vecs = LOCAL_MODEL.encode(
        texts,
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return vecs.tolist()


def embed_hf_api(texts: list, retry: int = 4) -> list:
    """
    Embed via HuggingFace Inference API.
    Uses the updated /pipeline/feature-extraction/ endpoint (2024+ format).
    """
    import requests

    headers = {"Content-Type": "application/json"}
    if HF_TOKEN:
        headers["Authorization"] = f"Bearer {HF_TOKEN}"
    else:
        print("\n⚠️  HF_TOKEN not set — API may rate-limit or reject. "
              "Get a free token at huggingface.co/settings/tokens")

    for attempt in range(retry):
        resp = requests.post(
            HF_EMBED_URL,
            headers=headers,
            json={"inputs": texts, "options": {"wait_for_model": True}},
            timeout=90,
        )

        if resp.status_code == 503:
            wait = 25 * (attempt + 1)
            print(f"\n⏳ HF model loading, retrying in {wait}s…")
            time.sleep(wait)
            continue

        if not resp.ok:
            raise RuntimeError(
                f"HF API error {resp.status_code}: {resp.text[:400]}\n"
                f"URL tried: {HF_EMBED_URL}\n"
                f"Tip: Install sentence-transformers to use local embedding instead:\n"
                f"     !pip install sentence-transformers"
            )

        data = resp.json()

        # Shape: [batch, 384]
        if isinstance(data, list) and data and isinstance(data[0], list) \
                and isinstance(data[0][0], float):
            return data

        # Shape: [batch, seq_len, 384] — mean-pool
        if isinstance(data, list) and data and isinstance(data[0], list) \
                and isinstance(data[0][0], list):
            pooled = []
            for token_embs in data:
                dim = len(token_embs[0])
                mean_vec = [
                    sum(t[d] for t in token_embs) / len(token_embs)
                    for d in range(dim)
                ]
                pooled.append(mean_vec)
            return pooled

        raise ValueError(f"Unexpected HF API response shape: {str(data)[:200]}")

    raise RuntimeError("HF Inference API failed after all retries.")


def embed_batch(texts: list) -> list:
    """Route to local model or HF API depending on what's available."""
    if USE_LOCAL:
        return embed_local(texts)
    else:
        return embed_hf_api(texts)


# ── Main pipeline ─────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(PDF_PATH):
        sys.exit(f"❌ PDF not found: {PDF_PATH}")

    backend = "sentence-transformers (local)" if USE_LOCAL else f"HuggingFace API ({EMBED_MODEL})"
    print(f"🧠 Embedding backend: {backend}\n")

    # Connect to Supabase
    sb: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    # Remove previous chunks (idempotent re-run)
    print(f"🗑  Removing existing chunks for doc_id='{DOC_ID}'…")
    sb.table("chunks").delete().eq("doc_id", DOC_ID).execute()

    # Build chunk corpus
    print(f"📄 Reading PDF: {PDF_PATH}")
    texts, metas = [], []
    for page_no, page_text in pdf_pages(PDF_PATH):
        if not page_text:
            continue
        for chunk in chunk_text(page_text):
            texts.append(chunk)
            metas.append({"page": page_no, "source": os.path.basename(PDF_PATH)})

    total_pages = len(set(m["page"] for m in metas))
    print(f"✅ Built {len(texts)} chunks from {total_pages} pages\n")

    # Embed
    batch_size = BATCH_EMBED if USE_LOCAL else 32
    label = "Embedding (local)" if USE_LOCAL else "Embedding (HF API)"
    all_vectors = []

    for i in tqdm(range(0, len(texts), batch_size), desc=label):
        batch = texts[i:i + batch_size]
        vecs  = embed_batch(batch)
        all_vectors.extend(vecs)
        # Rate-limit pause for API mode only
        if not USE_LOCAL and i > 0 and i % (batch_size * 5) == 0:
            time.sleep(1)

    print(f"\n✅ Generated {len(all_vectors)} vectors ({EMBED_DIMS}d each)\n")

    # Upload to Supabase
    rows = [
        {
            "doc_id":      DOC_ID,
            "chunk_index": idx,
            "content":     content,
            "metadata":    meta,
            "embedding":   emb,
        }
        for idx, (content, emb, meta) in enumerate(zip(texts, all_vectors, metas))
    ]

    print(f"☁️  Uploading {len(rows)} rows to Supabase…")
    for j in tqdm(range(0, len(rows), BATCH_INSERT), desc="Uploading"):
        sb.table("chunks").insert(rows[j:j + BATCH_INSERT]).execute()

    print(f"\n🎉 Done! Inserted {len(rows)} chunks for doc_id='{DOC_ID}'")
    print("   Deploy the frontend to Vercel and start chatting!")


if __name__ == "__main__":
    main()
