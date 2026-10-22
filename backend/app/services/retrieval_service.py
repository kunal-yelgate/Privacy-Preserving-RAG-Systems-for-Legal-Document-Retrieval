"""
Hybrid retrieval service combining semantic search and BM25 keyword search.
Implements Reciprocal Rank Fusion (RRF) and server-side matter boundary filtering.
"""
from typing import Any, Dict, List, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.infrastructure.embeddings.ollama_embeddings import OllamaEmbeddingClient
from backend.app.infrastructure.keyword_search.bm25_index import BM25IndexManager
from backend.app.infrastructure.vector_store.chroma_store import ChromaVectorStore
from backend.app.schemas.search import SearchResultItem


class RetrievalService:
    """Orchestrates authorized hybrid retrieval across ChromaDB and BM25."""

    def __init__(
        self,
        vector_store: ChromaVectorStore,
        bm25_manager: BM25IndexManager,
        embedding_client: OllamaEmbeddingClient,
    ):
        self.vector_store = vector_store
        self.bm25_manager = bm25_manager
        self.embedding_client = embedding_client

    async def search(
        self,
        query: str,
        matter_id: str,
        top_k: int = settings.RETRIEVAL_TOP_K,
        allowed_classifications: Optional[List[str]] = None,
        fusion_strategy: str = "rrf",  # 'rrf' or 'linear'
    ) -> List[SearchResultItem]:
        """
        Executes hybrid retrieval:
        1. Local semantic search via ChromaDB
        2. Local keyword search via BM25
        3. Reciprocal Rank Fusion
        """
        # 1. Semantic search
        semantic_results: List[Dict[str, Any]] = []
        try:
            query_embedding = await self.embedding_client.get_embedding(query)
            semantic_results = self.vector_store.search_similar(
                query_embedding=query_embedding,
                matter_id=matter_id,
                top_k=top_k * 2,
                allowed_classifications=allowed_classifications,
            )
        except Exception as e:
            logger.warning(f"Semantic search failed, falling back to keyword only: {e}")

        # 2. Keyword search
        bm25_results = self.bm25_manager.search(
            query=query,
            matter_id=matter_id,
            top_k=top_k * 2,
            allowed_classifications=allowed_classifications,
        )

        # 3. Fuse results
        fused = self._fuse_results(
            semantic_results=semantic_results,
            keyword_results=bm25_results,
            top_k=top_k,
            strategy=fusion_strategy,
        )

        return fused

    def _fuse_results(
        self,
        semantic_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        top_k: int,
        strategy: str = "rrf",
    ) -> List[SearchResultItem]:
        """Fuses semantic and keyword candidates using RRF or linear interpolation."""
        combined_scores: Dict[str, float] = {}
        candidate_meta: Dict[str, Dict[str, Any]] = {}
        candidate_sem_score: Dict[str, float] = {}
        candidate_kw_score: Dict[str, float] = {}

        # Index semantic ranks
        for rank, item in enumerate(semantic_results, start=1):
            cid = item["chunk_id"]
            candidate_meta[cid] = item
            candidate_sem_score[cid] = item.get("score", 0.0)
            if strategy == "rrf":
                combined_scores[cid] = combined_scores.get(cid, 0.0) + (1.0 / (60.0 + rank))
            else:
                combined_scores[cid] = combined_scores.get(cid, 0.0) + (1.0 - settings.HYBRID_FUSION_ALPHA) * item.get("score", 0.0)

        # Index BM25 ranks
        for rank, item in enumerate(keyword_results, start=1):
            cid = item["chunk_id"]
            if cid not in candidate_meta:
                candidate_meta[cid] = item
            candidate_kw_score[cid] = item.get("score", 0.0)
            if strategy == "rrf":
                combined_scores[cid] = combined_scores.get(cid, 0.0) + (1.0 / (60.0 + rank))
            else:
                combined_scores[cid] = combined_scores.get(cid, 0.0) + settings.HYBRID_FUSION_ALPHA * item.get("score", 0.0)

        # Sort by final score
        sorted_cids = sorted(combined_scores.keys(), key=lambda c: combined_scores[c], reverse=True)

        final_items: List[SearchResultItem] = []
        for cid in sorted_cids[:top_k]:
            data = candidate_meta[cid]
            meta = data.get("metadata", {})
            final_items.append(
                SearchResultItem(
                    chunk_id=cid,
                    document_id=meta.get("document_id", "unknown_doc"),
                    matter_id=meta.get("matter_id", "unknown_matter"),
                    document_title=meta.get("document_title", meta.get("document_id", "Document")),
                    page_number=int(meta.get("page_number", 1)),
                    text_content=data.get("text_content", ""),
                    score=float(combined_scores[cid]),
                    semantic_score=candidate_sem_score.get(cid),
                    keyword_score=candidate_kw_score.get(cid),
                    classification=meta.get("classification", "confidential"),
                )
            )

        return final_items
