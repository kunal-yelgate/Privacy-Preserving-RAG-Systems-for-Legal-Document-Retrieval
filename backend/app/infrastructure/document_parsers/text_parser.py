"""
Plain text parser for legal documents.
Detects page delimiters or splits by standard form feeds while preserving page references.
"""
from pathlib import Path
from typing import Dict, List, Any
import re
from backend.app.core.exceptions import DocumentExtractionError


class TextDocumentParser:
    """Parses plain text documents into page-attributed text blocks."""

    PAGE_BREAK_PATTERN = re.compile(
        r"(?:---\s*(?:PAGE|Page)\s*(\d+)\s*---|\[\s*(?:PAGE|Page)\s*(\d+)\s*\]|\x0c)",
        re.IGNORECASE,
    )

    def parse(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Parses text file and returns a list of pages:
        [{"page_number": int, "text": str}]
        """
        if not file_path.exists():
            raise DocumentExtractionError(f"File not found: {file_path.name}")

        content = None
        for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            try:
                content = file_path.read_text(encoding=enc)
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            raise DocumentExtractionError(f"Unable to decode text file: {file_path.name}")

        if not content.strip():
            raise DocumentExtractionError("Text document is empty.")

        # Split on page breaks if present
        parts = self.PAGE_BREAK_PATTERN.split(content)
        pages: List[Dict[str, Any]] = []

        if len(parts) == 1:
            # Single page document
            pages.append({"page_number": 1, "text": content.strip()})
        else:
            current_page_num = 1
            idx = 0
            while idx < len(parts):
                segment = parts[idx]
                if segment is None:
                    idx += 1
                    continue
                # If matched page number group
                if segment.isdigit():
                    current_page_num = int(segment)
                elif segment.strip():
                    pages.append({"page_number": current_page_num, "text": segment.strip()})
                    current_page_num += 1
                idx += 1

        if not pages:
            pages.append({"page_number": 1, "text": content.strip()})

        return pages
