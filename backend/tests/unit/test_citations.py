"""
Unit tests for CitationService parsing and verification against authorized passages.
"""
from backend.app.schemas.search import SearchResultItem
from backend.app.services.citation_service import CitationService


def test_format_evidence_and_extract_valid_citations():
    mock_chunks = [
        SearchResultItem(
            chunk_id="chunk_1",
            document_id="doc_1",
            matter_id="matter-101",
            document_title="Merger Agreement",
            page_number=1,
            text_content="Purchase price is USD 45,000,000.",
            score=0.95,
            classification="confidential",
        ),
        SearchResultItem(
            chunk_id="chunk_2",
            document_id="doc_1",
            matter_id="matter-101",
            document_title="Merger Agreement",
            page_number=2,
            text_content="Governed under laws of Republic of India.",
            score=0.88,
            classification="confidential",
        ),
    ]

    context, cite_map = CitationService.format_evidence_context(mock_chunks)
    assert "[cite-1]" in context
    assert "[cite-2]" in context

    # LLM answer references [cite-1] and non-existent [cite-99]
    answer = "The acquisition price is USD 45M [cite-1]. An invented fact is [cite-99]."
    verified = CitationService.extract_and_verify_citations(answer, cite_map)

    assert len(verified) == 1
    assert verified[0].citation_id == "cite-1"
    assert verified[0].document_title == "Merger Agreement"
    assert verified[0].page_number == 1
    # Verify [cite-99] was discarded as unauthorized/hallucinated
    assert not any(c.citation_id == "cite-99" for c in verified)
