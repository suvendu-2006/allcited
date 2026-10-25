import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

from app.pipeline.chunker import Chunk

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
BATCH_SIZE = 64


def resolve_local_model_path(model_name: str, model_type: str = "embedding") -> str:
    """
    Check if a local directory exists containing downloaded model weights.
    Searches candidate paths (relative to repo/api, cwd, and container root).
    Returns local path string if valid weights exist; otherwise returns original model_name.
    """
    p = Path(model_name)
    if p.exists() and ((p / "model.safetensors").exists() or (p / "config.json").exists()):
        return str(p.resolve())

    simple_name = model_name.split("/")[-1]
    name_candidates = [model_name, simple_name]

    api_root = Path(__file__).resolve().parent.parent.parent
    base_dirs = [
        api_root / "models",
        Path.cwd() / "models",
        Path.cwd() / "api" / "models",
        Path("/app/models"),
    ]

    for b in base_dirs:
        for nc in name_candidates:
            cand = b / nc
            if cand.exists() and ((cand / "model.safetensors").exists() or (cand / "config.json").exists()):
                return str(cand.resolve())

    return model_name


class EmbeddingManager:
    """
    Manages embedding generation with batching and in-memory hash caching.
    Outputs L2-normalized float32 vectors suitable for FAISS IndexFlatIP (cosine similarity).
    """

    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL):
        self.model_name = model_name
        self._model: SentenceTransformer | None = None
        # Hash cache: sha256(text) -> np.ndarray (shape: (384,), dtype: float32)
        self._cache: Dict[str, np.ndarray] = {}

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            resolved = resolve_local_model_path(self.model_name, "embedding")
            if resolved != self.model_name:
                logger.info("Loading embedding model from local path: %s", resolved)
                try:
                    self._model = SentenceTransformer(resolved, local_files_only=True)
                except Exception as e:
                    logger.warning("Local embedding model load failed from %s: %s; falling back to hub", resolved, e)
                    self._model = SentenceTransformer(self.model_name)
            else:
                logger.info("Loading embedding model from Hugging Face Hub: %s", self.model_name)
                self._model = SentenceTransformer(self.model_name)
        return self._model

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def embed_texts(
        self,
        texts: List[str],
        batch_size: int = BATCH_SIZE,
    ) -> np.ndarray:
        """
        Embed a list of text strings, utilizing the hash cache to avoid redundant computation.
        Returns L2-normalized numpy array of shape (len(texts), EMBEDDING_DIM).
        """
        if not texts:
            return np.empty((0, EMBEDDING_DIM), dtype=np.float32)

        results: List[np.ndarray | None] = [None] * len(texts)
        missing_indices: List[int] = []
        missing_texts: List[str] = []

        # 1. Check cache
        for idx, text in enumerate(texts):
            h = self._hash_text(text)
            if h in self._cache:
                results[idx] = self._cache[h]
            else:
                missing_indices.append(idx)
                missing_texts.append(text)

        # 2. Compute missing embeddings in batches of 64
        if missing_texts:
            embeddings = self.model.encode(
                missing_texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,  # L2 normalization for cosine similarity
            ).astype(np.float32)

            for idx, text, emb in zip(missing_indices, missing_texts, embeddings):
                h = self._hash_text(text)
                self._cache[h] = emb
                results[idx] = emb

        return np.array(results, dtype=np.float32)

    def embed_chunks(
        self,
        chunks: List[Chunk],
        batch_size: int = BATCH_SIZE,
    ) -> Tuple[np.ndarray, Dict[str, int]]:
        """
        Embed a list of Chunks, checking chunk.content_hash against the in-memory cache.
        Returns a tuple of (embeddings_array, stats_dict) where stats_dict contains:
        {"total": int, "reused": int, "new": int}.
        """
        if not chunks:
            return np.empty((0, EMBEDDING_DIM), dtype=np.float32), {"total": 0, "reused": 0, "new": 0}

        results: List[np.ndarray | None] = [None] * len(chunks)
        missing_indices: List[int] = []
        missing_texts: List[str] = []

        for idx, chunk in enumerate(chunks):
            text_to_embed = chunk.embed_text
            h = self._hash_text(text_to_embed)
            if h in self._cache:
                results[idx] = self._cache[h]
            else:
                missing_indices.append(idx)
                missing_texts.append(text_to_embed)

        reused_count = len(chunks) - len(missing_texts)
        new_count = len(missing_texts)

        if missing_texts:
            embeddings = self.model.encode(
                missing_texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,
            ).astype(np.float32)

            for idx, text, emb in zip(missing_indices, missing_texts, embeddings):
                h = self._hash_text(text)
                self._cache[h] = emb
                results[idx] = emb

        arr = np.array(results, dtype=np.float32)
        stats = {
            "total": len(chunks),
            "reused": reused_count,
            "new": new_count,
        }
        return arr, stats

    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single search query returning shape (1, EMBEDDING_DIM)."""
        return self.embed_texts([query])

    def clear_cache(self):
        """Clear the in-memory embedding cache."""
        self._cache.clear()

    @property
    def cache_size(self) -> int:
        return len(self._cache)


# Global singleton instance
_embedding_manager: EmbeddingManager | None = None


def get_embedding_manager() -> EmbeddingManager:
    global _embedding_manager
    if _embedding_manager is None:
        _embedding_manager = EmbeddingManager()
    return _embedding_manager
