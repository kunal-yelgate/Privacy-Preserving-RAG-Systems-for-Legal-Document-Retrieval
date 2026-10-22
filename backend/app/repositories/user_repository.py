"""
User and matter-membership repository.
Provides secure password hashing via bcrypt and membership queries.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional
import bcrypt

from backend.app.domain.enums import UserRole
from backend.app.infrastructure.database.connection import db_manager
from backend.app.schemas.user import UserResponse


class UserRepository:
    """Manages users, password verification, and matter permissions."""

    @classmethod
    def hash_password(cls, plain_password: str) -> str:
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            return False

    def create_user(
        self,
        username: str,
        plain_password: str,
        role: UserRole = UserRole.RESEARCHER,
        full_name: Optional[str] = None,
    ) -> UserResponse:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        hashed = self.hash_password(plain_password)
        now_dt = datetime.now(timezone.utc)
        now_str = now_dt.isoformat()

        with db_manager.session() as conn:
            conn.execute(
                """
                INSERT INTO users (user_id, username, hashed_password, role, full_name, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
                """,
                (user_id, username, hashed, role.value, full_name, now_str),
            )

        return UserResponse(
            user_id=user_id,
            username=username,
            role=role,
            full_name=full_name,
            created_at=now_dt,
            is_active=True,
        )

    def get_by_username(self, username: str) -> Optional[dict]:
        with db_manager.session() as conn:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            if row:
                return dict(row)
        return None

    def get_by_id(self, user_id: str) -> Optional[UserResponse]:
        with db_manager.session() as conn:
            row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if row:
                return UserResponse(
                    user_id=row["user_id"],
                    username=row["username"],
                    role=UserRole(row["role"]),
                    full_name=row["full_name"],
                    created_at=row["created_at"] if isinstance(row["created_at"], datetime) else datetime.fromisoformat(str(row["created_at"])),
                    is_active=bool(row["is_active"]),
                )
        return None

    def grant_matter_access(self, user_id: str, matter_id: str, role: UserRole = UserRole.RESEARCHER) -> None:
        with db_manager.session() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO matter_memberships (user_id, matter_id, role, granted_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (user_id, matter_id, role.value),
            )

    def check_matter_access(self, user_id: str, matter_id: str) -> bool:
        """Checks if a user is an admin or has explicit membership for a matter."""
        user = self.get_by_id(user_id)
        if not user:
            return False
        if user.role == UserRole.ADMIN:
            return True

        with db_manager.session() as conn:
            row = conn.execute(
                "SELECT 1 FROM matter_memberships WHERE user_id = ? AND matter_id = ?",
                (user_id, matter_id),
            ).fetchone()
            return row is not None

    def get_user_matter_ids(self, user_id: str) -> List[str]:
        user = self.get_by_id(user_id)
        if not user:
            return []
        with db_manager.session() as conn:
            if user.role == UserRole.ADMIN:
                rows = conn.execute("SELECT matter_id FROM matters").fetchall()
            else:
                rows = conn.execute(
                    "SELECT matter_id FROM matter_memberships WHERE user_id = ?",
                    (user_id,),
                ).fetchall()
            return [r["matter_id"] for r in rows]
