"""
Document ingestion pipeline service.
Handles validation, storage, page-aware text extraction, chunking,
batch local embedding generation, vector indexing, and BM25 indexing.
"""
from pathlib import Path
from typing import Optional, Tuple
from backend.app.core.config import settings
from backend.app.core.exceptions import (
    DocumentExtractionError,
    InvalidRequestError,
    UnsupportedDocumentError,
)
from backend.app.core.logging import logger
from backend.app.domain.enums import ClassificationLevel, IngestionStatus
from backend.app.infrastructure.document_parsers.pdf_parser import PDFDocumentParser
from backend.app.infrastructure.document_parsers.text_parser import TextDocumentParser
from backend.app.infrastructure.embeddings.ollama_embeddings import OllamaEmbeddingClient
from backend.app.infrastructure.filesystem.file_manager import SafeFileManager
from backend.app.infrastructure.keyword_search.bm25_index import BM25IndexManager
from backend.app.infrastructure.vector_store.chroma_store import ChromaVectorStore
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.schemas.document import DocumentMetadata
from backend.app.services.chunking_service import ChunkingService


class IngestionService:
    """Orchestrates document ingestion, extraction, and persistent indexing."""

    def __init__(
        self,
        doc_repo: DocumentRepository,
        vector_store: ChromaVectorStore,
        bm25_manager: BM25IndexManager,
        embedding_client: OllamaEmbeddingClient,
        chunking_service: ChunkingService,
    ):
        self.doc_repo = doc_repo
        self.vector_store = vector_store
        self.bm25_manager = bm25_manager
        self.embedding_client = embedding_client
        self.chunking_service = chunking_service
        self.pdf_parser = PDFDocumentParser()
        self.text_parser = TextDocumentParser()

    async def ingest_document(
        self,
        filename: str,
        content: bytes,
        matter_id: str,
        title: Optional[str] = None,
        classification: ClassificationLevel = ClassificationLevel.CONFIDENTIAL,
    ) -> DocumentMetadata:
        """
        Executes complete ingestion pipeline:
        Validate -> Save -> Hash -> Extract -> Chunk -> Embed -> Index -> Update DB.
        """
        # 1. Validate file extension
        ext = Path(filename).suffix.lower()
        if ext not in settings.SUPPORTED_EXTENSIONS:
            raise UnsupportedDocumentError(
                f"Unsupported file format '{ext}'. Only {settings.SUPPORTED_EXTENSIONS} are supported."
            )

        if not content:
            raise InvalidRequestError("Uploaded file content is empty.")

        doc_title = title.strip() if title and title.strip() else Path(filename).stem

        # 2. Save original safely and compute SHA-256
        doc_id, saved_path, content_hash = SafeFileManager.save_original(filename, content)

        # 3. Check for duplicates in the same matter
        existing_doc = self.doc_repo.find_by_hash(content_hash, matter_id)
        if existing_doc and existing_doc.status == IngestionStatus.COMPLETED:
            logger.info(f"Duplicate document detected (hash={content_hash[:8]}...) in matter {matter_id}")
            # Clean up temporary original
            SafeFileManager.delete_document_file(saved_path)
            return existing_doc

        # 4. Create pending DB record
        doc_meta = self.doc_repo.create(
            document_id=doc_id,
            matter_id=matter_id,
            title=doc_title,
            original_filename=Path(filename).name,
            file_extension=ext,
            file_size_bytes=len(content),
            content_hash=content_hash,
            classification=classification,
        )

        try:
            # 5. Extract pages
            self.doc_repo.update_status(doc_id, IngestionStatus.PARSING)
            if ext == ".pdf":
                pages = self.pdf_parser.parse(saved_path)
            elif ext == ".txt":
                pages = self.text_parser.parse(saved_path)
            else:
                raise UnsupportedDocumentError(f"No parser available for {ext}")

            # 6. Chunk extracted pages
            self.doc_repo.update_status(doc_id, IngestionStatus.CHUNKING, total_pages=len(pages))
            chunks = self.chunking_service.chunk_document(
                document_id=doc_id,
                matter_id=matter_id,
                pages=pages,
                classification=classification,
            )

            if not chunks:
                raise DocumentExtractionError("Document parsing produced no indexable chunks.")

            # 7. Generate embeddings in small batches
            self.doc_repo.update_status(doc_id, IngestionStatus.INDEXING, total_chunks=len(chunks))
            chunk_texts = [c["text_content"] for c in chunks]
            embeddings = await self.embedding_client.get_embeddings_batch(chunk_texts)

            # 8. Index into ChromaDB
            chunk_ids = [c["chunk_id"] for c in chunks]
            metadatas = [
                {
                    "document_id": doc_id,
                    "matter_id": matter_id,
                    "document_title": doc_title,
                    "page_number": int(c["page_number"]),
                    "chunk_index": int(c["chunk_index"]),
                    "classification": classification.value if hasattr(classification, "value") else classification,
                }
                for c in chunks
            ]
            self.vector_store.add_chunks(
                chunk_ids=chunk_ids,
                embeddings=embeddings,
                documents=chunk_texts,
                metadatas=metadatas,
            )

            # 9. Index into BM25
            self.bm25_manager.index_chunks(matter_id, chunks)

            # 10. Mark completed in DB
            self.doc_repo.update_status(
                doc_id,
                IngestionStatus.COMPLETED,
                total_pages=len(pages),
                total_chunks=len(chunks),
            )
            logger.info(f"Completed ingestion for document {doc_id} ({len(pages)} pages, {len(chunks)} chunks)")
            return self.doc_repo.get_by_id(doc_id)

        except Exception as e:
            logger.error(f"Ingestion failed for document {doc_id}: {e}")
            # Quarantine file
            SafeFileManager.quarantine_file(saved_path, str(e))
            self.doc_repo.update_status(doc_id, IngestionStatus.FAILED, error_message=str(e)[:300])
            raise

    def delete_document(self, document_id: str, matter_id: str) -> bool:
        """Removes document from SQLite, ChromaDB, and BM25."""
        # 1. Remove vectors from ChromaDB
        self.vector_store.delete_by_document_id(document_id)
        # 2. Remove from BM25
        self.bm25_manager.remove_document(matter_id, document_id)
        # 3. Remove DB record
        return self.doc_repo.delete(document_id)
