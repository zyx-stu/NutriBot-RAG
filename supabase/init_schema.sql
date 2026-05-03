-- ============================================================
-- supabase/schema.sql
-- NutriBot RAG — Supabase pgvector schema
--
-- IMPORTANT: Run this in the Supabase SQL Editor BEFORE ingesting.
-- If you previously had a chunks table with vector(1536),
-- this script drops and recreates it for vector(384).
-- ============================================================

-- 1. Enable pgvector extension
create extension if not exists vector;

-- 2. Drop old table (was vector(1536) with OpenAI embeddings)
drop table if exists chunks;

-- 3. Create new table with 384-dim vectors (all-MiniLM-L6-v2)
create table chunks (
  id           uuid primary key default gen_random_uuid(),
  doc_id       text        not null,
  chunk_index  int         not null,
  content      text        not null,
  metadata     jsonb,
  embedding    vector(384)           -- SentenceTransformers all-MiniLM-L6-v2
);

-- 4. IVFFlat index for fast approximate cosine search
--    (set lists ≈ sqrt(total_rows); 100 is fine for < 10 000 chunks)
create index chunks_embedding_idx
  on chunks
  using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

-- 5. Index on doc_id for filtered searches
create index chunks_doc_id_idx on chunks (doc_id);

-- 6. RPC function called by the Python retriever
--    Returns rows ordered by cosine similarity (highest first).
create or replace function match_chunks(
  query_embedding  vector(384),
  match_count      int     default 5,
  filter_doc_id    text    default null
)
returns table (
  id           uuid,
  doc_id       text,
  chunk_index  int,
  content      text,
  metadata     jsonb,
  similarity   float
)
language plpgsql
as $$
begin
  return query
  select
    c.id,
    c.doc_id,
    c.chunk_index,
    c.content,
    c.metadata,
    1 - (c.embedding <=> query_embedding) as similarity
  from chunks c
  where (filter_doc_id is null or c.doc_id = filter_doc_id)
  order by c.embedding <=> query_embedding
  limit match_count;
end;
$$;

-- Done! Now run: python ingest.py
