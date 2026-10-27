from app.ingest.models import DocumentMetadata


def validate_private_metadata(metadata: DocumentMetadata) -> str | None:
    if not metadata.document_id.strip():
        return "missing document_id"
    if not metadata.matter_id.strip():
        return "missing matter_id"
    if not metadata.filename.strip():
        return "missing filename"
    if metadata.media_type not in {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }:
        return "unsupported media_type"
    return None
