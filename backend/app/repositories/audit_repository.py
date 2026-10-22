import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from backend.app.infrastructure.database.connection import db_manager
from backend.app.schemas.security import AuditEventResponse


class AuditRepository:
    """Stores security and privacy audit trails in SQLite."""

    def record_event(
        self,
        event_type: str,
        outcome: str,
        user_id: Optional[str] = None,
        matter_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEventResponse:
        event_id = f"aud_{uuid.uuid4().hex[:12]}"
        now_dt = datetime.now(timezone.utc)
        now_str = now_dt.isoformat()
        details_json = json.dumps(details) if details else None

        with db_manager.session() as conn:
            conn.execute(
                """
                INSERT INTO security_audit_events (event_id, user_id, event_type, matter_id, resource_id, outcome, details_json, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (event_id, user_id, event_type, matter_id, resource_id, outcome, details_json, now_str),
            )

        return AuditEventResponse(
            event_id=event_id,
            user_id=user_id,
            event_type=event_type,
            matter_id=matter_id,
            resource_id=resource_id,
            outcome=outcome,
            details_json=details_json,
            timestamp=now_dt,
        )

    def list_recent(self, limit: int = 50) -> List[AuditEventResponse]:
        with db_manager.session() as conn:
            rows = conn.execute(
                "SELECT * FROM security_audit_events ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [
                AuditEventResponse(
                    event_id=r["event_id"],
                    user_id=r["user_id"],
                    event_type=r["event_type"],
                    matter_id=r["matter_id"],
                    resource_id=r["resource_id"],
                    outcome=r["outcome"],
                    details_json=r["details_json"],
                    timestamp=r["timestamp"] if isinstance(r["timestamp"], datetime) else datetime.fromisoformat(str(r["timestamp"])),
                )
                for r in rows
            ]

    def count_unauthorized_attempts(self) -> int:
        with db_manager.session() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM security_audit_events WHERE outcome = 'DENIED'"
            ).fetchone()
            return row["cnt"] if row else 0
