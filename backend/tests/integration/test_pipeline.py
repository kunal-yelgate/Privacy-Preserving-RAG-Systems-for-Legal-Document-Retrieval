"""
Integration test suite for ingestion, hybrid retrieval, and citation pipeline.
"""
from pathlib import Path
import pytest
from backend.app.core.config import settings
from backend.app.core.dependencies import (
    bm25_manager,
    chunking_service,
    doc_repo,
    embedding_client,
    ingestion_service,
    retrieval_service,
    vector_store,
)
from backend.app.domain.enums import ClassificationLevel


@pytest.mark.asyncio
async def test_full_ingestion_and_hybrid_retrieval():
    synthetic_txt = settings.root_path / "datasets" / "synthetic" / "matter_101_merger_agreement.txt"
    assert synthetic_txt.exists(), "Synthetic dataset file must exist"

    # Ensure matters exist in SQLite
    from backend.app.core.dependencies import matter_repo
    from backend.app.schemas.matter import MatterCreate
    if not matter_repo.get_by_id("matter-101"):
        matter_repo.create(MatterCreate(matter_id="matter-101", name="Merger Agreement Matter"))
    if not matter_repo.get_by_id("matter-102"):
        matter_repo.create(MatterCreate(matter_id="matter-102", name="Employment Dispute Matter"))

    content = synthetic_txt.read_bytes()

    # 1. Ingest document
    doc_meta = await ingestion_service.ingest_document(
        filename=synthetic_txt.name,
        content=content,
        matter_id="matter-101",
        title="Merger Agreement Apex & Nexus",
        classification=ClassificationLevel.CONFIDENTIAL,
    )

    assert doc_meta.document_id is not None
    assert doc_meta.total_pages >= 1
    assert doc_meta.total_chunks >= 1

    # 2. Search document within matter-101
    results = await retrieval_service.search(
        query="What is the purchase price acquisition consideration?",
        matter_id="matter-101",
        top_k=3,
    )

    assert len(results) > 0
    top_hit = results[0]
    assert top_hit.matter_id == "matter-101"
    assert "45,000,000" in top_hit.text_content or "Acquisition Consideration" in top_hit.text_content
    assert top_hit.page_number >= 1

    # 3. Cross-matter boundary search: searching matter-102 must NOT return this chunk
    results_matter_102 = await retrieval_service.search(
        query="What is the purchase price acquisition consideration?",
        matter_id="matter-102",
        top_k=3,
    )
    for r in results_matter_102:
        assert "CANARY-CORP-ALPHA-7892" not in r.text_content
        assert r.matter_id != "matter-101"
