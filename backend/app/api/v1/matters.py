"""
Matter management API routes.
Enforces matter-level access control on all endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, status

from backend.app.core.dependencies import (
    get_auth_service,
    get_current_user,
    get_matter_repo,
    get_user_repo,
)
from backend.app.core.exceptions import NotFoundError
from backend.app.domain.enums import UserRole
from backend.app.repositories.matter_repository import MatterRepository
from backend.app.repositories.user_repository import UserRepository
from backend.app.schemas.matter import (
    MatterCreate,
    MatterMembershipCreate,
    MatterResponse,
    MatterUpdate,
)
from backend.app.schemas.user import UserResponse
from backend.app.services.authorization_service import AuthorizationService

router = APIRouter(prefix="/matters", tags=["Matters"])


@router.get("", response_model=List[MatterResponse])
async def list_matters(
    current_user: UserResponse = Depends(get_current_user),
    matter_repo: MatterRepository = Depends(get_matter_repo),
    auth_service: AuthorizationService = Depends(get_auth_service),
):
    """Returns matters accessible to the current user."""
    if current_user.role == UserRole.ADMIN:
        return matter_repo.list_accessible(None)

    allowed_ids = auth_service.get_authorized_matter_ids(current_user)
    return matter_repo.list_accessible(allowed_ids)


@router.post("", response_model=MatterResponse, status_code=status.HTTP_201_CREATED)
async def create_matter(
    payload: MatterCreate,
    current_user: UserResponse = Depends(get_current_user),
    matter_repo: MatterRepository = Depends(get_matter_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Creates a new legal matter and grants the creator researcher membership."""
    existing = matter_repo.get_by_id(payload.matter_id)
    if existing:
        return existing

    created = matter_repo.create(payload)
    # Grant access to the creating user
    user_repo.grant_matter_access(current_user.user_id, payload.matter_id, role=current_user.role)
    return created


@router.get("/{matter_id}", response_model=MatterResponse)
async def get_matter(
    matter_id: str,
    current_user: UserResponse = Depends(get_current_user),
    matter_repo: MatterRepository = Depends(get_matter_repo),
    auth_service: AuthorizationService = Depends(get_auth_service),
):
    """Retrieves matter metadata if the user has access."""
    auth_service.authorize_matter_access(current_user, matter_id, action="read")
    matter = matter_repo.get_by_id(matter_id)
    if not matter:
        raise NotFoundError(f"Matter '{matter_id}' not found.")
    return matter


@router.patch("/{matter_id}", response_model=MatterResponse)
async def update_matter(
    matter_id: str,
    payload: MatterUpdate,
    current_user: UserResponse = Depends(get_current_user),
    matter_repo: MatterRepository = Depends(get_matter_repo),
    auth_service: AuthorizationService = Depends(get_auth_service),
):
    """Updates matter metadata."""
    auth_service.authorize_matter_access(current_user, matter_id, action="write")
    updated = matter_repo.update(matter_id, payload)
    if not updated:
        raise NotFoundError(f"Matter '{matter_id}' not found.")
    return updated


@router.delete("/{matter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_matter(
    matter_id: str,
    current_user: UserResponse = Depends(get_current_user),
    matter_repo: MatterRepository = Depends(get_matter_repo),
    auth_service: AuthorizationService = Depends(get_auth_service),
):
    """Deletes a legal matter and all associated documents."""
    auth_service.authorize_matter_access(current_user, matter_id, action="delete")
    success = matter_repo.delete(matter_id)
    if not success:
        raise NotFoundError(f"Matter '{matter_id}' not found.")


@router.post("/{matter_id}/members", status_code=status.HTTP_200_OK)
async def add_matter_member(
    matter_id: str,
    payload: MatterMembershipCreate,
    current_user: UserResponse = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo),
    auth_service: AuthorizationService = Depends(get_auth_service),
):
    """Grants a user access to the specified matter."""
    auth_service.authorize_matter_access(current_user, matter_id, action="admin")
    target_user = user_repo.get_by_id(payload.user_id)
    if not target_user:
        raise NotFoundError("Target user not found.")

    user_repo.grant_matter_access(payload.user_id, matter_id, role=payload.role)
    return {"status": "success", "message": f"Granted {payload.role.value} access to user {target_user.username}."}
