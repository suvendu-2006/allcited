import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Header, HTTPException, Request

from app.config import get_settings
from app.pipeline.answer import CitationItem, stream_answer_pipeline
from app.schemas import TelegramWebhookResponse
from app.sessions import DocumentSession, get_session_store

logger = logging.getLogger(__name__)

router = APIRouter()


class TelegramClient:
    """Telegram Bot API client with support for live calls or mocked test mode."""

    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}" if token else ""
        self.file_base_url = f"https://api.telegram.org/file/bot{token}" if token else ""

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: Optional[str] = "Markdown",
    ) -> Dict[str, Any]:
        """Send a message to a chat."""
        if not self.token:
            return {"ok": True, "result": {"message_id": 100, "chat": {"id": chat_id}, "text": text}}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
                timeout=20.0,
            )
            return resp.json()

    async def edit_message_text(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        parse_mode: Optional[str] = "Markdown",
    ) -> Dict[str, Any]:
        """Edit an existing message text."""
        if not self.token:
            return {"ok": True, "result": {"message_id": message_id, "chat": {"id": chat_id}, "text": text}}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/editMessageText",
                json={
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "text": text,
                    "parse_mode": parse_mode,
                },
                timeout=20.0,
            )
            return resp.json()

    async def get_file_bytes(self, file_id: str) -> bytes:
        """Download file content by file_id."""
        if not self.token:
            return b""

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/getFile",
                params={"file_id": file_id},
                timeout=20.0,
            )
            data = resp.json()
            file_path = data.get("result", {}).get("file_path")
            if not file_path:
                raise ValueError(f"Could not retrieve file_path for file_id {file_id}: {data}")

            dl_resp = await client.get(f"{self.file_base_url}/{file_path}", timeout=30.0)
            return dl_resp.content


_global_telegram_client: Optional[TelegramClient] = None


def get_telegram_client() -> TelegramClient:
    """Retrieve active Telegram client instance."""
    global _global_telegram_client
    if _global_telegram_client is None:
        settings = get_settings()
        _global_telegram_client = TelegramClient(token=settings.TELEGRAM_BOT_TOKEN)
    return _global_telegram_client


def set_telegram_client(client: Optional[TelegramClient]) -> None:
    """Override Telegram client for tests."""
    global _global_telegram_client
    _global_telegram_client = client


# In-memory chat-to-session routing & per-chat concurrency lock
chat_sessions: Dict[int, str] = {}
chat_locks: Dict[int, asyncio.Lock] = {}


def chunk_telegram_text(text: str, max_chars: int = 4000) -> List[str]:
    """Split text into <= 4000 char blocks for Telegram 4096-character limit."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    current_chunk: List[str] = []
    current_len = 0

    for line in text.splitlines(keepends=True):
        if current_len + len(line) > max_chars and current_chunk:
            chunks.append("".join(current_chunk))
            current_chunk = []
            current_len = 0
        current_chunk.append(line)
        current_len += len(line)

    if current_chunk:
        chunks.append("".join(current_chunk))

    return chunks


def format_telegram_answer(answer: str, citations: List[CitationItem]) -> str:
    """Format answer with structured, readable citation receipts for Telegram."""
    # Normalize full-width brackets from multilingual LLMs
    answer = answer.replace("【", "[").replace("】", "]")
    if not citations:
        return answer

    receipts = ["\n\n📚 *Sources:*"]
    for cit in citations:
        sec = f"§ {' > '.join(cit.section_path)}" if cit.section_path else ""
        pg = f"Page {cit.page}" if cit.page else ""
        meta_parts = [p for p in [pg, sec] if p]
        meta_str = f" ({', '.join(meta_parts)})" if meta_parts else ""
        ocr_tag = " [OCR]" if cit.is_ocr else ""
        two_hop_tag = " [Cross-Ref]" if cit.is_two_hop else ""

        preview = cit.text_preview.replace("\n", " ").strip()
        if len(preview) > 120:
            preview = preview[:117] + "..."
        receipts.append(f"• *[{cit.label}]*{ocr_tag}{two_hop_tag}{meta_str}:\n  _{preview}_")

    return answer + "\n" + "\n".join(receipts)


async def handle_document_upload(
    tg: TelegramClient,
    chat_id: int,
    file_id: str,
    file_name: str,
) -> None:
    """Download and ingest uploaded document into an active DocumentSession."""
    ack_res = await tg.send_message(
        chat_id=chat_id,
        text=f"📥 Receiving `{file_name}`... Ingesting and indexing vectors.",
    )
    ack_msg_id = ack_res.get("result", {}).get("message_id", 0)

    try:
        content = await tg.get_file_bytes(file_id)
        if not content:
            raise ValueError("Document file content is empty or download failed")

        store = get_session_store()
        session: DocumentSession = store.create_session_from_bytes(
            filename=file_name,
            content=content,
        )
        chat_sessions[chat_id] = session.session_id

        await tg.edit_message_text(
            chat_id=chat_id,
            message_id=ack_msg_id,
            text=(
                f"✅ *Document Indexed:* `{file_name}`\n"
                f"• Pages: {session.page_count}\n"
                f"• Passages: {len(session.chunks)}\n\n"
                "You can now ask questions about this document. Every answer will be grounded with verifiable citations!"
            ),
        )
    except Exception as e:
        logger.exception("Failed to ingest document from Telegram: %s", e)
        error_msg = f"❌ *Ingestion failed:* {str(e)}"
        if ack_msg_id:
            await tg.edit_message_text(chat_id=chat_id, message_id=ack_msg_id, text=error_msg)
        else:
            await tg.send_message(chat_id=chat_id, text=error_msg)


async def handle_question_query(
    tg: TelegramClient,
    chat_id: int,
    query: str,
) -> None:
    """Execute pipeline query with flood-safe message editing and 4096-char chunking."""
    session_id = chat_sessions.get(chat_id)
    if not session_id:
        await tg.send_message(
            chat_id=chat_id,
            text=(
                "⚠️ *No document uploaded yet!*\n\n"
                "Please upload a PDF or document first. Then ask questions about it."
            ),
        )
        return

    store = get_session_store()
    session = store.get_session(session_id)
    if not session:
        await tg.send_message(
            chat_id=chat_id,
            text="⚠️ Your document session has expired. Please upload your document again.",
        )
        chat_sessions.pop(chat_id, None)
        return

    placeholder_res = await tg.send_message(
        chat_id=chat_id,
        text="🔍 *Searching document...*",
    )
    msg_id = placeholder_res.get("result", {}).get("message_id", 0)

    accumulated_tokens: List[str] = []
    last_edit_time = time.time()
    citations: List[CitationItem] = []

    try:
        async for sse_chunk in stream_answer_pipeline(session=session, query=query):
            event_name = ""
            for line in sse_chunk.splitlines():
                line = line.strip()
                if line.startswith("event:"):
                    event_name = line[len("event:"):].strip()
                elif line.startswith("data:"):
                    data_str = line[len("data:"):].strip()
                    import json

                    try:
                        payload = json.loads(data_str)
                    except Exception:
                        continue

                    if event_name == "token":
                        accumulated_tokens.append(payload.get("delta", ""))
                        now = time.time()
                        if now - last_edit_time >= 1.5 and accumulated_tokens:
                            curr_text = "".join(accumulated_tokens)
                            if len(curr_text) <= 4000:
                                await tg.edit_message_text(
                                    chat_id=chat_id,
                                    message_id=msg_id,
                                    text=curr_text + " ▍",
                                )
                                last_edit_time = now

                    elif event_name == "citations":
                        raw_cits = payload.get("citations", [])
                        citations = [CitationItem(**c) for c in raw_cits]

                    elif event_name == "done":
                        final_answer = payload.get("answer", "".join(accumulated_tokens))
                        full_formatted = format_telegram_answer(final_answer, citations)

                        chunks = chunk_telegram_text(full_formatted, max_chars=4000)
                        if chunks:
                            await tg.edit_message_text(
                                chat_id=chat_id,
                                message_id=msg_id,
                                text=chunks[0],
                            )
                            for extra_chunk in chunks[1:]:
                                await tg.send_message(chat_id=chat_id, text=extra_chunk)
                        return

    except Exception as e:
        logger.exception("Error answering Telegram query: %s", e)
        error_text = f"❌ *Error answering question:* {str(e)}"
        if msg_id:
            await tg.edit_message_text(chat_id=chat_id, message_id=msg_id, text=error_text)
        else:
            await tg.send_message(chat_id=chat_id, text=error_text)


async def process_telegram_update(body: Dict[str, Any]) -> None:
    """Process an incoming Telegram update (from webhook or long-poller)."""
    message = body.get("message") or body.get("edited_message")
    if not message:
        return

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    if not chat_id:
        return

    tg = get_telegram_client()

    # Acquire per-chat lock for flood-safe queueing
    if chat_id not in chat_locks:
        chat_locks[chat_id] = asyncio.Lock()
    lock = chat_locks[chat_id]

    async with lock:
        # 1. Document upload
        document = message.get("document")
        if document:
            file_id = document.get("file_id")
            file_name = document.get("file_name", "document.pdf")
            await handle_document_upload(
                tg=tg,
                chat_id=chat_id,
                file_id=file_id,
                file_name=file_name,
            )
            return

        # 2. Text command or question
        text = message.get("text", "").strip()
        if not text:
            return

        if text.startswith("/start"):
            welcome_text = (
                "👋 *Welcome to Allcited!*\n\n"
                "I answer questions grounded *strictly* in your documents with verifiable inline citations.\n\n"
                "📌 *How to use:*\n"
                "1. Send me a document (PDF, DOCX, PPTX, XLSX, TXT).\n"
                "2. Ask any question.\n"
                "3. Receive accurate answers with inline `[S#]` citations and source receipts.\n\n"
                "Commands:\n"
                "/doc — View current active document info\n"
                "/clear — Clear current document session"
            )
            await tg.send_message(chat_id=chat_id, text=welcome_text)
            return

        if text.startswith("/clear"):
            chat_sessions.pop(chat_id, None)
            await tg.send_message(chat_id=chat_id, text="🧹 Active document session cleared.")
            return

        if text.startswith("/doc"):
            session_id = chat_sessions.get(chat_id)
            if not session_id:
                await tg.send_message(chat_id=chat_id, text="No active document. Send a document to index.")
            else:
                store = get_session_store()
                sess = store.get_session(session_id)
                if sess:
                    await tg.send_message(
                        chat_id=chat_id,
                        text=(
                            f"📄 *Active Document:* `{sess.filename}`\n"
                            f"• Pages: {sess.page_count}\n"
                            f"• Passages: {len(sess.chunks)}\n"
                            f"• Session ID: `{sess.session_id}`"
                        ),
                    )
                else:
                    await tg.send_message(chat_id=chat_id, text="Document session has expired.")
            return

        # 3. Question query
        await handle_question_query(
            tg=tg,
            chat_id=chat_id,
            query=text,
        )


async def run_telegram_polling() -> None:
    """Long-polling background worker for immediate local testing without webhooks or ngrok."""
    settings = get_settings()
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.info("No TELEGRAM_BOT_TOKEN configured; telegram poller is idle.")
        return

    logger.info("Starting Allcited Telegram long-polling worker...")
    offset = 0

    # Ensure any previous webhook registration is cleared so getUpdates works
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            await client.post(f"https://api.telegram.org/bot{token}/deleteWebhook")
        except Exception as e:
            logger.warning("Could not delete webhook for polling: %s", e)

    async with httpx.AsyncClient(timeout=35.0) as client:
        while True:
            try:
                url = f"https://api.telegram.org/bot{token}/getUpdates"
                params = {"offset": offset, "timeout": 20}
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        asyncio.create_task(process_telegram_update(update))
                elif resp.status_code == 409:
                    await asyncio.sleep(2)
                else:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                logger.info("Telegram long-polling worker cancelled.")
                break
            except Exception as e:
                logger.warning("Telegram polling error: %s", e)
                await asyncio.sleep(3)


@router.post(
    "/webhook",
    response_model=TelegramWebhookResponse,
    summary="Handle Telegram bot webhook events",
    operation_id="telegramWebhook",
)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """
    Telegram webhook endpoint.
    Verifies secret token header, handles /start, document ingest, and cited Q&A.
    Uses per-chat lock to avoid Telegram flood limits.
    """
    settings = get_settings()
    if settings.TELEGRAM_WEBHOOK_SECRET:
        if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
            raise HTTPException(
                status_code=401,
                detail={"error": {"code": "invalid_secret_token", "message": "Invalid secret token"}},
            )

    body = await request.json()
    await process_telegram_update(body)
    return {"ok": True}
