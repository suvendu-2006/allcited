import logging
import time
import uuid
from typing import Any, Dict, List, Optional

import pymupdf as fitz
from fastapi import HTTPException

from app.pipeline.chunker import Chunk, chunk_blocks
from app.pipeline.headers import generate_structural_headers
from app.pipeline.indexes import DocumentIndex
from app.pipeline.parsers.base import ParsedBlock
from app.pipeline.parsers.docx import DOCXParserError, parse_docx
from app.pipeline.parsers.html import HTMLParserError, parse_html
from app.pipeline.parsers.md_txt import parse_md_txt
from app.pipeline.parsers.pdf import PDFParserError, parse_pdf
from app.pipeline.parsers.pptx import PPTXParserError, parse_pptx
from app.pipeline.parsers.xlsx import XLSXParserError, parse_xlsx
from app.pipeline.refmap import ReferenceMap, build_reference_map

logger = logging.getLogger(__name__)

MAX_SESSIONS = 8
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB
MAX_PAGES = 300
SESSION_TTL_SECONDS = 2 * 3600  # 2 hours


class DocumentSession:
    """Encapsulates an active in-memory document session with its index and graph."""

    def __init__(
        self,
        session_id: str,
        filename: str,
        file_size_bytes: int,
        page_count: int,
        blocks: List[ParsedBlock],
        chunks: List[Chunk],
        ref_map: ReferenceMap,
        doc_index: DocumentIndex,
        delta_stats: Optional[Dict[str, int]] = None,
        knowledge_graph: Optional[Any] = None,
    ):
        self.session_id = session_id
        self.filename = filename
        self.file_size_bytes = file_size_bytes
        self.page_count = page_count
        self.blocks = blocks
        self.chunks = chunks
        self.ref_map = ref_map
        self.doc_index = doc_index
        self.delta_stats = delta_stats or {"total": len(chunks), "reused": 0, "new": len(chunks)}
        self.knowledge_graph = knowledge_graph
        self.created_at = time.time()
        self.last_accessed = self.created_at

    def touch(self):
        self.last_accessed = time.time()

    def is_expired(self, ttl: float = SESSION_TTL_SECONDS) -> bool:
        return (time.time() - self.last_accessed) > ttl


class SessionStore:
    """Manages active sessions with LRU and TTL eviction policies."""

    def __init__(self):
        self._sessions: Dict[str, DocumentSession] = {}

    def get_session(self, session_id: str) -> Optional[DocumentSession]:
        self._cleanup_expired()
        session = self._sessions.get(session_id)
        if session:
            session.touch()
        return session

    def delete_session(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def _cleanup_expired(self):
        now = time.time()
        expired_keys = [
            sid for sid, s in self._sessions.items()
            if (now - s.last_accessed) > SESSION_TTL_SECONDS
        ]
        for sid in expired_keys:
            del self._sessions[sid]

    def _evict_lru_if_needed(self):
        if len(self._sessions) >= MAX_SESSIONS:
            # Sort by last_accessed ascending
            oldest_sid = min(self._sessions.keys(), key=lambda sid: self._sessions[sid].last_accessed)
            del self._sessions[oldest_sid]

    def create_session_from_bytes(
        self,
        filename: str,
        content: bytes,
        target_tokens: int = 400,
        overlap_ratio: float = 0.15,
        section_aware: bool = False,
        enable_headers: bool = True,
    ) -> DocumentSession:
        # 1. Enforce 20 MB cap
        file_size = len(content)
        if file_size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail={"error": {"code": "plan_limit_reached", "message": f"File size ({file_size} bytes) exceeds 20 MB cap"}},
            )

        self._cleanup_expired()
        self._evict_lru_if_needed()

        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        lower_name = filename.lower()

        # 2. Parse document
        page_count = 1
        blocks: List[ParsedBlock] = []

        if lower_name.endswith(".pdf"):
            try:
                # Check page cap before full parse
                doc = fitz.open(stream=content, filetype="pdf")
                page_count = doc.page_count
                doc.close()
                if page_count > MAX_PAGES:
                    raise HTTPException(
                        status_code=400,
                        detail={"error": {"code": "plan_limit_reached", "message": f"Document has {page_count} pages, exceeding the 300-page cap"}},
                    )
                blocks = parse_pdf(content, source_name=filename)
            except PDFParserError as e:
                raise HTTPException(
                    status_code=400,
                    detail={"error": {"code": "doc_unreadable", "message": str(e)}},
                ) from e
        elif lower_name.endswith((".md", ".txt")):
            blocks = parse_md_txt(content, source_name=filename)
            page_count = 1
        elif lower_name.endswith(".docx"):
            try:
                blocks = parse_docx(content, source_name=filename)
                page_count = 1
            except DOCXParserError as e:
                raise HTTPException(
                    status_code=400,
                    detail={"error": {"code": "doc_unreadable", "message": str(e)}},
                ) from e
        elif lower_name.endswith(".pptx"):
            try:
                blocks = parse_pptx(content, source_name=filename)
                page_count = max((b.page for b in blocks if b.page), default=1)
            except PPTXParserError as e:
                raise HTTPException(
                    status_code=400,
                    detail={"error": {"code": "doc_unreadable", "message": str(e)}},
                ) from e
        elif lower_name.endswith((".xlsx", ".xlsm")):
            try:
                blocks = parse_xlsx(content, source_name=filename)
                page_count = max((b.page for b in blocks if b.page), default=1)
            except XLSXParserError as e:
                raise HTTPException(
                    status_code=400,
                    detail={"error": {"code": "doc_unreadable", "message": str(e)}},
                ) from e
        elif lower_name.startswith(("http://", "https://")) or lower_name.endswith((".html", ".htm")):
            try:
                blocks = parse_html(content, source_name=filename)
                page_count = 1
            except HTMLParserError as e:
                raise HTTPException(
                    status_code=400,
                    detail={"error": {"code": "doc_unreadable", "message": str(e)}},
                ) from e
        else:
            # Default text fallback
            blocks = parse_md_txt(content, source_name=filename)

        if not blocks:
            raise HTTPException(
                status_code=400,
                detail={"error": {"code": "doc_unreadable", "message": "No readable text extracted from document"}},
            )

        # 3. Chunk document
        # Plan §3.0: PPTX slide = chunk basis
        if lower_name.endswith(".pptx"):
            chunks = []
            chunk_idx = 0
            for b in blocks:
                slide_chunks = chunk_blocks(
                    [b],
                    doc_id=session_id,
                    target_tokens=target_tokens,
                    overlap_ratio=overlap_ratio,
                    section_aware=section_aware,
                )
                for sc in slide_chunks:
                    chunk_idx += 1
                    sc.id = f"{session_id}_chunk_{chunk_idx:04d}"
                    chunks.append(sc)
        else:
            chunks = chunk_blocks(
                blocks,
                doc_id=session_id,
                target_tokens=target_tokens,
                overlap_ratio=overlap_ratio,
                section_aware=section_aware,
            )

        # 3b. Generate contextual headers (situating chunks in document hierarchy)
        if enable_headers:
            chunks = generate_structural_headers(chunks, doc_title=filename)

        # 4. Build Reference Map
        ref_map = build_reference_map(chunks)

        # 5. Build In-Memory FAISS + BM25 Document Index
        doc_index = DocumentIndex()
        embed_stats = doc_index.build(chunks)

        logger.info(
            "Delta re-ingest for '%s': %d total chunks, %d reused/skipped, %d newly embedded",
            filename,
            embed_stats.get("total", len(chunks)),
            embed_stats.get("reused", 0),
            embed_stats.get("new", len(chunks)),
        )

        # 6. Extract GraphRAG-lite knowledge graph
        from app.pipeline.graph import extract_heuristic_entities
        knowledge_graph = extract_heuristic_entities(chunks)

        # 7. Record stats
        from app.stats import get_platform_stats
        p_stats = get_platform_stats()
        p_stats.record_chunks(len(chunks))
        if lower_name.endswith(".pdf"):
            p_stats.record_format("pdf")
        elif lower_name.endswith(".docx"):
            p_stats.record_format("docx")
        elif lower_name.endswith(".pptx"):
            p_stats.record_format("pptx")
        elif lower_name.endswith((".xlsx", ".xlsm")):
            p_stats.record_format("xlsx")
        elif lower_name.startswith(("http://", "https://")) or lower_name.endswith((".html", ".htm")):
            p_stats.record_format("html")
        else:
            p_stats.record_format("md_txt")

        session = DocumentSession(
            session_id=session_id,
            filename=filename,
            file_size_bytes=file_size,
            page_count=page_count,
            blocks=blocks,
            chunks=chunks,
            ref_map=ref_map,
            doc_index=doc_index,
            delta_stats=embed_stats,
            knowledge_graph=knowledge_graph,
        )

        self._sessions[session_id] = session

        # 6. Invalidate semantic cache entries for this document
        from app.cache import get_semantic_cache
        get_semantic_cache().invalidate_filename(filename)

        return session

    @property
    def active_count(self) -> int:
        self._cleanup_expired()
        return len(self._sessions)


# Global singleton session store
_session_store: SessionStore | None = None


def get_session_store() -> SessionStore:
    global _session_store
    if _session_store is None:
        _session_store = SessionStore()
    return _session_store
