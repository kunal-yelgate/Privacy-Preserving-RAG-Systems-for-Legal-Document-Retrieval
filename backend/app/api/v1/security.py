"""
Security and privacy audit API routes.
"""
from typing import List
from fastapi import APIRouter, Depends

from backend.app.core.dependencies import (
    get_admin_user,
    get_audit_repo,
    get_current_user,
    get_security_service,
)
from backend.app.repositories.audit_repository import AuditRepository
from backend.app.schemas.security import AuditEventResponse, SecurityStatusResponse
from backend.app.schemas.user import UserResponse
from backend.app.services.security_service import SecurityService

router = APIRouter(prefix="/security", tags=["Security"])


@router.get("/status", response_model=SecurityStatusResponse)
async def get_security_status(
    current_user: UserResponse = Depends(get_current_user),
    security_service: SecurityService = Depends(get_security_service),
):
    """Audits current offline configuration, model readiness, and quarantine count."""
    return await security_service.get_security_status()


@router.get("/audit", response_model=List[AuditEventResponse])
async def list_audit_events(
    limit: int = 50,
    current_user: UserResponse = Depends(get_admin_user),
    audit_repo: AuditRepository = Depends(get_audit_repo),
):
    """Retrieves recent security and access audit events (Admin only)."""
    return audit_repo.list_recent(limit=limit)
