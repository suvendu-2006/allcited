from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.telegram import (
    TelegramClient,
    chat_sessions,
    chunk_telegram_text,
    format_telegram_answer,
    set_telegram_client,
)


class MockTelegramClient(TelegramClient):
    """Mock Telegram client that records outgoing messages and serves local fixtures."""

    def __init__(self, fixture_bytes: Optional[bytes] = None):
        super().__init__(token="mock_token_123")
        self.fixture_bytes = fixture_bytes or b"%PDF-1.4 mock pdf content"
        self.sent_messages: List[Dict[str, Any]] = []
        self.edited_messages: List[Dict[str, Any]] = []
        self.next_msg_id = 100

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: Optional[str] = "Markdown",
    ) -> Dict[str, Any]:
        self.next_msg_id += 1
        msg = {
            "message_id": self.next_msg_id,
            "chat": {"id": chat_id},
            "text": text,
            "parse_mode": parse_mode,
        }
        self.sent_messages.append(msg)
        return {"ok": True, "result": msg}

    async def edit_message_text(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        parse_mode: Optional[str] = "Markdown",
    ) -> Dict[str, Any]:
        msg = {
            "message_id": message_id,
            "chat": {"id": chat_id},
            "text": text,
            "parse_mode": parse_mode,
        }
        self.edited_messages.append(msg)
        return {"ok": True, "result": msg}

    async def get_file_bytes(self, file_id: str) -> bytes:
        return self.fixture_bytes


def test_telegram_secret_token_verification():
    """Verify webhook enforces X-Telegram-Bot-Api-Secret-Token when secret is configured."""
    client = TestClient(app)
    settings = get_settings()

    with patch.object(settings, "TELEGRAM_WEBHOOK_SECRET", "super_secret_webhook_key"):
        # Missing header -> 401
        res1 = client.post("/v1/telegram/webhook", json={"message": {"chat": {"id": 123}, "text": "/start"}})
        assert res1.status_code == 401

        # Invalid header -> 401
        res2 = client.post(
            "/v1/telegram/webhook",
            json={"message": {"chat": {"id": 123}, "text": "/start"}},
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong_key"},
        )
        assert res2.status_code == 401

        # Correct header -> 200
        res3 = client.post(
            "/v1/telegram/webhook",
            json={"message": {"chat": {"id": 123}, "text": "/start"}},
            headers={"X-Telegram-Bot-Api-Secret-Token": "super_secret_webhook_key"},
        )
        assert res3.status_code == 200


def test_telegram_start_and_clear_commands():
    """Verify /start and /clear commands."""
    client = TestClient(app)
    mock_tg = MockTelegramClient()
    set_telegram_client(mock_tg)
    settings = get_settings()
    headers = {"X-Telegram-Bot-Api-Secret-Token": settings.TELEGRAM_WEBHOOK_SECRET} if settings.TELEGRAM_WEBHOOK_SECRET else {}

    chat_id = 778899

    # /start
    res = client.post(
        "/v1/telegram/webhook",
        json={"message": {"chat": {"id": chat_id}, "text": "/start"}},
        headers=headers,
    )
    assert res.status_code == 200
    assert any("Welcome to Allcited" in m["text"] for m in mock_tg.sent_messages)

    # Query without document -> warning
    mock_tg.sent_messages.clear()
    res_q = client.post(
        "/v1/telegram/webhook",
        json={"message": {"chat": {"id": chat_id}, "text": "What is our leave policy?"}},
        headers=headers,
    )
    assert res_q.status_code == 200
    assert any("No document uploaded yet" in m["text"] for m in mock_tg.sent_messages)

    # /clear
    chat_sessions[chat_id] = "some_session"
    res_clear = client.post(
        "/v1/telegram/webhook",
        json={"message": {"chat": {"id": chat_id}, "text": "/clear"}},
        headers=headers,
    )
    assert res_clear.status_code == 200
    assert chat_id not in chat_sessions


def test_telegram_document_ingest_and_qa_flow():
    """
    Test end-to-end Telegram bot flow:
    1. Upload PDF document via Telegram webhook
    2. Bot acknowledges and indexes document
    3. User asks question
    4. Bot streams and edits answer with inline [S#] citations and source receipts
    """
    client = TestClient(app)
    settings = get_settings()
    headers = {"X-Telegram-Bot-Api-Secret-Token": settings.TELEGRAM_WEBHOOK_SECRET} if settings.TELEGRAM_WEBHOOK_SECRET else {}

    fixture_path = Path(__file__).resolve().parent.parent.parent / "eval" / "fixtures" / "handbook.pdf"
    assert fixture_path.exists()
    pdf_bytes = fixture_path.read_bytes()

    mock_tg = MockTelegramClient(fixture_bytes=pdf_bytes)
    set_telegram_client(mock_tg)

    chat_id = 445566

    # 1. Send Document
    upload_update = {
        "update_id": 1001,
        "message": {
            "message_id": 50,
            "chat": {"id": chat_id},
            "document": {
                "file_id": "file_handbook_pdf_123",
                "file_name": "handbook.pdf",
                "mime_type": "application/pdf",
                "file_size": len(pdf_bytes),
            },
        },
    }

    res_upload = client.post("/v1/telegram/webhook", json=upload_update, headers=headers)
    assert res_upload.status_code == 200

    # Verify session registered
    assert chat_id in chat_sessions
    assert any("Document Indexed" in m["text"] for m in mock_tg.edited_messages)

    # 2. Check /doc command
    res_doc = client.post(
        "/v1/telegram/webhook",
        json={"message": {"chat": {"id": chat_id}, "text": "/doc"}},
        headers=headers,
    )
    assert res_doc.status_code == 200
    assert any("Active Document" in m["text"] for m in mock_tg.sent_messages)

    # 3. Ask question
    query_update = {
        "update_id": 1002,
        "message": {
            "message_id": 51,
            "chat": {"id": chat_id},
            "text": "What is the notice period for voluntary resignation?",
        },
    }

    async def mock_stream(session, query, **kwargs):
        yield 'event: token\ndata: {"delta": "The notice period is 60 calendar days [S1]."}\n\n'
        yield 'event: citations\ndata: {"citations": [{"label": "S1", "chunk_id": "c1", "page": 3, "section_path": ["3. Separation"], "text_preview": "60 calendar days"}]}\n\n'
        yield 'event: done\ndata: {"answer": "The notice period is 60 calendar days [S1].", "refused": false}\n\n'

    with patch("app.telegram.stream_answer_pipeline", side_effect=mock_stream):
        res_query = client.post("/v1/telegram/webhook", json=query_update, headers=headers)
    assert res_query.status_code == 200

    # Verify bot answered
    all_edited_texts = [m["text"] for m in mock_tg.edited_messages]
    final_message = all_edited_texts[-1]

    # Verify answer accuracy & citations
    assert "60" in final_message
    assert "[S" in final_message
    assert "Sources:" in final_message


def test_telegram_chunking_and_formatting():
    """Verify 4096-character chunking and citation receipt formatting."""
    # Test chunking
    long_text = "Line 1\n" * 700  # ~4900 chars
    chunks = chunk_telegram_text(long_text, max_chars=4000)
    assert len(chunks) == 2
    for chk in chunks:
        assert len(chk) <= 4000
    assert "".join(chunks) == long_text

    # Test single very long line without newlines
    continuous_text = "A" * 9500
    cont_chunks = chunk_telegram_text(continuous_text, max_chars=4000)
    assert len(cont_chunks) == 3
    for chk in cont_chunks:
        assert len(chk) <= 4000
    assert "".join(cont_chunks) == continuous_text

    # Test receipt formatting
    from app.pipeline.answer import CitationItem

    dummy_cits = [
        CitationItem(
            label="S1",
            chunk_id="chk_01",
            page=2,
            section_path=["Leave Policy", "Annual Leave"],
            text_preview="Employees accrue 24 days annual leave per calendar year.",
            is_two_hop=False,
        )
    ]
    formatted = format_telegram_answer("Employees accrue 24 days [S1].", dummy_cits)
    assert "Employees accrue 24 days [S1]." in formatted
    assert "📚 *Sources:*" in formatted
    assert "*[S1]*" in formatted
    assert "Page 2" in formatted
    assert "Leave Policy > Annual Leave" in formatted


def test_telegram_error_event_handling():
    """Verify that when stream_answer_pipeline emits an error event, Telegram message is updated."""
    client = TestClient(app)
    settings = get_settings()
    headers = {"X-Telegram-Bot-Api-Secret-Token": settings.TELEGRAM_WEBHOOK_SECRET} if settings.TELEGRAM_WEBHOOK_SECRET else {}

    mock_tg = MockTelegramClient()
    set_telegram_client(mock_tg)

    chat_id = 998877
    chat_sessions[chat_id] = "active_session_123"

    # Seed active session in store
    from app.sessions import get_session_store
    store = get_session_store()
    store.create_session_from_bytes("dummy.txt", b"Dummy session content")
    # Point chat_sessions to the real session ID
    real_session = list(store._sessions.values())[-1]
    chat_sessions[chat_id] = real_session.session_id

    query_update = {
        "update_id": 2001,
        "message": {
            "message_id": 60,
            "chat": {"id": chat_id},
            "text": "What is the content?",
        },
    }

    async def mock_error_stream(session, query, **kwargs):
        yield 'event: error\ndata: {"error": "LLM generation failed", "detail": "Rate limit reached"}\n\n'

    with patch("app.telegram.stream_answer_pipeline", side_effect=mock_error_stream):
        res = client.post("/v1/telegram/webhook", json=query_update, headers=headers)
    assert res.status_code == 200

    edited_texts = [m["text"] for m in mock_tg.edited_messages]
    assert any("LLM generation failed" in t or "Rate limit reached" in t for t in edited_texts)


def test_telegram_markdown_fallback_on_parse_error():
    """Verify TelegramClient falls back to plain text when Telegram API rejects Markdown entities."""
    import httpx

    # Create client with dummy token
    tg = TelegramClient(token="dummy_token")

    # Mock httpx client response: first call fails with Markdown entity parse error, second call succeeds with plain text
    call_count = 0

    class MockResponse:
        def __init__(self, json_data):
            self._json = json_data
            self.status_code = 200

        def json(self):
            return self._json

    async def mock_post(url, **kwargs):
        nonlocal call_count
        call_count += 1
        json_body = kwargs.get("json", {})
        if json_body.get("parse_mode") == "Markdown":
            return MockResponse({"ok": False, "error_code": 400, "description": "Bad Request: can't parse entities"})
        return MockResponse({"ok": True, "result": {"message_id": 101, "text": json_body.get("text")}})

    with patch.object(httpx.AsyncClient, "post", side_effect=mock_post):
        import asyncio
        res = asyncio.run(tg.edit_message_text(chat_id=123, message_id=101, text="Code_with_unmatched_underscores", parse_mode="Markdown"))
        assert res["ok"] is True
        assert call_count == 2
