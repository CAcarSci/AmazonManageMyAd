create extension if not exists vector;

create table
    if not exists keyword_chunks (
        chunk_id bigserial primary key,
        category_id text,
        chunk text,
        meta jsonb,
        embedding vector (768)
    );

create index if not exists idx_keyword_chunks_vec on keyword_chunks using ivfflat (embedding vector_cosine_ops)
with
    (lists = 100);