"""
BM25 keyword search implementation using rank-bm25.
Enforces matter isolation for keyword retrieval.
"""
import re
from typing import Any, Dict, List, Optional
from rank_bm25 import BM25Okapi

from backend.app.core.config import settings
from backend.app.core.logging import logger


class BM25IndexManager:
    """Manages matter-scoped BM25 keyword search indices."""

    def __init__(self, k1: float = settings.BM25_K1, b: float = settings.BM25_B):
        self.k1 = k1
        self.b = b
        # Structure: {matter_id: {"chunks": [...], "model": BM25Okapi, "tokens": [...]}}
        self._indices: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def tokenize(cls, text: str) -> List[str]:
        """Simple, legal-aware tokenization: lower-cased alphanumeric tokens."""
        return re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", text.lower())

    def index_chunks(self, matter_id: str, chunks: List[Dict[str, Any]]) -> None:
        """Adds or updates chunks for a specific matter in the BM25 index."""
        if matter_id not in self._indices:
            self._indices[matter_id] = {"chunks": [], "model": None, "tokens": []}

        existing_chunks = self._indices[matter_id]["chunks"]
        existing_ids = {c["chunk_id"] for c in existing_chunks}

        # Filter out duplicates
        for chunk in chunks:
            if chunk["chunk_id"] not in existing_ids:
                existing_chunks.append(chunk)

        # Recompute corpus tokens and model
        corpus = [self.tokenize(c["text_content"]) for c in existing_chunks]
        if corpus:
            self._indices[matter_id]["tokens"] = corpus
            self._indices[matter_id]["model"] = BM25Okapi(corpus, k1=self.k1, b=self.b)
            logger.info(f"Re-indexed BM25 for matter {matter_id} with {len(existing_chunks)} chunks.")

    def search(
        self,
        query: str,
        matter_id: str,
        top_k: int = 5,
        allowed_classifications: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Searches BM25 index for the specified matter only."""
        if matter_id not in self._indices or not self._indices[matter_id]["model"]:
            return []

        matter_data = self._indices[matter_id]
        chunks = matter_data["chunks"]
        model = matter_data["model"]

        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        raw_scores = model.get_scores(query_tokens)

        # Filter and rank
        scored_candidates: List[Dict[str, Any]] = []
        max_score = max(raw_scores) if len(raw_scores) > 0 and max(raw_scores) > 0 else 1.0

        for idx, score in enumerate(raw_scores):
            if score <= 0:
                continue

            chunk = chunks[idx]
            classification = chunk.get("classification")
            if allowed_classifications and classification not in allowed_classifications:
                continue

            normalized_score = min(1.0, score / max_score)
            scored_candidates.append({
                "chunk_id": chunk["chunk_id"],
                "text_content": chunk["text_content"],
                "score": float(normalized_score),
                "metadata": {
                    "document_id": chunk.get("document_id"),
                    "matter_id": matter_id,
                    "page_number": chunk.get("page_number", 1),
                    "classification": classification,
                },
            })

        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        return scored_candidates[:top_k]

    def remove_document(self, matter_id: str, document_id: str) -> None:
        """Removes a document's chunks from a matter's BM25 index."""
        if matter_id not in self._indices:
            return

        chunks = [c for c in self._indices[matter_id]["chunks"] if c.get("document_id") != document_id]
        self._indices[matter_id]["chunks"] = chunks
        if chunks:
            corpus = [self.tokenize(c["text_content"]) for c in chunks]
            self._indices[matter_id]["tokens"] = corpus
            self._indices[matter_id]["model"] = BM25Okapi(corpus, k1=self.k1, b=self.b)
        else:
            self._indices[matter_id]["tokens"] = []
            self._indices[matter_id]["model"] = None
        logger.info(f"Removed document {document_id} from BM25 index for matter {matter_id}")
