"""
Document management and ingestion API routes.
Enforces matter authorization, safe storage, and ingestion state tracking.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from backend.app.core.dependencies import (
    get_auth_service,
    get_current_user,
    get_doc_repo,
    get_ingestion_service,
)
from backend.app.core.exceptions import InvalidRequestError, NotFoundError
from backend.app.domain.enums import ClassificationLevel
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.schemas.document import DocumentMetadata
from backend.app.schemas.user import UserResponse
from backend.app.services.authorization_service import AuthorizationService
from backend.app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("", response_model=DocumentMetadata, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    matter_id: str = Form(...),
    title: Optional[str] = Form(None),
    classification: ClassificationLevel = Form(ClassificationLevel.CONFIDENTIAL),
    current_user: UserResponse = Depends(get_current_user),
    auth_service: AuthorizationService = Depends(get_auth_service),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    """
    Uploads and ingests a legal document (.pdf or .txt) into an authorized matter.
    Executes page extraction, chunking, and local embedding indexing.
    """
    auth_service.authorize_matter_access(current_user, matter_id, action="upload")

    if not file.filename:
        raise InvalidRequestError("Uploaded file must have a filename.")

    content = await file.read()
    if len(content) == 0:
        raise InvalidRequestError("Uploaded file is empty.")

    doc_meta = await ingestion_service.ingest_document(
        filename=file.filename,
        content=content,
        matter_id=matter_id,
        title=title,
        classification=classification,
    )
    return doc_meta


@router.get("", response_model=List[DocumentMetadata])
async def list_documents(
    matter_id: str = Query(..., description="Matter ID to list documents for"),
    current_user: UserResponse = Depends(get_current_user),
    auth_service: AuthorizationService = Depends(get_auth_service),
    doc_repo: DocumentRepository = Depends(get_doc_repo),
):
    """Lists all documents registered under the specified matter."""
    auth_service.authorize_matter_access(current_user, matter_id, action="read")
    return doc_repo.list_by_matter(matter_id)


@router.get("/{document_id}", response_model=DocumentMetadata)
async def get_document(
    document_id: str,
    current_user: UserResponse = Depends(get_current_user),
    auth_service: AuthorizationService = Depends(get_auth_service),
    doc_repo: DocumentRepository = Depends(get_doc_repo),
):
    """Retrieves metadata for a specific document."""
    doc = doc_repo.get_by_id(document_id)
    if not doc:
        raise NotFoundError("Document not found.")

    auth_service.authorize_matter_access(current_user, doc.matter_id, action="read")
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user: UserResponse = Depends(get_current_user),
    auth_service: AuthorizationService = Depends(get_auth_service),
    doc_repo: DocumentRepository = Depends(get_doc_repo),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    """Deletes document, chunks, and vector embeddings."""
    doc = doc_repo.get_by_id(document_id)
    if not doc:
        raise NotFoundError("Document not found.")

    auth_service.authorize_matter_access(current_user, doc.matter_id, action="delete")
    ingestion_service.delete_document(document_id, doc.matter_id)


@router.get("/{document_id}/status")
async def get_document_status(
    document_id: str,
    current_user: UserResponse = Depends(get_current_user),
    auth_service: AuthorizationService = Depends(get_auth_service),
    doc_repo: DocumentRepository = Depends(get_doc_repo),
):
    """Returns the current ingestion lifecycle status."""
    doc = doc_repo.get_by_id(document_id)
    if not doc:
        raise NotFoundError("Document not found.")

    auth_service.authorize_matter_access(current_user, doc.matter_id, action="read")
    return {
        "document_id": doc.document_id,
        "status": doc.status,
        "total_pages": doc.total_pages,
        "total_chunks": doc.total_chunks,
        "error_message": doc.error_message,
        "updated_at": doc.updated_at,
    }
