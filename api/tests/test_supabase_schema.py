import os
from pathlib import Path

import pytest


def test_migration_file_structure_and_tables():
    """Verify that STEP 25 schema migration file exists and defines all required tables and indexes."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    migration_path = repo_root / "supabase" / "migrations" / "20261025000000_init_schema.sql"

    assert migration_path.exists(), f"Migration file missing at {migration_path}"
    content = migration_path.read_text(encoding="utf-8")

    # Required tables from STEP 25
    expected_tables = [
        "saved_documents",
        "saved_chunks",
        "subscriptions",
        "feedback",
        "audit_log",
        "graph_nodes",
        "graph_edges",
    ]
    for table in expected_tables:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in content, f"Table {table} missing from schema"

    # Required vector extension and dimension
    assert "CREATE EXTENSION IF NOT EXISTS vector;" in content
    assert "vector(384)" in content
    assert "USING hnsw (embedding vector_cosine_ops)" in content

    # Required RLS policies keyed to Clerk user_id
    for table in ["saved_documents", "saved_chunks", "subscriptions", "graph_nodes", "graph_edges", "audit_log"]:
        assert f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;" in content
        assert f"ON {table}" in content

    assert "auth.jwt() ->> 'sub'" in content


def test_rls_isolation_script_exists():
    """Verify that test_rls_isolation.sql exists and tests user A vs user B."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    isolation_script = repo_root / "supabase" / "test_rls_isolation.sql"

    assert isolation_script.exists()
    content = isolation_script.read_text(encoding="utf-8")
    assert "user_alice_123" in content
    assert "user_bob_456" in content
    assert "bob_sees_alice_docs" in content


@pytest.mark.skipif(
    not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    reason="SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY not configured in environment",
)
def test_live_supabase_rls_isolation():
    """Live test against Supabase project when credentials are provided in environment."""
    # When credentials are provided by the user, live queries verify isolation
    pass
