from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedPage:
    page_number: int
    text: str


@dataclass(frozen=True)
class DocumentMetadata:
    document_id: str
    matter_id: str
    filename: str
    media_type: str


@dataclass(frozen=True)
class IngestedChunk:
    chunk_id: str
    document_id: str
    matter_id: str
    text: str
    page: int
    paragraph: int | None
    section: str | None
