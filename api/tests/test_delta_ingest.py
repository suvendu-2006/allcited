import logging

from fastapi.testclient import TestClient

from app.main import app
from app.pipeline.embed import get_embedding_manager

client = TestClient(app)


def test_delta_reingest_skips_unchanged_chunks_and_logs(caplog):
    """
    Gate check for STEP 31:
    Re-uploading an edited doc re-embeds only changed chunks;
    log and response show accurate skip counts.
    """
    emb_manager = get_embedding_manager()
    emb_manager.clear_cache()

    sec1 = (
        "This is the corporate intro section describing our mission and company principles. " * 35
    )
    sec2 = (
        "This policy governs employee leave entitlements, sick days, and vacation accrual rules. "
        * 35
    )
    sec3 = (
        "Security credential protocols mandate multi-factor authentication and 16-character keys. "
        * 35
    )

    doc_v1 = f"# 1. Mission and Overview\n{sec1}\n\n# 2. Leave Policy\n{sec2}\n\n# 3. Security Protocols\n{sec3}"

    # 1. First ingest (Initial upload)
    with caplog.at_level(logging.INFO):
        resp1 = client.post(
            "/v1/ingest",
            files={"file": ("guide.md", doc_v1.encode("utf-8"), "text/markdown")},
        )
    assert resp1.status_code == 200
    data1 = resp1.json()
    total1 = data1["chunk_count"]
    assert total1 >= 3
    assert data1["new_chunks"] == total1
    assert data1["reused_chunks"] == 0

    # Verify log output for initial upload
    assert any(
        f"{total1} total chunks, 0 reused/skipped, {total1} newly embedded" in record.message
        for record in caplog.records
    )

    caplog.clear()

    # 2. Re-upload IDENTICAL document (Exact duplicate)
    with caplog.at_level(logging.INFO):
        resp2 = client.post(
            "/v1/ingest",
            files={"file": ("guide.md", doc_v1.encode("utf-8"), "text/markdown")},
        )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["chunk_count"] == total1
    assert data2["reused_chunks"] == total1
    assert data2["new_chunks"] == 0

    # Verify log output shows 100% skip
    assert any(
        f"{total1} total chunks, {total1} reused/skipped, 0 newly embedded" in record.message
        for record in caplog.records
    )

    caplog.clear()

    # 3. Re-upload EDITED document: Section 1 & 2 unchanged, Section 3 modified, Section 4 added
    sec3_edited = "Updated security rules require 24-character passwords and YubiKey tokens. " * 35
    sec4_new = (
        "New statutory schedules define severance pay formulas and travel expense stipends. " * 35
    )
    doc_v2 = f"# 1. Mission and Overview\n{sec1}\n\n# 2. Leave Policy\n{sec2}\n\n# 3. Security Protocols\n{sec3_edited}\n\n# 4. Statutory Schedules\n{sec4_new}"

    with caplog.at_level(logging.INFO):
        resp3 = client.post(
            "/v1/ingest",
            files={"file": ("guide.md", doc_v2.encode("utf-8"), "text/markdown")},
        )
    assert resp3.status_code == 200
    data3 = resp3.json()
    assert data3["chunk_count"] >= 3
    # The unchanged chunks from sec1 and sec2 are skipped/reused from hash cache
    assert data3["reused_chunks"] >= 1
    # The modified section 3 and new section 4 are newly embedded
    assert data3["new_chunks"] >= 1

    # Verify log output shows delta skip counts
    assert any(
        f"{data3['reused_chunks']} reused/skipped, {data3['new_chunks']} newly embedded"
        in record.message
        for record in caplog.records
    )
