from app.generation.answer import validate_generated_answer
from app.security.filter import Chunk


def evidence() -> list[Chunk]:
    return [Chunk("c1", "d1", "authorized evidence", "private", "m1", paragraph=4)]


def test_generated_answer_requires_authorized_citation() -> None:
    validated = validate_generated_answer("The evidence supports this [c1].", evidence())
    assert validated.abstained is False
    assert [citation.chunk_id for citation in validated.citations] == ["c1"]


def test_unsupported_citation_abstains() -> None:
    validated = validate_generated_answer("The evidence supports this [other].", evidence())
    assert validated.abstained is True
    assert validated.citations == []


def test_missing_citation_abstains() -> None:
    validated = validate_generated_answer("The evidence supports this.", evidence())
    assert validated.abstained is True
