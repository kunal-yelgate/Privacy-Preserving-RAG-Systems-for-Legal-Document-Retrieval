"""
Chat session and message repository for conversation history persistence.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from backend.app.infrastructure.database.connection import db_manager
from backend.app.schemas.chat import ChatMessageSchema, ChatSessionSchema


class ChatRepository:
    """Manages chat sessions and evidence-grounded messages."""

    def create_session(self, matter_id: str, user_id: str, title: str) -> ChatSessionSchema:
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        with db_manager.session() as conn:
            conn.execute(
                """
                INSERT INTO chat_sessions (session_id, matter_id, user_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, matter_id, user_id, title, now, now),
            )
        return self.get_session(session_id)

    def get_session(self, session_id: str) -> Optional[ChatSessionSchema]:
        with db_manager.session() as conn:
            row = conn.execute("SELECT * FROM chat_sessions WHERE session_id = ?", (session_id,)).fetchone()
            if not row:
                return None
            return ChatSessionSchema(
                session_id=row["session_id"],
                matter_id=row["matter_id"],
                user_id=row["user_id"],
                title=row["title"],
                created_at=row["created_at"] if isinstance(row["created_at"], datetime) else datetime.fromisoformat(str(row["created_at"])),
                updated_at=row["updated_at"] if isinstance(row["updated_at"], datetime) else datetime.fromisoformat(str(row["updated_at"])),
            )

    def list_sessions(self, user_id: str, matter_id: Optional[str] = None) -> List[ChatSessionSchema]:
        with db_manager.session() as conn:
            if matter_id:
                rows = conn.execute(
                    "SELECT * FROM chat_sessions WHERE user_id = ? AND matter_id = ? ORDER BY updated_at DESC",
                    (user_id, matter_id),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC",
                    (user_id,),
                ).fetchall()

            return [
                ChatSessionSchema(
                    session_id=r["session_id"],
                    matter_id=r["matter_id"],
                    user_id=r["user_id"],
                    title=r["title"],
                    created_at=r["created_at"] if isinstance(r["created_at"], datetime) else datetime.fromisoformat(str(r["created_at"])),
                    updated_at=r["updated_at"] if isinstance(r["updated_at"], datetime) else datetime.fromisoformat(str(r["updated_at"])),
                )
                for r in rows
            ]

    def add_message(
        self,
        session_id: str,
        sender: str,
        content: str,
        citations_json: Optional[str] = None,
    ) -> ChatMessageSchema:
        message_id = f"msg_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        with db_manager.session() as conn:
            conn.execute(
                """
                INSERT INTO chat_messages (message_id, session_id, sender, content, citations_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (message_id, session_id, sender, content, citations_json, now),
            )
            conn.execute(
                "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
                (session_id,),
            )
        return ChatMessageSchema(
            message_id=message_id,
            session_id=session_id,
            sender=sender,
            content=content,
            citations_json=citations_json,
            created_at=now,
        )

    def get_messages(self, session_id: str) -> List[ChatMessageSchema]:
        with db_manager.session() as conn:
            rows = conn.execute(
                "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,),
            ).fetchall()
            return [
                ChatMessageSchema(
                    message_id=r["message_id"],
                    session_id=r["session_id"],
                    sender=r["sender"],
                    content=r["content"],
                    citations_json=r["citations_json"],
                    created_at=r["created_at"] if isinstance(r["created_at"], datetime) else datetime.fromisoformat(str(r["created_at"])),
                )
                for r in rows
            ]

    def delete_session(self, session_id: str) -> bool:
        with db_manager.session() as conn:
            cursor = conn.execute("DELETE FROM chat_sessions WHERE session_id = ?", (session_id,))
            return cursor.rowcount > 0
