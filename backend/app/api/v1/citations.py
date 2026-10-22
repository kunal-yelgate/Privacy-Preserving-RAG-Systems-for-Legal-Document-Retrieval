"""
Citation inspection and verification API routes.
"""
from fastapi import APIRouter, Depends

from backend.app.core.dependencies import (
    get_auth_service,
    get_current_user,
    get_doc_repo,
    vector_store,
)
from backend.app.core.exceptions import NotFoundError
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.schemas.chat import CitationReference
from backend.app.schemas.user import UserResponse
from backend.app.services.authorization_service import AuthorizationService

router = APIRouter(prefix="/citations", tags=["Citations"])


@router.get("/{chunk_id}", response_model=CitationReference)
async def get_citation_details(
    chunk_id: str,
    current_user: UserResponse = Depends(get_current_user),
    auth_service: AuthorizationService = Depends(get_auth_service),
    doc_repo: DocumentRepository = Depends(get_doc_repo),
):
    """
    Fetches verified source passage and provenance metadata for a citation chunk.
    Enforces authorization check against the chunk's matter.
    """
    try:
        res = vector_store.collection.get(ids=[chunk_id], include=["documents", "metadatas"])
    except Exception:
        raise NotFoundError(f"Citation chunk '{chunk_id}' not found.")

    if not res or not res["ids"]:
        raise NotFoundError(f"Citation chunk '{chunk_id}' not found.")

    doc_text = res["documents"][0] if res.get("documents") else ""
    meta = res["metadatas"][0] if res.get("metadatas") else {}

    matter_id = meta.get("matter_id")
    if not matter_id:
        raise NotFoundError("Corrupted citation metadata: matter_id missing.")

    # Authorize matter access
    auth_service.authorize_matter_access(current_user, matter_id, action="read")

    doc_title = meta.get("document_title", meta.get("document_id", "Document"))
    page_number = int(meta.get("page_number", 1))

    return CitationReference(
        citation_id=chunk_id,
        chunk_id=chunk_id,
        document_id=meta.get("document_id", "unknown_doc"),
        document_title=doc_title,
        matter_id=matter_id,
        page_number=page_number,
        snippet=doc_text,
    )
