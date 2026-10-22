"""
PDF parser for legal documents using PyMuPDF.
Extracts text page-by-page, preserving page numbers and document structure.
"""
from pathlib import Path
from typing import Dict, List, Any
import pymupdf

from backend.app.core.exceptions import DocumentExtractionError, UnsupportedDocumentError
from backend.app.core.logging import logger


class PDFDocumentParser:
    """Extracts text content per page from PDF files using PyMuPDF."""

    def parse(self, file_path: Path) -> List[Dict[str, Any]]:
        if not file_path.exists():
            raise DocumentExtractionError(f"PDF file does not exist: {file_path.name}")

        try:
            doc = pymupdf.open(str(file_path))
        except Exception as e:
            raise DocumentExtractionError(f"Failed to open PDF document: {file_path.name}")

        if doc.is_encrypted:
            doc.close()
            raise UnsupportedDocumentError("Encrypted or password-protected PDF documents are not supported.")

        if doc.page_count == 0:
            doc.close()
            raise DocumentExtractionError("PDF document has 0 pages.")

        pages: List[Dict[str, Any]] = []
        total_extracted_chars = 0

        try:
            for page_index in range(doc.page_count):
                page_num = page_index + 1
                page = doc.load_page(page_index)
                page_text = page.get_text("text")

                # Normalize whitespace
                cleaned_text = page_text.strip()
                if cleaned_text:
                    pages.append({
                        "page_number": page_num,
                        "text": cleaned_text,
                    })
                    total_extracted_chars += len(cleaned_text)
                else:
                    # Record page even if empty/scanned so page count is preserved
                    pages.append({
                        "page_number": page_num,
                        "text": "[Empty or scanned image page - no extractable digital text]",
                    })
        finally:
            doc.close()

        if total_extracted_chars == 0:
            logger.warning(f"PDF {file_path.name} contains no digital text (may require OCR).")
            raise DocumentExtractionError(
                "PDF contains no selectable text. If this is a scanned document, OCR is required."
            )

        logger.info(f"Successfully extracted {len(pages)} pages ({total_extracted_chars} chars) from {file_path.name}")
        return pages
