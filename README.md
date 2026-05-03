<div align="center">

<img src="https://img.shields.io/badge/NutriBot-RAG%20Chatbot-2d6a4f?style=for-the-badge&logo=leaflet&logoColor=white" height="40"/>

# 🥗 NutriBot — AI Nutrition Chatbot

### A production-ready, fully free RAG (Retrieval-Augmented Generation) chatbot  
### that answers nutrition questions grounded in a real textbook.

<br/>

[![Next.js](https://img.shields.io/badge/Next.js_16-black?style=flat-square&logo=next.js)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Supabase](https://img.shields.io/badge/Supabase_pgvector-3ECF8E?style=flat-square&logo=supabase&logoColor=white)](https://supabase.com)
[![Groq](https://img.shields.io/badge/Groq_Llama_3.1-F55036?style=flat-square&logo=meta&logoColor=white)](https://console.groq.com)
[![HuggingFace](https://img.shields.io/badge/HuggingFace_Embeddings-FFD21E?style=flat-square&logo=huggingface&logoColor=black)](https://huggingface.co)
[![Vercel](https://img.shields.io/badge/Deploy-Vercel-black?style=flat-square&logo=vercel)](https://vercel.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

<br/>

> 💡 **Zero paid APIs. Zero GPU. Zero monthly cost.**  
> Built with HuggingFace embeddings + Supabase pgvector + Groq Llama 3.1

</div>

---

## 📸 Preview

> NutriBot answers questions about macronutrients, vitamins, diet plans, and more —  
> with source citations pointing to the exact textbook page.

```
User: "What are the best sources of protein for muscle building?"

NutriBot: "Great question! According to the Human Nutrition textbook [1][2]:

• Complete proteins (all essential amino acids): eggs, meat, fish, dairy, soy
• Plant-based combinations: rice + beans, hummus + pita
• Leucine-rich foods trigger muscle protein synthesis most effectively

[1] Page 142 — Protein Quality and Digestibility  
[2] Page 156 — Sports Nutrition and Muscle Recovery"
```

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER'S BROWSER                               │
│                   Next.js Chat Interface                            │
│           (Dark green UI, source citations, typing dots)            │
└─────────────────────┬───────────────────────────────────────────────┘
                      │ POST /api/chat
                      │ { message, history }
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│              VERCEL SERVERLESS FUNCTION                             │
│              frontend/app/api/chat/route.ts                         │
│                                                                     │
│   Step 1 ──► Step 2 ──────────────────► Step 3                     │
│   EMBED       RETRIEVE                   GENERATE                   │
└──────┬──────────────┬────────────────────────┬──────────────────────┘
       │              │                        │
       ▼              ▼                        ▼
┌─────────────┐ ┌──────────────────┐ ┌────────────────────┐
│ HuggingFace │ │     Supabase     │ │    Groq Cloud      │
│ Inference   │ │    pgvector DB   │ │  Llama 3.1 8B      │
│    API      │ │                  │ │                    │
│             │ │  match_chunks()  │ │  "You are         │
│ all-MiniLM  │ │  cosine search   │ │   NutriBot..."    │
│  -L6-v2     │ │  returns top-5   │ │                    │
│  (384 dims) │ │  most relevant   │ │  Context + Query  │
│             │ │  text chunks     │ │  → Answer          │
│  query →    │ │  from textbook   │ │                    │
│  [0.12,     │ │                  │ │  grounded answer  │
│   0.84,...] │ │                  │ │  + citations      │
└─────────────┘ └──────────────────┘ └────────────────────┘
  FREE API ✅       FREE tier ✅         FREE tier ✅
```

---

## 🔄 Data Flow (End to End)

```
                        ┌─── ONE-TIME SETUP ────────────────────────────────┐
                        │                                                   │
  human-nutrition-      │   ingest_data.py                                  │
  text.pdf (30MB)  ───► │                                                   │
                        │   1. PyMuPDF extracts text page by page           │
                        │   2. Text split into ~1645 overlapping chunks     │
                        │   3. SentenceTransformers encodes each chunk      │
                        │      → 384-dimensional vector                     │
                        │   4. Vectors + text stored in Supabase pgvector   │
                        │                                                   │
                        └───────────────────────────────────────────────────┘

                        ┌─── EVERY CHAT MESSAGE ────────────────────────────┐
                        │                                                   │
  "What is              │   /api/chat  (Vercel serverless)                  │
   vitamin C?" ──────►  │                                                   │
                        │   1. HuggingFace API embeds the user query        │
                        │      "What is vitamin C?" → [0.12, 0.84, ...]    │
                        │                                                   │
                        │   2. Supabase runs cosine similarity search       │
                        │      Finds top-5 chunks most similar to query     │
                        │                                                   │
                        │   3. Groq Llama 3.1 receives:                     │
                        │      - System prompt (NutriBot persona)           │
                        │      - Retrieved context chunks [1][2][3]...      │
                        │      - Conversation history (last 6 turns)        │
                        │      - User question                              │
                        │      → Generates grounded, cited answer           │
                        │                                                   │
  "Vitamin C is ◄──────  │   4. Response sent back with:                    │
   found in..."         │      { answer, sources[], model, tokens_used }   │
                        │                                                   │
                        └───────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose | Cost |
|-------|-----------|---------|------|
| **Frontend** | Next.js 16 + TypeScript | Chat UI + API routes | Free (Vercel) |
| **Styling** | Vanilla CSS | Dark green premium theme | — |
| **Embeddings** | HuggingFace Inference API | Encode query to 384d vector | Free |
| **Vector DB** | Supabase pgvector | Store & search 1645 chunks | Free (500MB) |
| **LLM** | Groq → Llama 3.1 8B | Generate grounded answers | Free (14k req/day) |
| **Ingestion** | SentenceTransformers + PyMuPDF | PDF → chunks → vectors | Free (Colab) |
| **Hosting** | Vercel | Serverless deployment | Free |

---

## 📁 Project Structure

```
NutriBot-RAG/
│
├── 📂 frontend/                     # Next.js app → deployed to Vercel
│   ├── 📂 app/
│   │   ├── 📄 page.tsx              # Chat UI (sidebar + messages + input)
│   │   ├── 📄 layout.tsx            # HTML layout + SEO metadata
│   │   ├── 📄 globals.css           # Dark green theme + animations
│   │   └── 📂 api/chat/
│   │       └── 📄 route.ts          # ⭐ Core RAG pipeline (embed→retrieve→generate)
│   ├── 📄 .env.local                # API keys (never commit this!)
│   ├── 📄 next.config.ts
│   └── 📄 package.json
│
├── 📂 backend/                      # FastAPI (optional, for Render deployment)
│   ├── 📂 src/
│   │   ├── 📄 main.py               # FastAPI app + /chat + /health endpoints
│   │   ├── 📄 config.py             # Environment variables
│   │   ├── 📄 embeddings.py         # HuggingFace Inference API
│   │   ├── 📄 retriever.py          # Supabase pgvector search
│   │   ├── 📄 llm.py                # Groq integration
│   │   └── 📄 models.py             # Pydantic schemas
│   ├── 📄 run.py                    # uvicorn entry-point
│   └── 📄 requirements.txt          # Lightweight Python deps
│
├── 📂 supabase/
│   └── 📄 init_schema.sql           # ⭐ Run once in Supabase SQL Editor
│
├── 📄 ingest_data.py                # ⭐ PDF ingestion pipeline
├── 📄 human-nutrition-text.pdf      # Source knowledge base
├── 📄 render.yaml                   # One-click Render deployment
├── 📄 .env                          # Root env template
├── 📄 .gitignore
└── 📄 README.md
```

---

## ⚡ Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- Free accounts at: [Supabase](https://supabase.com) · [Groq](https://console.groq.com) · [HuggingFace](https://huggingface.co) · [Vercel](https://vercel.com)

---

### 1️⃣ Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/NutriBot-RAG.git
cd NutriBot-RAG
```

### 2️⃣ Get your free API keys

| Service | Link | Key needed |
|---------|------|-----------|
| Supabase | https://supabase.com → New Project | Project URL + Service Role Key |
| Groq | https://console.groq.com → API Keys | API Key |
| HuggingFace | https://huggingface.co/settings/tokens | Read token |

### 3️⃣ Set up Supabase database

1. Go to your Supabase project → **SQL Editor**
2. Paste contents of `supabase/init_schema.sql` → click **Run**

This creates:
- `chunks` table with 384-dimensional pgvector column
- `match_chunks()` RPC function for cosine similarity search

### 4️⃣ Configure environment variables

Copy and fill in `.env`:
```env
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...
GROQ_API_KEY=gsk_xxxx
GROQ_MODEL=llama-3.1-8b-instant
HF_TOKEN=hf_xxxx
PDF_PATH=human-nutrition-text.pdf
```

Copy and fill in `frontend/.env.local` (same keys + frontend-specific):
```env
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...
GROQ_API_KEY=gsk_xxxx
GROQ_MODEL=llama-3.1-8b-instant
HF_TOKEN=hf_xxxx
TOP_K=5
```

### 5️⃣ Run ingestion (Google Colab — FREE, recommended)

Open [Google Colab](https://colab.research.google.com), upload `ingest_data.py`, `.env`, and `human-nutrition-text.pdf`, then run:

```python
# Cell 1
!pip install pymupdf supabase sentence-transformers python-dotenv tqdm groq

# Cell 2
!python ingest_data.py
```

Expected output:
```
🔍 Detected torch — using local sentence-transformers model.
✅ Model loaded: sentence-transformers/all-MiniLM-L6-v2
✅ Built 1645 chunks from 1134 pages
Embedding (local): 100%|████████| 26/26 [00:04<00:00]
✅ Generated 1645 vectors (384d each)
☁️  Uploading 1645 rows to Supabase…
🎉 Done! Inserted 1645 chunks
```

### 6️⃣ Deploy to Vercel

**Option A — Vercel Dashboard (recommended):**
1. Go to https://vercel.com/new → Import Git Repository → select this repo
2. Set **Root Directory** to `frontend`
3. Add all 6 environment variables from `frontend/.env.local`
4. Click Deploy 🚀

**Option B — Vercel CLI:**
```bash
cd frontend
npx vercel --prod
npx vercel env add SUPABASE_URL
npx vercel env add SUPABASE_SERVICE_ROLE_KEY
npx vercel env add GROQ_API_KEY
npx vercel env add GROQ_MODEL
npx vercel env add HF_TOKEN
npx vercel env add TOP_K
npx vercel --prod
```

---

## 🔌 API Reference

### `POST /api/chat`

**Request:**
```json
{
  "message": "What are symptoms of iron deficiency?",
  "history": [
    { "role": "user", "content": "Tell me about vitamins" },
    { "role": "assistant", "content": "Vitamins are..." }
  ]
}
```

**Response:**
```json
{
  "answer": "Iron deficiency can cause fatigue, pale skin, brittle nails... [1][2]",
  "sources": [
    {
      "content": "Iron is essential for hemoglobin synthesis...",
      "page": 234,
      "source": "human-nutrition-text.pdf",
      "similarity": 0.89
    }
  ],
  "model": "llama-3.1-8b-instant",
  "tokens_used": 387
}
```

---

## 🧠 Embedding Model Details

| Property | Value |
|----------|-------|
| Model | `sentence-transformers/all-MiniLM-L6-v2` |
| Dimensions | 384 |
| Max tokens | 256 |
| Similarity metric | Cosine |
| Chunks in DB | ~1645 |
| Source | Human Nutrition Textbook (1134 pages) |

---

## 🔄 LLM Options (all free on Groq)

Change `GROQ_MODEL` in your env vars:

| Model | Speed | Quality | Best for |
|-------|-------|---------|---------|
| `llama-3.1-8b-instant` | ⚡⚡⚡ Very fast | Good | Default, low latency |
| `llama-3.1-70b-versatile` | ⚡ Medium | Excellent | Complex nutrition questions |
| `mixtral-8x7b-32768` | ⚡⚡ Fast | Very good | Balanced |
| `gemma2-9b-it` | ⚡⚡ Fast | Good | Alternative |

---

## 🚀 Deployment Architecture

```
GitHub (source code)
        │
        │  auto-deploy on push
        ▼
   Vercel (frontend)          Render (optional backend)
   ─────────────────          ───────────────────────
   frontend/                  backend/
   ├── app/page.tsx            ├── src/main.py (FastAPI)
   └── app/api/chat/           ├── src/embeddings.py
       route.ts                ├── src/retriever.py
                               └── src/llm.py
        │                              │
        └──────────────┬───────────────┘
                       │
              ┌────────▼─────────┐
              │  Cloud Services  │
              │                  │
              │  • Supabase DB   │
              │  • Groq API      │
              │  • HuggingFace   │
              └──────────────────┘
```

---

## 📊 Cost Breakdown

| Service | Free Tier Limit | Our Usage | Cost |
|---------|----------------|-----------|------|
| Vercel | Unlimited hobby deploys | 1 project | **$0** |
| Supabase | 500MB storage, unlimited API | ~10MB for 1645 chunks | **$0** |
| Groq | 14,400 requests/day | ~100 req/day typical | **$0** |
| HuggingFace | Rate-limited free inference | Query embedding only | **$0** |
| **Total** | | | **$0/month** |

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/add-meal-planner`)
3. Commit your changes (`git commit -m 'Add meal planner feature'`)
4. Push to the branch (`git push origin feature/add-meal-planner`)
5. Open a Pull Request

---

## 📝 License

MIT © 2025 — Free to use, modify, and distribute.

---

<div align="center">

Built with ❤️ using Next.js · Supabase · Groq · HuggingFace

**[⭐ Star this repo](https://github.com/YOUR_USERNAME/NutriBot-RAG)** if you found it useful!

</div>
