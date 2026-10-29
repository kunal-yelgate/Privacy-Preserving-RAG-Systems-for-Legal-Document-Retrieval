import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.ingest.chunk import chunk_pages
from app.ingest.extract import ExtractionError, extract_document
from app.retrieval.embeddings import LocalHashEmbedder
from app.retrieval.store import LocalIndex
from app.security.filter import Chunk


@dataclass(frozen=True)
class PublicSource:
    source_id: str
    title: str
    license_name: str
    license_url: str | None = None


@dataclass(frozen=True)
class PublicDocument:
    document_id: str
    source_id: str
    filename: str
    media_type: str
    source_url: str


class PublicCorpusPipeline:
    """Ingest licensed public documents with immutable snapshots and rollback."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        index: LocalIndex,
        embedder: LocalHashEmbedder,
    ) -> None:
        self.connection = connection
        self.index = index
        self.embedder = embedder
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS public_sources (
                source_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                license_name TEXT NOT NULL,
                license_url TEXT
            );
            CREATE TABLE IF NOT EXISTS public_documents (
                document_id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL REFERENCES public_sources(source_id),
                filename TEXT NOT NULL,
                media_type TEXT NOT NULL,
                source_url TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                snapshot_id TEXT NOT NULL,
                status TEXT NOT NULL,
                UNIQUE(source_id, content_hash)
            );
            CREATE TABLE IF NOT EXISTS public_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL
            );
            """
        )
        self.connection.commit()

    def register_source(self, source: PublicSource) -> None:
        if not source.source_id or not source.title or not source.license_name:
            raise ValueError("public sources require identity and license metadata")
        self.connection.execute(
            """
            INSERT OR REPLACE INTO public_sources
            (source_id, title, license_name, license_url)
            VALUES (?, ?, ?, ?)
            """,
            (source.source_id, source.title, source.license_name, source.license_url),
        )
        self.connection.commit()

    def ingest(
        self,
        source: PublicSource,
        document: PublicDocument,
        path: Path,
        snapshot_id: str | None = None,
    ) -> str:
        self.register_source(source)
        snapshot = snapshot_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        self.connection.execute(
            "INSERT OR IGNORE INTO public_snapshots(snapshot_id, created_at, status) VALUES (?, ?, ?)",
            (snapshot, datetime.now(UTC).isoformat(), "active"),
        )
        content_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        existing = self.connection.execute(
            """
            SELECT document_id FROM public_documents
            WHERE source_id = ? AND content_hash = ? AND status != 'rolled_back'
            """,
            (source.source_id, content_hash),
        ).fetchone()
        if existing:
            return "duplicate"
        try:
            pages = extract_document(path)
            chunks = chunk_pages(document.document_id, "", pages)
            if not chunks:
                raise ExtractionError("document produced no chunks")
            for chunk in chunks:
                self.index.add(
                    Chunk(
                        chunk_id=f"public-{chunk.chunk_id}",
                        document_id=chunk.document_id,
                        text=chunk.text,
                        tier="public",
                        matter_id=None,
                        paragraph=chunk.paragraph,
                    ),
                    self.embedder.embed(chunk.text),
                )
        except ExtractionError:
            self.connection.execute(
                """
                INSERT OR REPLACE INTO public_documents
                (document_id, source_id, filename, media_type, source_url,
                 content_hash, snapshot_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'quarantined')
                """,
                (
                    document.document_id,
                    source.source_id,
                    document.filename,
                    document.media_type,
                    document.source_url,
                    content_hash,
                    snapshot,
                ),
            )
            self.connection.commit()
            return "quarantined"
        self.connection.execute(
            """
            INSERT OR REPLACE INTO public_documents
            (document_id, source_id, filename, media_type, source_url,
             content_hash, snapshot_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'indexed')
            """,
            (
                document.document_id,
                source.source_id,
                document.filename,
                document.media_type,
                document.source_url,
                content_hash,
                snapshot,
            ),
        )
        self.connection.commit()
        return "indexed"

    def rollback(self, snapshot_id: str) -> None:
        row = self.connection.execute(
            "SELECT 1 FROM public_snapshots WHERE snapshot_id = ?", (snapshot_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"unknown public snapshot: {snapshot_id}")
        self.connection.execute(
            "UPDATE public_snapshots SET status = 'rolled_back' WHERE snapshot_id = ?",
            (snapshot_id,),
        )
        self.connection.execute(
            "UPDATE public_documents SET status = 'rolled_back' WHERE snapshot_id = ?",
            (snapshot_id,),
        )
        self.connection.execute(
            """
            UPDATE chunks SET status = 'inactive'
            WHERE tier = 'public' AND document_id IN (
                SELECT document_id FROM public_documents
                WHERE snapshot_id = ?
            )
            """,
            (snapshot_id,),
        )
        self.connection.commit()

    def list_snapshots(self) -> list[dict[str, str]]:
        rows = self.connection.execute(
            "SELECT snapshot_id, created_at, status FROM public_snapshots ORDER BY created_at DESC"
        ).fetchall()
        return [
            {"snapshot_id": str(snapshot_id), "created_at": str(created_at), "status": str(status)}
            for snapshot_id, created_at, status in rows
        ]
