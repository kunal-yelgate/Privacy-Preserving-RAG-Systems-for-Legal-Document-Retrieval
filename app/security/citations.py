from dataclasses import dataclass

from app.security.filter import Chunk


@dataclass(frozen=True)
class Citation:
    chunk_id: str
    tier: str
    matter_id: str | None
    court: str | None
    date: str | None
    paragraph: int | None


def citation_for(chunk: Chunk) -> Citation:
    return Citation(
        chunk_id=chunk.chunk_id,
        tier=chunk.tier,
        matter_id=chunk.matter_id,
        court=chunk.court,
        date=chunk.date,
        paragraph=chunk.paragraph,
    )


def validate_citations(citations: list[Citation], evidence: list[Chunk]) -> list[Citation]:
    evidence_ids = {chunk.chunk_id for chunk in evidence}
    return [citation for citation in citations if citation.chunk_id in evidence_ids]
