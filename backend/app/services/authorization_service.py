"""
Authorization service enforcing matter-level boundaries and least privilege.
Guarantees that no user can access documents or search indices outside authorized matters.
"""
from typing import List, Optional
import jwt
from datetime import datetime, timedelta, timezone

from backend.app.core.config import settings
from backend.app.core.exceptions import AuthenticationError, AuthorizationError
from backend.app.core.logging import logger
from backend.app.domain.enums import UserRole
from backend.app.repositories.audit_repository import AuditRepository
from backend.app.repositories.user_repository import UserRepository
from backend.app.schemas.user import UserResponse


class AuthorizationService:
    """Enforces authentication and server-side matter permissions."""

    def __init__(self, user_repo: UserRepository, audit_repo: AuditRepository):
        self.user_repo = user_repo
        self.audit_repo = audit_repo

    def create_access_token(self, user_id: str, username: str, role: UserRole) -> str:
        """Generates a signed JWT access token."""
        expires = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": user_id,
            "username": username,
            "role": role.value,
            "exp": expires,
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    def verify_token(self, token: str) -> UserResponse:
        """Decodes and validates JWT token, returning the authenticated User entity."""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationError("Invalid token: subject missing.")
        except jwt.PyJWTError as e:
            logger.warning(f"Failed JWT verification: {e}")
            raise AuthenticationError("Session token expired or invalid.")

        user = self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User account not found or disabled.")

        return user

    def authorize_matter_access(
        self,
        user: UserResponse,
        matter_id: str,
        action: str = "read",
    ) -> None:
        """
        Authorizes access to a matter.
        Raises AuthorizationError if the user is not an Admin or not a member of the matter.
        """
        has_access = self.user_repo.check_matter_access(user.user_id, matter_id)
        outcome = "ALLOWED" if has_access else "DENIED"

        self.audit_repo.record_event(
            event_type=f"MATTER_{action.upper()}",
            outcome=outcome,
            user_id=user.user_id,
            matter_id=matter_id,
            details={"action": action, "user_role": user.role.value},
        )

        if not has_access:
            logger.warning(f"Unauthorized access attempt by user {user.username} to matter {matter_id}")
            raise AuthorizationError(f"Access denied: You do not have permission to access matter '{matter_id}'.")

    def get_authorized_matter_ids(self, user: UserResponse) -> List[str]:
        """Returns the list of matter IDs that the user is authorized to access."""
        return self.user_repo.get_user_matter_ids(user.user_id)
