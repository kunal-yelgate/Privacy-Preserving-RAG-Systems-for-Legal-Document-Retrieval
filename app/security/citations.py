from dataclasses import dataclass

from app.security.filter import Chunk


@dataclass(frozen=True)
class Citation:
    chunk_id: str
    document_id: str
    tier: str
    matter_id: str | None
    court: str | None
    date: str | None
    paragraph: int | None


def citation_for(chunk: Chunk) -> Citation:
    return Citation(
        chunk_id=chunk.chunk_id,
        document_id=chunk.document_id,
        tier=chunk.tier,
        matter_id=chunk.matter_id,
        court=chunk.court,
        date=chunk.date,
        paragraph=chunk.paragraph,
    )


def validate_citations(citations: list[Citation], evidence: list[Chunk]) -> list[Citation]:
    evidence_ids = {chunk.chunk_id for chunk in evidence}
    validated: list[Citation] = []
    seen: set[str] = set()
    for citation in citations:
        if citation.chunk_id in evidence_ids and citation.chunk_id not in seen:
            validated.append(citation)
            seen.add(citation.chunk_id)
    return validated
