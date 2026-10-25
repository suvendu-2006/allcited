import logging
import math
from typing import List, Optional

from pydantic import BaseModel, Field
from sentence_transformers import CrossEncoder

from app.pipeline.embed import resolve_local_model_path
from app.pipeline.retrieve import ScoredChunk

logger = logging.getLogger(__name__)

DEFAULT_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class RerankedChunk(BaseModel):
    """Represents a candidate chunk scored by the cross-encoder re-ranker."""

    chunk_id: str
    text: str
    rerank_score: float = Field(..., description="Sigmoidal relevance score in [0.0, 1.0]")
    original_rank: int = Field(..., description="1-based rank prior to re-ranking")
    rerank_rank: int = Field(..., description="1-based rank after re-ranking")
    scored_chunk: ScoredChunk


def sigmoid(x: float) -> float:
    """Map real logit to [0, 1] probability range."""
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0


class Reranker:
    """Cross-encoder re-ranker with feature flagging and graceful degradation."""

    def __init__(self, model_name: str = DEFAULT_RERANKER_MODEL):
        self.model_name = model_name
        self._model: Optional[CrossEncoder] = None

    @property
    def model(self) -> CrossEncoder:
        if self._model is None:
            resolved = resolve_local_model_path(self.model_name, "reranker")
            if resolved != self.model_name:
                logger.info("Loading reranker model from local path: %s", resolved)
                try:
                    self._model = CrossEncoder(resolved, local_files_only=True)
                except Exception as e:
                    logger.warning("Local reranker model load failed from %s: %s; falling back to hub", resolved, e)
                    self._model = CrossEncoder(self.model_name)
            else:
                logger.info("Loading reranker model from Hugging Face Hub: %s", self.model_name)
                self._model = CrossEncoder(self.model_name)
        return self._model

    def rerank(
        self,
        query: str,
        candidates: List[ScoredChunk],
        top_k: int = 4,
        enabled: bool = True,
    ) -> List[RerankedChunk]:
        """
        Score (query, chunk_text) pairs using CrossEncoder and reorder to top_k.
        If disabled or on failure/OOM, gracefully fall back to initial ranking order.
        """
        if not candidates:
            return []

        # 1. Feature flag off: return initial order
        if not enabled:
            return [
                RerankedChunk(
                    chunk_id=sc.chunk.id,
                    text=sc.chunk.text,
                    rerank_score=sc.rrf_score,
                    original_rank=idx + 1,
                    rerank_rank=idx + 1,
                    scored_chunk=sc,
                )
                for idx, sc in enumerate(candidates[:top_k])
            ]

        # 2. Re-rank with CrossEncoder
        try:
            pairs = [[query, sc.chunk.text] for sc in candidates]
            raw_scores = self.model.predict(pairs)

            scored_items = []
            for idx, (sc, raw_score) in enumerate(zip(candidates, raw_scores)):
                norm_score = sigmoid(float(raw_score))
                scored_items.append((sc, norm_score, idx + 1))

            # Sort descending by cross-encoder score
            scored_items.sort(key=lambda item: item[1], reverse=True)

            results: List[RerankedChunk] = []
            for new_rank_0, (sc, score, orig_rank) in enumerate(scored_items[:top_k]):
                results.append(
                    RerankedChunk(
                        chunk_id=sc.chunk.id,
                        text=sc.chunk.text,
                        rerank_score=score,
                        original_rank=orig_rank,
                        rerank_rank=new_rank_0 + 1,
                        scored_chunk=sc,
                    )
                )

            return results

        except Exception as e:
            logger.warning(f"Re-ranker failure or OOM ({str(e)}), falling back to RRF rankings")
            # Safe degradation path
            return [
                RerankedChunk(
                    chunk_id=sc.chunk.id,
                    text=sc.chunk.text,
                    rerank_score=sc.rrf_score,
                    original_rank=idx + 1,
                    rerank_rank=idx + 1,
                    scored_chunk=sc,
                )
                for idx, sc in enumerate(candidates[:top_k])
            ]


# Global singleton
_reranker: Optional[Reranker] = None


def get_reranker() -> Reranker:
    global _reranker
    if _reranker is None:
        _reranker = Reranker()
    return _reranker
