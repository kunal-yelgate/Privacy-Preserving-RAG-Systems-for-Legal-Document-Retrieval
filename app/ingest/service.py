import sqlite3
from pathlib import Path

from app.ingest.chunk import chunk_pages
from app.ingest.extract import ExtractionError, extract_document
from app.ingest.metadata import validate_private_metadata
from app.ingest.models import DocumentMetadata
from app.retrieval.embeddings import LocalHashEmbedder
from app.retrieval.store import LocalIndex
from app.security.filter import Chunk


class IngestionService:
    def __init__(
        self,
        connection: sqlite3.Connection,
        index: LocalIndex,
        embedder: LocalHashEmbedder,
    ) -> None:
        self.connection = connection
        self.index = index
        self.embedder = embedder
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                matter_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                media_type TEXT NOT NULL,
                status TEXT NOT NULL,
                quarantine_reason TEXT
            )
            """
        )
        self.connection.commit()

    def ingest(self, metadata: DocumentMetadata, path: Path) -> str:
        reason = validate_private_metadata(metadata)
        if reason is not None:
            self._record(metadata, "quarantined", reason)
            return "quarantined"
        try:
            pages = extract_document(path)
            chunks = chunk_pages(metadata.document_id, metadata.matter_id, pages)
            if not chunks:
                raise ExtractionError("document produced no chunks")
            for chunk in chunks:
                self.index.add(
                    Chunk(
                        chunk_id=chunk.chunk_id,
                        document_id=chunk.document_id,
                        text=chunk.text,
                        tier="private",
                        matter_id=chunk.matter_id,
                        paragraph=chunk.paragraph,
                    ),
                    self.embedder.embed(chunk.text),
                )
        except ExtractionError as error:
            self._record(metadata, "quarantined", str(error))
            return "quarantined"
        self._record(metadata, "indexed", None)
        return "indexed"

    def _record(self, metadata: DocumentMetadata, status: str, reason: str | None) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO documents
            (document_id, matter_id, filename, media_type, status, quarantine_reason)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                metadata.document_id,
                metadata.matter_id,
                metadata.filename,
                metadata.media_type,
                status,
                reason,
            ),
        )
        self.connection.commit()

    def list_documents(self, matter_id: str) -> list[dict[str, str | None]]:
        rows = self.connection.execute(
            """
            SELECT document_id, filename, media_type, status, quarantine_reason
            FROM documents WHERE matter_id = ? ORDER BY document_id
            """,
            (matter_id,),
        ).fetchall()
        return [
            {
                "document_id": str(document_id),
                "filename": str(filename),
                "media_type": str(media_type),
                "status": str(status),
                "quarantine_reason": reason,
            }
            for document_id, filename, media_type, status, reason in rows
        ]
