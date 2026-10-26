import os
from pathlib import Path

import pytest

from app.sessions import DocumentSession, get_session_store

# Prevent OpenMP and Tokenizer threadpool deadlocks / segfaults during full test runs
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TOKENIZERS_PARALLELISM"] = "false"


@pytest.fixture(scope="session")
def session_handbook() -> DocumentSession:
    """Session-scoped ingested index fixture for handbook.pdf per FIX 14."""
    store = get_session_store()
    sid = "sess_shared_handbook"
    session = store.get_session(sid)
    if not session:
        fixture_path = Path(__file__).resolve().parent.parent.parent / "eval" / "fixtures" / "handbook.pdf"
        with open(fixture_path, "rb") as f:
            session = store.create_session_from_bytes("handbook.pdf", f.read())
            session.session_id = sid
            store._sessions[sid] = session
    return session


@pytest.fixture(scope="session")
def session_scanned_handbook() -> DocumentSession:
    """Session-scoped ingested index fixture for scanned_handbook.pdf per FIX 14."""
    store = get_session_store()
    sid = "sess_scanned_handbook"
    session = store.get_session(sid)
    if not session:
        fixture_path = Path(__file__).resolve().parent.parent.parent / "eval" / "fixtures" / "scanned_handbook.pdf"
        with open(fixture_path, "rb") as f:
            session = store.create_session_from_bytes("scanned_handbook.pdf", f.read())
            session.session_id = sid
            store._sessions[sid] = session
    return session
