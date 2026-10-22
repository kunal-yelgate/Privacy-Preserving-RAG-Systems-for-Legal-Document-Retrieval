"""
Centralized exception hierarchy for Legal RAG system.
Guarantees consistent error codes and prevents leaking sensitive information.
"""
from typing import Any, Dict, Optional


class LegalRAGException(Exception):
    """Base exception for all domain and operational errors."""
    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}


class InvalidRequestError(LegalRAGException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="INVALID_REQUEST", status_code=400, details=details)


class AuthenticationError(LegalRAGException):
    def __init__(self, message: str = "Authentication required or credentials invalid."):
        super().__init__(message, error_code="UNAUTHENTICATED", status_code=401)


class AuthorizationError(LegalRAGException):
    def __init__(self, message: str = "Access denied: insufficient matter permissions."):
        super().__init__(message, error_code="FORBIDDEN", status_code=403)


class NotFoundError(LegalRAGException):
    def __init__(self, message: str = "Requested resource not found."):
        super().__init__(message, error_code="NOT_FOUND", status_code=404)


class UnsupportedDocumentError(LegalRAGException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="UNSUPPORTED_DOCUMENT", status_code=415, details=details)


class DocumentExtractionError(LegalRAGException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="EXTRACTION_FAILED", status_code=422, details=details)


class EmbeddingServiceError(LegalRAGException):
    def __init__(self, message: str = "Local embedding service unavailable."):
        super().__init__(message, error_code="EMBEDDING_UNAVAILABLE", status_code=503)


class LocalModelUnavailableError(LegalRAGException):
    def __init__(self, message: str = "Local inference model is unavailable."):
        super().__init__(message, error_code="MODEL_UNAVAILABLE", status_code=503)


class VectorStoreError(LegalRAGException):
    def __init__(self, message: str = "Local vector store operation failed."):
        super().__init__(message, error_code="VECTOR_STORE_ERROR", status_code=500)


class CitationValidationError(LegalRAGException):
    def __init__(self, message: str = "Citation could not be verified against authorized evidence."):
        super().__init__(message, error_code="CITATION_VALIDATION_FAILED", status_code=422)


class PromptInjectionDetectedError(LegalRAGException):
    def __init__(self, message: str = "Input contains potential adversarial or injection pattern."):
        super().__init__(message, error_code="PROMPT_INJECTION_DETECTED", status_code=400)
