import re
from dataclasses import dataclass

from app.security.citations import Citation, citation_for, validate_citations
from app.security.filter import Chunk

_CITATION_PATTERN = re.compile(r"\[([^\]]+)\]")


@dataclass(frozen=True)
class ValidatedAnswer:
    text: str
    citations: list[Citation]
    abstained: bool


def validate_generated_answer(text: str, evidence: list[Chunk]) -> ValidatedAnswer:
    text = re.sub(
        r"\[(\d+(?:\s*,\s*\d+)+)\]",
        lambda match: "".join(
            f"[{label.strip()}]" for label in match.group(1).split(",")
        ),
        text,
    )
    evidence_by_id = {chunk.chunk_id: chunk for chunk in evidence}
    # Numeric references are the short labels exposed to the model in the
    # evidence prompt; keep accepting chunk IDs for backwards compatibility.
    evidence_by_id.update(
        {str(index): chunk for index, chunk in enumerate(evidence, start=1)}
    )
    cited_ids = [
        label.strip()
        for group in _CITATION_PATTERN.findall(text)
        for label in group.split(",")
    ]
    citations = validate_citations(
        [
            citation_for(evidence_by_id[cited_id])
            for cited_id in cited_ids
            if cited_id in evidence_by_id
        ],
        evidence,
    )
    unsupported_ids = [cited_id for cited_id in cited_ids if cited_id not in evidence_by_id]
    answer_without_citations = _CITATION_PATTERN.sub("", text).rstrip()
    complete_sentence = answer_without_citations.endswith((".", "!", "?"))
    return ValidatedAnswer(
        text=text,
        citations=citations,
        abstained=not citations or bool(unsupported_ids) or not complete_sentence,
    )
