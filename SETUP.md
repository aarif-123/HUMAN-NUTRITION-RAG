# 🛠️ Nutri-RAG — Supabase Setup Guide

This guide covers the exact SQL you need to run in Supabase to set up the vector store for Nutri-RAG.

---

## Step 1 — Enable pgvector

In your Supabase project → **SQL Editor**, run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## Step 2 — Create the `chunks` Table

```sql
CREATE TABLE IF NOT EXISTS public.chunks (
    id          bigserial   PRIMARY KEY,
    doc_id      text        NOT NULL,
    chunk_index integer     NOT NULL DEFAULT 0,
    content     text        NOT NULL,
    metadata    jsonb       DEFAULT '{}'::jsonb,
    embedding   vector(768) NULL,           -- 768 dims = E5-base-v2
    created_at  timestamptz DEFAULT now()
);

-- Index for faster vector search (IVFFlat — good for < 1M rows)
CREATE INDEX IF NOT EXISTS chunks_embedding_idx
    ON public.chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Index for document lookups
CREATE INDEX IF NOT EXISTS chunks_doc_id_idx
    ON public.chunks (doc_id);
```

---

## Step 3 — Create the `match_documents` RPC Function

```sql
CREATE OR REPLACE FUNCTION public.match_documents(
    query_embedding vector(768),
    match_count     integer DEFAULT 5
)
RETURNS TABLE (
    doc_id      text,
    chunk_index integer,
    content     text,
    metadata    jsonb,
    similarity  float
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.doc_id,
        c.chunk_index,
        c.content,
        c.metadata,
        -- Cosine similarity = 1 - cosine distance
        (1 - (c.embedding <=> query_embedding))::float AS similarity
    FROM public.chunks c
    WHERE c.embedding IS NOT NULL
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

---

## Step 4 — Set Row Level Security (RLS)

For a backend-only API using the service role key, you can disable RLS on the chunks table:

```sql
-- Allow service role unrestricted access (safe since RLS is bypassed by service_role)
ALTER TABLE public.chunks ENABLE ROW LEVEL SECURITY;

-- Optional: public read policy (only if you want unauthenticated reads)
-- CREATE POLICY "Allow public reads" ON public.chunks FOR SELECT USING (true);
```

---

## Step 5 — Verify Setup

```sql
-- Should return 0 rows (empty table before ingestion)
SELECT count(*) FROM public.chunks;

-- Should show the match_documents function
SELECT routine_name FROM information_schema.routines
WHERE routine_schema = 'public' AND routine_name = 'match_documents';
```

---

## Notes

- **Embedding dimensions**: The table is created with `vector(768)` to match `jeffh/intfloat-e5-base-v2:f16`. If you switch embedding models, you must recreate the table with the correct dimension.
- **IVFFlat index**: The `lists = 100` parameter is a starting point. For production with > 100k rows, increase `lists` (Supabase recommends `sqrt(row_count)`).
- **Service Role Key**: Always use the **service role** key in your backend `.env`, never the anon key. The service role bypasses RLS and is required for inserts from `ingest.py`.
