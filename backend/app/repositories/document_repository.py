"""
Document repository managing SQLite metadata, ingestion status, and deduplication.
"""
from datetime import datetime, timezone
from typing import List, Optional
from backend.app.domain.enums import ClassificationLevel, IngestionStatus
from backend.app.infrastructure.database.connection import db_manager
from backend.app.schemas.document import DocumentMetadata


class DocumentRepository:
    """Manages document records in SQLite."""

    def create(
        self,
        document_id: str,
        matter_id: str,
        title: str,
        original_filename: str,
        file_extension: str,
        file_size_bytes: int,
        content_hash: str,
        classification: ClassificationLevel = ClassificationLevel.CONFIDENTIAL,
    ) -> DocumentMetadata:
        now_dt = datetime.now(timezone.utc)
        now_str = now_dt.isoformat()
        with db_manager.session() as conn:
            conn.execute(
                """
                INSERT INTO documents (
                    document_id, matter_id, title, original_filename, file_extension,
                    file_size_bytes, content_hash, classification, status,
                    total_pages, total_chunks, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', 0, 0, ?, ?)
                """,
                (
                    document_id,
                    matter_id,
                    title,
                    original_filename,
                    file_extension,
                    file_size_bytes,
                    content_hash,
                    classification.value if hasattr(classification, "value") else classification,
                    now_str,
                    now_str,
                ),
            )
        return self.get_by_id(document_id)

    def get_by_id(self, document_id: str) -> Optional[DocumentMetadata]:
        with db_manager.session() as conn:
            row = conn.execute("SELECT * FROM documents WHERE document_id = ?", (document_id,)).fetchone()
            if not row:
                return None
            return DocumentMetadata(
                document_id=row["document_id"],
                matter_id=row["matter_id"],
                title=row["title"],
                original_filename=row["original_filename"],
                file_extension=row["file_extension"],
                file_size_bytes=row["file_size_bytes"],
                content_hash=row["content_hash"],
                classification=ClassificationLevel(row["classification"]),
                status=IngestionStatus(row["status"]),
                total_pages=row["total_pages"],
                total_chunks=row["total_chunks"],
                error_message=row["error_message"],
                created_at=row["created_at"] if isinstance(row["created_at"], datetime) else datetime.fromisoformat(str(row["created_at"])),
                updated_at=row["updated_at"] if isinstance(row["updated_at"], datetime) else datetime.fromisoformat(str(row["updated_at"])),
            )

    def list_by_matter(
        self,
        matter_id: str,
        allowed_classifications: Optional[List[ClassificationLevel]] = None,
    ) -> List[DocumentMetadata]:
        with db_manager.session() as conn:
            if allowed_classifications:
                class_vals = [c.value for c in allowed_classifications]
                placeholders = ",".join("?" for _ in class_vals)
                rows = conn.execute(
                    f"SELECT * FROM documents WHERE matter_id = ? AND classification IN ({placeholders}) ORDER BY created_at DESC",
                    [matter_id, *class_vals],
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM documents WHERE matter_id = ? ORDER BY created_at DESC",
                    (matter_id,),
                ).fetchall()

            return [
                DocumentMetadata(
                    document_id=r["document_id"],
                    matter_id=r["matter_id"],
                    title=r["title"],
                    original_filename=r["original_filename"],
                    file_extension=r["file_extension"],
                    file_size_bytes=r["file_size_bytes"],
                    content_hash=r["content_hash"],
                    classification=ClassificationLevel(r["classification"]),
                    status=IngestionStatus(r["status"]),
                    total_pages=r["total_pages"],
                    total_chunks=r["total_chunks"],
                    error_message=r["error_message"],
                    created_at=r["created_at"] if isinstance(r["created_at"], datetime) else datetime.fromisoformat(str(r["created_at"])),
                    updated_at=r["updated_at"] if isinstance(r["updated_at"], datetime) else datetime.fromisoformat(str(r["updated_at"])),
                )
                for r in rows
            ]

    def update_status(
        self,
        document_id: str,
        status: IngestionStatus,
        total_pages: Optional[int] = None,
        total_chunks: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> None:
        updates = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
        params = [status.value]

        if total_pages is not None:
            updates.append("total_pages = ?")
            params.append(total_pages)
        if total_chunks is not None:
            updates.append("total_chunks = ?")
            params.append(total_chunks)
        if error_message is not None:
            updates.append("error_message = ?")
            params.append(error_message)

        params.append(document_id)
        with db_manager.session() as conn:
            conn.execute(
                f"UPDATE documents SET {', '.join(updates)} WHERE document_id = ?",
                params,
            )

    def find_by_hash(self, content_hash: str, matter_id: str) -> Optional[DocumentMetadata]:
        with db_manager.session() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE content_hash = ? AND matter_id = ?",
                (content_hash, matter_id),
            ).fetchone()
            if row:
                return self.get_by_id(row["document_id"])
        return None

    def delete(self, document_id: str) -> bool:
        with db_manager.session() as conn:
            cursor = conn.execute("DELETE FROM documents WHERE document_id = ?", (document_id,))
            return cursor.rowcount > 0
