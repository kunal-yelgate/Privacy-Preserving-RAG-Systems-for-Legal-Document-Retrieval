"""
Text chunking service tailored for legal texts.
Preserves page references, statutory citations, and matter metadata across chunks.
"""
import re
from typing import Any, Dict, List
from backend.app.core.config import settings
from backend.app.domain.enums import ClassificationLevel
from backend.app.schemas.document import DocumentChunkSchema


class ChunkingService:
    """Chunks legal documents into overlapping passages while retaining provenance metadata."""

    def __init__(self, chunk_size: int = settings.CHUNK_SIZE, chunk_overlap: int = settings.CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    @classmethod
    def normalize_legal_text(cls, text: str) -> str:
        """
        Conservative normalization for legal text:
        - Collapses repeated newlines and excessive spaces
        - Preserves legal punctuation, section symbols (§), quotes, brackets
        """
        # Replace carriage returns
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Replace multiple spaces/tabs on the same line
        text = re.sub(r"[ \t]+", " ", text)
        # Collapse 3+ newlines to 2 (preserve paragraph breaks)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def chunk_document(
        self,
        document_id: str,
        matter_id: str,
        pages: List[Dict[str, Any]],
        classification: ClassificationLevel = ClassificationLevel.CONFIDENTIAL,
    ) -> List[Dict[str, Any]]:
        """
        Splits extracted pages into overlapping chunks.
        Each chunk is tagged with its source page number and matter ID.
        """
        chunks: List[Dict[str, Any]] = []
        chunk_counter = 0

        for page in pages:
            page_num = page["page_number"]
            page_text = self.normalize_legal_text(page["text"])

            if not page_text:
                continue

            # Split text by sentences or paragraphs if within boundary
            words = page_text.split()
            if not words:
                continue

            # If page is shorter than chunk size, keep it as a single chunk
            if len(page_text) <= self.chunk_size:
                chunk_id = f"{document_id}_p{page_num}_c{chunk_counter}"
                chunks.append({
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "matter_id": matter_id,
                    "page_number": page_num,
                    "chunk_index": chunk_counter,
                    "text_content": page_text,
                    "token_count": len(words),
                    "classification": classification.value if hasattr(classification, "value") else classification,
                })
                chunk_counter += 1
                continue

            # Sliding window over words
            # Approximate words per chunk: chunk_size / 6 characters per word
            words_per_chunk = max(20, self.chunk_size // 6)
            words_overlap = max(5, self.chunk_overlap // 6)
            step = max(1, words_per_chunk - words_overlap)

            for i in range(0, len(words), step):
                chunk_words = words[i : i + words_per_chunk]
                chunk_str = " ".join(chunk_words)

                # Skip tiny orphan fragments at the end of a page
                if len(chunk_words) < 8 and chunks and i > 0:
                    break

                chunk_id = f"{document_id}_p{page_num}_c{chunk_counter}"
                chunks.append({
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "matter_id": matter_id,
                    "page_number": page_num,
                    "chunk_index": chunk_counter,
                    "text_content": chunk_str,
                    "token_count": len(chunk_words),
                    "classification": classification.value if hasattr(classification, "value") else classification,
                })
                chunk_counter += 1

                if i + words_per_chunk >= len(words):
                    break

        return chunks
