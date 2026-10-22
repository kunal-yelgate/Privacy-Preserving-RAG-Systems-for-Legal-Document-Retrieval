"""
Unit tests for legal text normalization and page-aware chunking.
"""
from backend.app.domain.enums import ClassificationLevel
from backend.app.services.chunking_service import ChunkingService


def test_normalize_legal_text():
    raw_text = "Section  4.1 \r\n\r\n\r\n  The Executive agrees...  "
    normalized = ChunkingService.normalize_legal_text(raw_text)
    assert "\r" not in normalized
    assert "Section 4.1" in normalized
    assert "\n\n\n" not in normalized


def test_chunking_preserves_page_numbers():
    service = ChunkingService(chunk_size=100, chunk_overlap=20)
    pages = [
        {"page_number": 1, "text": "Page one short legal clause."},
        {"page_number": 2, "text": "Page two second legal covenant."},
    ]

    chunks = service.chunk_document(
        document_id="doc_test_1",
        matter_id="matter-101",
        pages=pages,
        classification=ClassificationLevel.CONFIDENTIAL,
    )

    assert len(chunks) == 2
    assert chunks[0]["page_number"] == 1
    assert chunks[0]["matter_id"] == "matter-101"
    assert chunks[1]["page_number"] == 2
    assert chunks[1]["document_id"] == "doc_test_1"
