"""
Citation service for verifying, linking, and grounding generated legal statements
against retrieved documentary evidence.
"""
import re
from typing import Dict, List, Tuple
from backend.app.schemas.chat import CitationReference
from backend.app.schemas.search import SearchResultItem


class CitationService:
    """Validates citations in generated answers against authorized retrieved passages."""

    CITE_PATTERN = re.compile(r"\[cite-(\d+)\]", re.IGNORECASE)

    @classmethod
    def format_evidence_context(cls, results: List[SearchResultItem]) -> Tuple[str, Dict[str, SearchResultItem]]:
        """
        Formats retrieved chunks into numbered context blocks.
        Returns: (formatted_context_string, mapping_of_cite_key_to_chunk)
        """
        context_blocks = []
        cite_map: Dict[str, SearchResultItem] = {}

        for i, item in enumerate(results, start=1):
            cite_key = f"cite-{i}"
            cite_map[cite_key] = item
            header = (
                f"--- EVIDENCE [{cite_key}] (Document: '{item.document_title}', Page {item.page_number}) ---"
            )
            context_blocks.append(f"{header}\n{item.text_content}")

        return "\n\n".join(context_blocks), cite_map

    @classmethod
    def extract_and_verify_citations(
        cls,
        answer_text: str,
        cite_map: Dict[str, SearchResultItem],
    ) -> List[CitationReference]:
        """
        Parses all citations in the answer text, ensures they reference authorized chunks in cite_map,
        and constructs validated CitationReference objects.
        """
        matches = cls.CITE_PATTERN.findall(answer_text)
        referenced_keys = set(f"cite-{m}" for m in matches)

        verified_citations: List[CitationReference] = []

        for cite_key in sorted(referenced_keys):
            if cite_key in cite_map:
                chunk = cite_map[cite_key]
                verified_citations.append(
                    CitationReference(
                        citation_id=cite_key,
                        chunk_id=chunk.chunk_id,
                        document_id=chunk.document_id,
                        document_title=chunk.document_title,
                        matter_id=chunk.matter_id,
                        page_number=chunk.page_number,
                        snippet=chunk.text_content[:200] + ("..." if len(chunk.text_content) > 200 else ""),
                    )
                )

        return verified_citations
