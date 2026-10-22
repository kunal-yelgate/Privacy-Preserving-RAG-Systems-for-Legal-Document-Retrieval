"""
Matter repository handling legal matter records and permissions.
"""
from datetime import datetime, timezone
from typing import List, Optional
from backend.app.domain.enums import MatterStatus
from backend.app.infrastructure.database.connection import db_manager
from backend.app.schemas.matter import MatterCreate, MatterResponse, MatterUpdate


class MatterRepository:
    """Persistence repository for Legal Matters."""

    def create(self, matter_data: MatterCreate) -> MatterResponse:
        now_dt = datetime.now(timezone.utc)
        now_str = now_dt.isoformat()
        with db_manager.session() as conn:
            conn.execute(
                """
                INSERT INTO matters (matter_id, name, description, client_name, lead_counsel, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
                """,
                (
                    matter_data.matter_id,
                    matter_data.name,
                    matter_data.description,
                    matter_data.client_name,
                    matter_data.lead_counsel,
                    now_str,
                    now_str,
                ),
            )
        return self.get_by_id(matter_data.matter_id)

    def get_by_id(self, matter_id: str) -> Optional[MatterResponse]:
        with db_manager.session() as conn:
            row = conn.execute(
                """
                SELECT m.*, COUNT(d.document_id) as document_count
                FROM matters m
                LEFT JOIN documents d ON m.matter_id = d.matter_id
                WHERE m.matter_id = ?
                GROUP BY m.matter_id
                """,
                (matter_id,),
            ).fetchone()
            if not row:
                return None
            return MatterResponse(
                matter_id=row["matter_id"],
                name=row["name"],
                description=row["description"],
                client_name=row["client_name"],
                lead_counsel=row["lead_counsel"],
                status=MatterStatus(row["status"]),
                created_at=row["created_at"] if isinstance(row["created_at"], datetime) else datetime.fromisoformat(str(row["created_at"])),
                updated_at=row["updated_at"] if isinstance(row["updated_at"], datetime) else datetime.fromisoformat(str(row["updated_at"])),
                document_count=row["document_count"],
            )

    def list_accessible(self, allowed_matter_ids: Optional[List[str]] = None) -> List[MatterResponse]:
        with db_manager.session() as conn:
            if allowed_matter_ids is None:
                # All matters
                rows = conn.execute(
                    """
                    SELECT m.*, COUNT(d.document_id) as document_count
                    FROM matters m
                    LEFT JOIN documents d ON m.matter_id = d.matter_id
                    GROUP BY m.matter_id
                    ORDER BY m.created_at DESC
                    """
                ).fetchall()
            else:
                if not allowed_matter_ids:
                    return []
                placeholders = ",".join("?" for _ in allowed_matter_ids)
                rows = conn.execute(
                    f"""
                    SELECT m.*, COUNT(d.document_id) as document_count
                    FROM matters m
                    LEFT JOIN documents d ON m.matter_id = d.matter_id
                    WHERE m.matter_id IN ({placeholders})
                    GROUP BY m.matter_id
                    ORDER BY m.created_at DESC
                    """,
                    allowed_matter_ids,
                ).fetchall()

            return [
                MatterResponse(
                    matter_id=r["matter_id"],
                    name=r["name"],
                    description=r["description"],
                    client_name=r["client_name"],
                    lead_counsel=r["lead_counsel"],
                    status=MatterStatus(r["status"]),
                    created_at=r["created_at"] if isinstance(r["created_at"], datetime) else datetime.fromisoformat(str(r["created_at"])),
                    updated_at=r["updated_at"] if isinstance(r["updated_at"], datetime) else datetime.fromisoformat(str(r["updated_at"])),
                    document_count=r["document_count"],
                )
                for r in rows
            ]

    def update(self, matter_id: str, update_data: MatterUpdate) -> Optional[MatterResponse]:
        updates = []
        params = []
        if update_data.name is not None:
            updates.append("name = ?")
            params.append(update_data.name)
        if update_data.description is not None:
            updates.append("description = ?")
            params.append(update_data.description)
        if update_data.client_name is not None:
            updates.append("client_name = ?")
            params.append(update_data.client_name)
        if update_data.lead_counsel is not None:
            updates.append("lead_counsel = ?")
            params.append(update_data.lead_counsel)
        if update_data.status is not None:
            updates.append("status = ?")
            params.append(update_data.status.value)

        if not updates:
            return self.get_by_id(matter_id)

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(matter_id)

        with db_manager.session() as conn:
            conn.execute(
                f"UPDATE matters SET {', '.join(updates)} WHERE matter_id = ?",
                params,
            )
        return self.get_by_id(matter_id)

    def delete(self, matter_id: str) -> bool:
        with db_manager.session() as conn:
            cursor = conn.execute("DELETE FROM matters WHERE matter_id = ?", (matter_id,))
            return cursor.rowcount > 0
