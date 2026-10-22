"""
Evidence-grounded chat and legal Q&A API routes.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status

from backend.app.core.dependencies import (
    get_auth_service,
    get_chat_repo,
    get_current_user,
    get_generation_service,
    get_retrieval_service,
)
from backend.app.core.exceptions import NotFoundError
from backend.app.repositories.chat_repository import ChatRepository
from backend.app.schemas.chat import (
    ChatMessageSchema,
    ChatRequest,
    ChatResponse,
    ChatSessionSchema,
)
from backend.app.schemas.user import UserResponse
from backend.app.services.authorization_service import AuthorizationService
from backend.app.services.generation_service import GenerationService
from backend.app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/chat", tags=["Research / Chat"])


@router.post("", response_model=ChatResponse)
async def ask_question(
    payload: ChatRequest,
    current_user: UserResponse = Depends(get_current_user),
    auth_service: AuthorizationService = Depends(get_auth_service),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    generation_service: GenerationService = Depends(get_generation_service),
):
    """
    Submits a natural-language legal question for an authorized matter.
    Retrieves authorized evidence chunks, invokes local Ollama LLM, validates citations,
    and returns an evidence-grounded response.
    """
    auth_service.authorize_matter_access(current_user, payload.matter_id, action="chat")

    # Retrieve authorized evidence
    evidence = await retrieval_service.search(
        query=payload.question,
        matter_id=payload.matter_id,
        top_k=payload.top_k,
    )

    # Generate answer with citation validation and prompt defense
    response = await generation_service.answer_question(
        question=payload.question,
        matter_id=payload.matter_id,
        user_id=current_user.user_id,
        evidence=evidence,
        session_id=payload.session_id,
    )

    return response


@router.get("/sessions", response_model=List[ChatSessionSchema])
async def list_chat_sessions(
    matter_id: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_user),
    chat_repo: ChatRepository = Depends(get_chat_repo),
    auth_service: AuthorizationService = Depends(get_auth_service),
):
    """Lists recent conversation sessions for the current user."""
    if matter_id:
        auth_service.authorize_matter_access(current_user, matter_id, action="read")
    return chat_repo.list_sessions(current_user.user_id, matter_id=matter_id)


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageSchema])
async def get_session_messages(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user),
    chat_repo: ChatRepository = Depends(get_chat_repo),
    auth_service: AuthorizationService = Depends(get_auth_service),
):
    """Retrieves all conversation messages and citations for a session."""
    session = chat_repo.get_session(session_id)
    if not session:
        raise NotFoundError("Chat session not found.")

    auth_service.authorize_matter_access(current_user, session.matter_id, action="read")
    return chat_repo.get_messages(session_id)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user),
    chat_repo: ChatRepository = Depends(get_chat_repo),
    auth_service: AuthorizationService = Depends(get_auth_service),
):
    """Deletes a chat session and associated messages."""
    session = chat_repo.get_session(session_id)
    if not session:
        raise NotFoundError("Chat session not found.")

    auth_service.authorize_matter_access(current_user, session.matter_id, action="delete")
    chat_repo.delete_session(session_id)
