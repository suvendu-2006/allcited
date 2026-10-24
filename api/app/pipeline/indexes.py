import re
from typing import List, Tuple

import faiss
import numpy as np
from rank_bm25 import BM25Okapi

from app.pipeline.chunker import Chunk
from app.pipeline.embed import EMBEDDING_DIM, get_embedding_manager


def tokenize_for_bm25(text: str) -> List[str]:
    """Simple alphanumeric lowercase tokenizer for BM25 ranking."""
    return re.findall(r"\b[a-z0-9_\-\.]{2,}\b", text.lower())


class VectorIndex:
    """FAISS IndexFlatIP (inner product on normalized vectors = exact cosine similarity)."""

    def __init__(self, dimension: int = EMBEDDING_DIM):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)
        self.chunks: List[Chunk] = []

    def build(self, chunks: List[Chunk], embeddings: np.ndarray):
        """Add chunks and precomputed float32 normalized embeddings to the index."""
        if len(chunks) != len(embeddings):
            raise ValueError(f"Mismatched chunks ({len(chunks)}) and embeddings ({len(embeddings)})")

        if len(chunks) == 0:
            return

        # Ensure correct float32 type and dimension
        embs = embeddings.astype(np.float32)
        # Rebuild or add
        self.chunks.extend(chunks)
        self.index.add(embs)

    def search(self, query_emb: np.ndarray, top_k: int = 10) -> List[Tuple[Chunk, float]]:
        """Search nearest chunks returning list of (chunk, cosine_score) tuples."""
        if self.index.ntotal == 0 or not self.chunks:
            return []

        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_emb.astype(np.float32), k)

        results: List[Tuple[Chunk, float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.chunks):
                results.append((self.chunks[idx], float(score)))

        return results


class BM25Index:
    """BM25Okapi keyword index over chunk tokens."""

    def __init__(self):
        self.chunks: List[Chunk] = []
        self.corpus_tokens: List[List[str]] = []
        self.bm25: BM25Okapi | None = None

    def build(self, chunks: List[Chunk]):
        self.chunks = list(chunks)
        self.corpus_tokens = [tokenize_for_bm25(c.embed_text) for c in self.chunks]
        if self.corpus_tokens and any(self.corpus_tokens):
            self.bm25 = BM25Okapi(self.corpus_tokens)
        else:
            self.bm25 = None

    def search(self, query: str, top_k: int = 10) -> List[Tuple[Chunk, float]]:
        """Search BM25 returning list of (chunk, bm25_score) tuples."""
        if not self.bm25 or not self.chunks:
            return []

        query_tokens = tokenize_for_bm25(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)
        k = min(top_k, len(self.chunks))
        # Top-k indices sorted descending by score
        top_indices = np.argsort(scores)[::-1][:k]

        results: List[Tuple[Chunk, float]] = []
        for idx in top_indices:
            score = float(scores[idx])
            if score > 0:
                results.append((self.chunks[idx], score))

        return results


class DocumentIndex:
    """Unified container managing both VectorIndex and BM25Index for a document or session."""

    def __init__(self):
        self.vector_index = VectorIndex()
        self.bm25_index = BM25Index()
        self.chunks: List[Chunk] = []

    def build(self, chunks: List[Chunk], embedding_manager=None) -> dict:
        if embedding_manager is None:
            embedding_manager = get_embedding_manager()

        self.chunks = list(chunks)
        if not self.chunks:
            return {"total": 0, "reused": 0, "new": 0}

        # 1. Build BM25
        self.bm25_index.build(self.chunks)

        # 2. Embed and build FAISS vector index with delta skip tracking
        embeddings, stats = embedding_manager.embed_chunks(self.chunks)
        self.vector_index = VectorIndex()
        self.vector_index.build(self.chunks, embeddings)
        return stats

    def search_vector(self, query: str, top_k: int = 10, embedding_manager=None) -> List[Tuple[Chunk, float]]:
        if embedding_manager is None:
            embedding_manager = get_embedding_manager()
        query_emb = embedding_manager.embed_query(query)
        return self.vector_index.search(query_emb, top_k=top_k)

    def search_bm25(self, query: str, top_k: int = 10) -> List[Tuple[Chunk, float]]:
        return self.bm25_index.search(query, top_k=top_k)
