"""
Hybrid search API endpoint with matter boundary authorization.
"""
from fastapi import APIRouter, Depends

from backend.app.core.dependencies import (
    get_auth_service,
    get_current_user,
    get_retrieval_service,
)
from backend.app.schemas.search import SearchRequest, SearchResponse
from backend.app.schemas.user import UserResponse
from backend.app.services.authorization_service import AuthorizationService
from backend.app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
async def search_documents(
    payload: SearchRequest,
    current_user: UserResponse = Depends(get_current_user),
    auth_service: AuthorizationService = Depends(get_auth_service),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
):
    """
    Executes authorized hybrid retrieval (ChromaDB + BM25) for a legal query.
    Enforces matter-level access and server-side filtering.
    """
    auth_service.authorize_matter_access(current_user, payload.matter_id, action="search")

    class_filters = [c.value for c in payload.classification_filter] if payload.classification_filter else None
    results = await retrieval_service.search(
        query=payload.query,
        matter_id=payload.matter_id,
        top_k=payload.top_k,
        allowed_classifications=class_filters,
    )

    return SearchResponse(
        query=payload.query,
        matter_id=payload.matter_id,
        total_results=len(results),
        results=results,
    )
