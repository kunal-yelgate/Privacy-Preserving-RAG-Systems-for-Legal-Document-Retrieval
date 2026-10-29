from app.generation.answer import validate_generated_answer
from app.generation.prompt import build_evidence_prompt
from app.security.filter import Chunk


def evidence() -> list[Chunk]:
    return [Chunk("c1", "d1", "authorized evidence", "private", "m1", paragraph=4)]


def test_generated_answer_requires_authorized_citation() -> None:
    validated = validate_generated_answer("The evidence supports this [c1].", evidence())
    assert validated.abstained is False
    assert [citation.chunk_id for citation in validated.citations] == ["c1"]


def test_generated_answer_resolves_compact_evidence_label() -> None:
    validated = validate_generated_answer("The evidence supports this [1].", evidence())
    assert validated.abstained is False
    assert [citation.chunk_id for citation in validated.citations] == ["c1"]


def test_repeated_citations_are_deduplicated() -> None:
    validated = validate_generated_answer("Claim [1]. Again [c1].", evidence())
    assert validated.abstained is False
    assert [citation.chunk_id for citation in validated.citations] == ["c1"]


def test_grouped_numeric_citations_are_resolved() -> None:
    validated = validate_generated_answer("Evidence supports it. [1, 1]", evidence())
    assert validated.abstained is False
    assert validated.text == "Evidence supports it. [1][1]"
    assert [citation.chunk_id for citation in validated.citations] == ["c1"]


def test_sentence_punctuation_before_citation_is_complete() -> None:
    validated = validate_generated_answer("Evidence supports it. [1]", evidence())
    assert validated.abstained is False


def test_unsupported_citation_abstains() -> None:
    validated = validate_generated_answer("The evidence supports this [other].", evidence())
    assert validated.abstained is True
    assert validated.citations == []


def test_missing_citation_abstains() -> None:
    validated = validate_generated_answer("The evidence supports this.", evidence())
    assert validated.abstained is True


def test_truncated_answer_abstains() -> None:
    validated = validate_generated_answer("The seller missed the deadline [1] because", evidence())
    assert validated.abstained is True


def test_prompt_adapts_to_non_land_case_and_question() -> None:
    contract_evidence = [
        Chunk(
            "contract-1",
            "doc-contract",
            "Clause 7.2 required replacement by March 15 after notice.",
            "private",
            "contract-matter",
            paragraph=3,
        )
    ]
    prompt = build_evidence_prompt(
        "Did the seller meet the replacement deadline?", contract_evidence
    )
    assert "Did the seller meet the replacement deadline?" in prompt
    assert "[1 | private | paragraph 3]" in prompt
    assert "Adapt the structure to the question" in prompt
    assert "This question does not ask for competing-claim outcomes" in prompt
    assert "exactly four short numbered points" not in prompt
    assert "2012 partition" not in prompt
    assert "20 ares" not in prompt
    assert "never convert units" in prompt
    assert "Do not infer jurisdiction from another matter" in prompt
    assert "required approvals and conditions" in prompt
    assert "preserve limits such as 'where legally available'" in prompt
    assert "citation markers, not speakers" in prompt
    assert "Begin with one brief sentence stating the relevant allegation" in prompt


def test_prompt_selects_conditional_format_for_title_question() -> None:
    prompt = build_evidence_prompt(
        "How will the court determine rightful ownership between the parties?", evidence()
    )
    assert "exactly four short numbered points" in prompt
    assert "what follows if the competing claim is proved" in prompt
    assert "2012 partition" not in prompt
    assert "20 ares" not in prompt
