"""
Persistent ChromaDB vector store adapter.
Enforces local file persistence and metadata filtering by matter_id.
"""
from typing import Any, Dict, List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.app.core.config import settings
from backend.app.core.exceptions import VectorStoreError
from backend.app.core.logging import logger


class ChromaVectorStore:
    """Persistent local vector database using ChromaDB."""

    COLLECTION_NAME = "legal_rag_chunks"

    def __init__(self, persist_directory: str = str(settings.chroma_path)):
        try:
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=ChromaSettings(anonymized_telemetry=False, is_persistent=True),
            )
            self.collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"Initialized local ChromaDB store at {persist_directory}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise VectorStoreError(f"ChromaDB initialization failed: {e}")

    def add_chunks(
        self,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """Adds vectorized chunks with metadata to the persistent collection."""
        if not chunk_ids:
            return

        try:
            self.collection.upsert(
                ids=chunk_ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
            logger.info(f"Upserted {len(chunk_ids)} chunks into ChromaDB.")
        except Exception as e:
            logger.error(f"Error adding chunks to ChromaDB: {e}")
            raise VectorStoreError(f"Failed to persist vectors: {e}")

    def search_similar(
        self,
        query_embedding: List[float],
        matter_id: str,
        top_k: int = 5,
        allowed_classifications: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top_k nearest chunks matching the exact matter_id.
        Enforces server-side matter boundary filtering.
        """
        where_filter: Dict[str, Any] = {"matter_id": matter_id}
        if allowed_classifications:
            if len(allowed_classifications) == 1:
                where_filter["classification"] = allowed_classifications[0]
            else:
                where_filter["$and"] = [
                    {"matter_id": matter_id},
                    {"classification": {"$in": allowed_classifications}},
                ]

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )

            matched_items: List[Dict[str, Any]] = []
            if not results or not results["ids"] or not results["ids"][0]:
                return matched_items

            ids = results["ids"][0]
            docs = results["documents"][0] if results.get("documents") else []
            metas = results["metadatas"][0] if results.get("metadatas") else []
            distances = results["distances"][0] if results.get("distances") else []

            for i in range(len(ids)):
                # Convert cosine distance to cosine similarity score (score = 1 - distance)
                dist = distances[i] if i < len(distances) else 1.0
                score = max(0.0, min(1.0, 1.0 - dist))

                meta = metas[i] if i < len(metas) else {}
                matched_items.append({
                    "chunk_id": ids[i],
                    "text_content": docs[i] if i < len(docs) else "",
                    "score": score,
                    "metadata": meta,
                })

            return matched_items
        except Exception as e:
            logger.error(f"Vector search failed for matter {matter_id}: {e}")
            raise VectorStoreError(f"Search query failed: {e}")

    def delete_by_document_id(self, document_id: str) -> None:
        """Deletes all chunks belonging to a document from ChromaDB."""
        try:
            self.collection.delete(where={"document_id": document_id})
            logger.info(f"Deleted vector chunks for document {document_id}")
        except Exception as e:
            logger.error(f"Failed to delete chunks for document {document_id}: {e}")
            raise VectorStoreError(f"Delete chunks failed: {e}")

    def delete_by_matter_id(self, matter_id: str) -> None:
        """Deletes all chunks belonging to a matter from ChromaDB."""
        try:
            self.collection.delete(where={"matter_id": matter_id})
            logger.info(f"Deleted vector chunks for matter {matter_id}")
        except Exception as e:
            logger.error(f"Failed to delete chunks for matter {matter_id}: {e}")
            raise VectorStoreError(f"Delete matter chunks failed: {e}")

    def count(self) -> int:
        return self.collection.count()
