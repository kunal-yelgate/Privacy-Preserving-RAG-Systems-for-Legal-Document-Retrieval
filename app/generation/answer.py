import re
from dataclasses import dataclass

from app.security.citations import Citation, citation_for, validate_citations
from app.security.filter import Chunk

_CITATION_PATTERN = re.compile(r"\[([A-Za-z0-9:_-]+)\]")


@dataclass(frozen=True)
class ValidatedAnswer:
    text: str
    citations: list[Citation]
    abstained: bool


def validate_generated_answer(text: str, evidence: list[Chunk]) -> ValidatedAnswer:
    evidence_by_id = {chunk.chunk_id: chunk for chunk in evidence}
    cited_ids = _CITATION_PATTERN.findall(text)
    citations = validate_citations(
        [
            citation_for(evidence_by_id[cited_id])
            for cited_id in cited_ids
            if cited_id in evidence_by_id
        ],
        evidence,
    )
    unsupported_ids = [cited_id for cited_id in cited_ids if cited_id not in evidence_by_id]
    return ValidatedAnswer(
        text=text,
        citations=citations,
        abstained=not citations or bool(unsupported_ids),
    )
