import sqlite3
from pathlib import Path

from app.ingest.chunk import chunk_pages
from app.ingest.models import DocumentMetadata, ExtractedPage
from app.ingest.service import IngestionService
from app.retrieval.embeddings import LocalHashEmbedder
from app.retrieval.store import LocalIndex


def test_chunking_preserves_page_paragraph_and_section() -> None:
    chunks = chunk_pages(
        "doc-1",
        "matter-1",
        [ExtractedPage(2, "Section 12: The court shall consider evidence.\n\nA second paragraph.")],
        max_characters=200,
    )
    assert chunks[0].page == 2
    assert chunks[0].paragraph == 1
    assert chunks[0].section == "Section 12"
    assert chunks[1].paragraph == 2


def test_invalid_metadata_is_quarantined_without_indexing(tmp_path: Path) -> None:
    connection = sqlite3.connect(":memory:")
    index = LocalIndex(connection, 8)
    service = IngestionService(connection, index, LocalHashEmbedder(8))
    metadata = DocumentMetadata("doc-1", "", "case.txt", "text/plain")
    assert service.ingest(metadata, tmp_path / "case.txt") == "quarantined"
    status = connection.execute(
        "SELECT status, quarantine_reason FROM documents WHERE document_id = 'doc-1'"
    ).fetchone()
    assert status == ("quarantined", "missing matter_id")


def test_docx_ingestion_indexes_only_private_chunks(tmp_path: Path) -> None:
    from docx import Document

    path = tmp_path / "case.docx"
    document = Document()
    document.add_paragraph("Section 4: Synthetic private evidence.")
    document.save(path)
    connection = sqlite3.connect(":memory:")
    index = LocalIndex(connection, 8)
    service = IngestionService(connection, index, LocalHashEmbedder(8))
    metadata = DocumentMetadata(
        "doc-1",
        "matter-1",
        path.name,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    assert service.ingest(metadata, path) == "indexed"
    row = connection.execute("SELECT tier, matter_id FROM chunks").fetchone()
    assert row == ("private", "matter-1")
