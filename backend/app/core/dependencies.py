"""
FastAPI dependency injection container.
Provides singleton instances of repositories, infrastructure adapters, and domain services.
"""
from typing import Annotated
from fastapi import Depends, Header

from backend.app.core.config import settings
from backend.app.core.exceptions import AuthenticationError, AuthorizationError
from backend.app.domain.enums import UserRole
from backend.app.infrastructure.embeddings.ollama_embeddings import OllamaEmbeddingClient
from backend.app.infrastructure.keyword_search.bm25_index import BM25IndexManager
from backend.app.infrastructure.llm.ollama_client import OllamaLLMClient
from backend.app.infrastructure.vector_store.chroma_store import ChromaVectorStore
from backend.app.repositories.audit_repository import AuditRepository
from backend.app.repositories.chat_repository import ChatRepository
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.repositories.matter_repository import MatterRepository
from backend.app.repositories.user_repository import UserRepository
from backend.app.schemas.user import UserResponse
from backend.app.services.authorization_service import AuthorizationService
from backend.app.services.chunking_service import ChunkingService
from backend.app.services.generation_service import GenerationService
from backend.app.services.ingestion_service import IngestionService
from backend.app.services.retrieval_service import RetrievalService
from backend.app.services.security_service import SecurityService

# Shared Singleton Instances
user_repo = UserRepository()
matter_repo = MatterRepository()
doc_repo = DocumentRepository()
audit_repo = AuditRepository()
chat_repo = ChatRepository()

vector_store = ChromaVectorStore()
bm25_manager = BM25IndexManager()
embedding_client = OllamaEmbeddingClient()
llm_client = OllamaLLMClient()
chunking_service = ChunkingService()

auth_service = AuthorizationService(user_repo=user_repo, audit_repo=audit_repo)
ingestion_service = IngestionService(
    doc_repo=doc_repo,
    vector_store=vector_store,
    bm25_manager=bm25_manager,
    embedding_client=embedding_client,
    chunking_service=chunking_service,
)
retrieval_service = RetrievalService(
    vector_store=vector_store,
    bm25_manager=bm25_manager,
    embedding_client=embedding_client,
)
generation_service = GenerationService(llm_client=llm_client, chat_repo=chat_repo)
security_service = SecurityService(audit_repo=audit_repo)


# Ensure default admin user and default researcher user exist for local offline use
def ensure_default_accounts():
    if not user_repo.get_by_username("admin"):
        user_repo.create_user("admin", "AdminSecureOffline2026!", role=UserRole.ADMIN, full_name="System Administrator")
    if not user_repo.get_by_username("researcher1"):
        user_repo.create_user("researcher1", "ResearcherPass2026!", role=UserRole.RESEARCHER, full_name="Legal Researcher 1")
    if not user_repo.get_by_username("researcher2"):
        user_repo.create_user("researcher2", "ResearcherPass2026!", role=UserRole.RESEARCHER, full_name="Legal Researcher 2")


ensure_default_accounts()


# Dependency Providers
def get_user_repo() -> UserRepository:
    return user_repo


def get_matter_repo() -> MatterRepository:
    return matter_repo


def get_doc_repo() -> DocumentRepository:
    return doc_repo


def get_audit_repo() -> AuditRepository:
    return audit_repo


def get_chat_repo() -> ChatRepository:
    return chat_repo


def get_auth_service() -> AuthorizationService:
    return auth_service


def get_ingestion_service() -> IngestionService:
    return ingestion_service


def get_retrieval_service() -> RetrievalService:
    return retrieval_service


def get_generation_service() -> GenerationService:
    return generation_service


def get_security_service() -> SecurityService:
    return security_service


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    auth_svc: AuthorizationService = Depends(get_auth_service),
) -> UserResponse:
    """Extracts and verifies Bearer token from Authorization header."""
    if not authorization:
        raise AuthenticationError("Authorization header missing.")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError("Invalid Authorization header format. Expected 'Bearer <token>'.")

    return auth_svc.verify_token(parts[1])


def get_admin_user(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """Ensures user has administrative privileges."""
    if current_user.role != UserRole.ADMIN:
        raise AuthorizationError("Administrative privileges required.")
    return current_user
