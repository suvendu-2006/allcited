import hashlib
from typing import Dict, List

import numpy as np
from sentence_transformers import SentenceTransformer

DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
BATCH_SIZE = 64


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
