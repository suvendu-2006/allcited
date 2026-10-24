-- Allcited Supabase Schema Migration (Phase 5 / Step 25)
-- Enables pgvector, creates all required tables, and enforces Row-Level Security (RLS) keyed to Clerk user_id.

-- 1. Extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. saved_documents table
CREATE TABLE IF NOT EXISTS saved_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    format TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    page_count INT DEFAULT 1 NOT NULL,
    chunk_count INT DEFAULT 0 NOT NULL,
    doc_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_saved_documents_user ON saved_documents(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_documents_hash ON saved_documents(user_id, doc_hash);

-- 3. saved_chunks table (with 384-dim vector embedding & HNSW index)
CREATE TABLE IF NOT EXISTS saved_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES saved_documents(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    chunk_id TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    text TEXT NOT NULL,
    section_path TEXT[] DEFAULT '{}' NOT NULL,
    page INT,
    token_count INT DEFAULT 0 NOT NULL,
    embedding vector(384) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_saved_chunks_user_doc ON saved_chunks(user_id, document_id);
CREATE INDEX IF NOT EXISTS idx_saved_chunks_content_hash ON saved_chunks(content_hash);

-- HNSW cosine index for 384-dimensional dense vector search
CREATE INDEX IF NOT EXISTS idx_saved_chunks_embedding 
ON saved_chunks 
USING hnsw (embedding vector_cosine_ops);

-- 4. subscriptions table (Free / Pro plan tier gates)
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL UNIQUE,
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    plan TEXT NOT NULL DEFAULT 'free',
    status TEXT NOT NULL DEFAULT 'active',
    current_period_end TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);

-- 5. feedback table (online quality capture for thumb-down / thumb-up)
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT,
    session_id TEXT,
    question_id TEXT NOT NULL,
    query TEXT NOT NULL,
    answer TEXT NOT NULL,
    score INT NOT NULL CHECK (score IN (-1, 1)),
    note TEXT,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_feedback_question ON feedback(question_id);
CREATE INDEX IF NOT EXISTS idx_feedback_score ON feedback(score);

-- 6. audit_log table
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT,
    action TEXT NOT NULL,
    details JSONB DEFAULT '{}'::jsonb NOT NULL,
    ip_address TEXT,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_log_user_action ON audit_log(user_id, action);

-- 7. GraphRAG-lite tables (graph_nodes and graph_edges)
CREATE TABLE IF NOT EXISTS graph_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    document_id UUID NOT NULL REFERENCES saved_documents(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_graph_nodes_user_doc ON graph_nodes(user_id, document_id);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_name ON graph_nodes(user_id, name);

CREATE TABLE IF NOT EXISTS graph_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    document_id UUID NOT NULL REFERENCES saved_documents(id) ON DELETE CASCADE,
    source_node_id UUID NOT NULL REFERENCES graph_nodes(id) ON DELETE CASCADE,
    target_node_id UUID NOT NULL REFERENCES graph_nodes(id) ON DELETE CASCADE,
    relation TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_graph_edges_user_doc ON graph_edges(user_id, document_id);

-- =========================================================================
-- 8. ROW LEVEL SECURITY (RLS) POLICIES
-- Clerk authenticates via JWT containing the 'sub' claim with user_id.
-- =========================================================================

-- Enable RLS on all user-scoped tables
ALTER TABLE saved_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE graph_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE graph_edges ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;

-- saved_documents policies
CREATE POLICY "Users can only select their own documents"
    ON saved_documents FOR SELECT
    TO authenticated
    USING (user_id = (auth.jwt() ->> 'sub'));

CREATE POLICY "Users can only insert their own documents"
    ON saved_documents FOR INSERT
    TO authenticated
    WITH CHECK (user_id = (auth.jwt() ->> 'sub'));

CREATE POLICY "Users can only update their own documents"
    ON saved_documents FOR UPDATE
    TO authenticated
    USING (user_id = (auth.jwt() ->> 'sub'))
    WITH CHECK (user_id = (auth.jwt() ->> 'sub'));

CREATE POLICY "Users can only delete their own documents"
    ON saved_documents FOR DELETE
    TO authenticated
    USING (user_id = (auth.jwt() ->> 'sub'));

-- saved_chunks policies
CREATE POLICY "Users can only select their own chunks"
    ON saved_chunks FOR SELECT
    TO authenticated
    USING (user_id = (auth.jwt() ->> 'sub'));

CREATE POLICY "Users can only insert their own chunks"
    ON saved_chunks FOR INSERT
    TO authenticated
    WITH CHECK (user_id = (auth.jwt() ->> 'sub'));

CREATE POLICY "Users can only update their own chunks"
    ON saved_chunks FOR UPDATE
    TO authenticated
    USING (user_id = (auth.jwt() ->> 'sub'))
    WITH CHECK (user_id = (auth.jwt() ->> 'sub'));

CREATE POLICY "Users can only delete their own chunks"
    ON saved_chunks FOR DELETE
    TO authenticated
    USING (user_id = (auth.jwt() ->> 'sub'));

-- subscriptions policies
CREATE POLICY "Users can only view their own subscription"
    ON subscriptions FOR SELECT
    TO authenticated
    USING (user_id = (auth.jwt() ->> 'sub'));

-- graph_nodes policies
CREATE POLICY "Users can only access their own graph nodes"
    ON graph_nodes FOR ALL
    TO authenticated
    USING (user_id = (auth.jwt() ->> 'sub'))
    WITH CHECK (user_id = (auth.jwt() ->> 'sub'));

-- graph_edges policies
CREATE POLICY "Users can only access their own graph edges"
    ON graph_edges FOR ALL
    TO authenticated
    USING (user_id = (auth.jwt() ->> 'sub'))
    WITH CHECK (user_id = (auth.jwt() ->> 'sub'));

-- audit_log policies
CREATE POLICY "Users can view their own audit log"
    ON audit_log FOR SELECT
    TO authenticated
    USING (user_id = (auth.jwt() ->> 'sub'));

-- feedback policies (anyone authenticated or anon can submit feedback)
CREATE POLICY "Anyone can submit feedback"
    ON feedback FOR INSERT
    TO anon, authenticated
    WITH CHECK (true);

-- Backend Service Role Bypass Policies (FastAPI server uses service role key)
CREATE POLICY "Service role full access on saved_documents"
    ON saved_documents FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access on saved_chunks"
    ON saved_chunks FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access on subscriptions"
    ON subscriptions FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access on graph_nodes"
    ON graph_nodes FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access on graph_edges"
    ON graph_edges FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access on audit_log"
    ON audit_log FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access on feedback"
    ON feedback FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
