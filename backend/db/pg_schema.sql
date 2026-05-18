-- PostgreSQL schema with pgvector for RAG
CREATE EXTENSION IF NOT EXISTS pgvector;

CREATE TABLE IF NOT EXISTS components (
    id SERIAL PRIMARY KEY,
    lib_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    mpn TEXT,
    category TEXT,
    manufacturer TEXT,
    package TEXT,
    jlc_part TEXT,
    price REAL,
    stock INTEGER DEFAULT 9999,
    description TEXT,
    pins_json TEXT DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS component_embeddings (
    id SERIAL PRIMARY KEY,
    component_id INTEGER REFERENCES components(id) ON DELETE CASCADE,
    description_text TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_embedding_cosine
    ON component_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);