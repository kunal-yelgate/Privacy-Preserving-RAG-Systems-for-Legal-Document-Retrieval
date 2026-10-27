from pathlib import Path

from app.ingest.models import ExtractedPage


class ExtractionError(RuntimeError):
    """Raised when a local document cannot be extracted safely."""


class OcrUnavailableError(ExtractionError):
    """Raised when OCR is required but no local OCR runtime is available."""


def extract_document(path: Path) -> list[ExtractedPage]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf(path)
    if suffix == ".docx":
        return _extract_docx(path)
    raise ExtractionError(f"unsupported document type: {suffix or 'none'}")


def _extract_pdf(path: Path) -> list[ExtractedPage]:
    try:
        import fitz

        document = fitz.open(path)
    except Exception as error:
        raise ExtractionError("PDF could not be opened") from error
    pages = [
        ExtractedPage(index + 1, page.get_text("text").strip())
        for index, page in enumerate(document)
    ]
    if not any(page.text for page in pages):
        raise OcrUnavailableError("PDF contains no extractable text and OCR is unavailable")
    return pages


def _extract_docx(path: Path) -> list[ExtractedPage]:
    try:
        from docx import Document

        document = Document(path)
    except Exception as error:
        raise ExtractionError("DOCX could not be opened") from error
    text = "\n".join(
        paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()
    )
    if not text:
        raise ExtractionError("DOCX contains no extractable text")
    return [ExtractedPage(1, text)]
