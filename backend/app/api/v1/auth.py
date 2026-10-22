"""
Authentication API routes.
Issues JWT tokens and validates current user session.
"""
from fastapi import APIRouter, Depends
from backend.app.core.dependencies import get_auth_service, get_current_user, get_user_repo
from backend.app.core.exceptions import AuthenticationError
from backend.app.domain.enums import UserRole
from backend.app.repositories.user_repository import UserRepository
from backend.app.schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse
from backend.app.services.authorization_service import AuthorizationService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLogin,
    user_repo: UserRepository = Depends(get_user_repo),
    auth_service: AuthorizationService = Depends(get_auth_service),
):
    user_row = user_repo.get_by_username(payload.username)
    if not user_row or not user_repo.verify_password(payload.password, user_row["hashed_password"]):
        raise AuthenticationError("Invalid username or password.")

    user = user_repo.get_by_id(user_row["user_id"])
    token = auth_service.create_access_token(user.user_id, user.username, user.role)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.user_id,
        username=user.username,
        role=user.role,
    )


@router.post("/register", response_model=UserResponse)
async def register(
    payload: UserCreate,
    user_repo: UserRepository = Depends(get_user_repo),
):
    if user_repo.get_by_username(payload.username):
        raise AuthenticationError(f"Username '{payload.username}' is already registered.")

    return user_repo.create_user(
        username=payload.username,
        plain_password=payload.password,
        role=payload.role,
        full_name=payload.full_name,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: UserResponse = Depends(get_current_user),
):
    return current_user
