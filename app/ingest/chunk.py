import re
from hashlib import sha256

from app.ingest.models import ExtractedPage, IngestedChunk

_SECTION_PATTERN = re.compile(
    r"(?im)^(?P<section>(?:section|article|rule|para(?:graph)?|clause)\s+[\w().-]+)\s*[:.-]?\s*"
)


def chunk_pages(
    document_id: str,
    matter_id: str,
    pages: list[ExtractedPage],
    max_characters: int = 1200,
) -> list[IngestedChunk]:
    if max_characters < 1:
        raise ValueError("max_characters must be positive")
    chunks: list[IngestedChunk] = []
    for page in pages:
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n|\n", page.text) if part.strip()]
        for paragraph_number, paragraph in enumerate(paragraphs, start=1):
            section_match = _SECTION_PATTERN.match(paragraph)
            section = section_match.group("section") if section_match else None
            for offset in range(0, len(paragraph), max_characters):
                text = paragraph[offset : offset + max_characters].strip()
                if not text:
                    continue
                digest = sha256(
                    f"{document_id}:{page.page_number}:{paragraph_number}:{offset}:{text}".encode()
                ).hexdigest()[:20]
                chunks.append(
                    IngestedChunk(
                        chunk_id=f"{document_id}:{digest}",
                        document_id=document_id,
                        matter_id=matter_id,
                        text=text,
                        page=page.page_number,
                        paragraph=paragraph_number,
                        section=section,
                    )
                )
    return chunks
