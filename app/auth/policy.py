import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class PermissionSnapshot:
    user_id: str
    policy_version: int
    matter_ids: frozenset[str]


class PolicyStore:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def initialize(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS matters (
                matter_id TEXT PRIMARY KEY,
                owner_id TEXT NOT NULL REFERENCES users(user_id)
            );
            CREATE TABLE IF NOT EXISTS memberships (
                user_id TEXT NOT NULL REFERENCES users(user_id),
                matter_id TEXT NOT NULL REFERENCES matters(matter_id),
                role TEXT NOT NULL,
                PRIMARY KEY (user_id, matter_id)
            );
            CREATE TABLE IF NOT EXISTS policy_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                version INTEGER NOT NULL
            );
            INSERT OR IGNORE INTO policy_state(id, version) VALUES (1, 1);
            """
        )
        self.connection.commit()

    def add_user(self, user_id: str, display_name: str) -> None:
        self.connection.execute(
            "INSERT INTO users(user_id, display_name) VALUES (?, ?)", (user_id, display_name)
        )
        self.connection.commit()

    def user_exists(self, user_id: str) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        return row is not None

    def add_matter(self, matter_id: str, owner_id: str) -> None:
        self.connection.execute(
            "INSERT INTO matters(matter_id, owner_id) VALUES (?, ?)", (matter_id, owner_id)
        )
        self.add_member(owner_id, matter_id, "owner")
        self.connection.commit()

    def create_matter(self, matter_id: str, owner_id: str) -> None:
        if not self.user_exists(owner_id):
            raise ValueError("owner does not exist")
        self.add_matter(matter_id, owner_id)

    def add_member(self, user_id: str, matter_id: str, role: str = "member") -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO memberships(user_id, matter_id, role) VALUES (?, ?, ?)",
            (user_id, matter_id, role),
        )
        self._increment_version()
        self.connection.commit()

    def remove_member(self, user_id: str, matter_id: str) -> None:
        self.connection.execute(
            "DELETE FROM memberships WHERE user_id = ? AND matter_id = ?",
            (user_id, matter_id),
        )
        self._increment_version()
        self.connection.commit()

    def matter_exists(self, matter_id: str) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM matters WHERE matter_id = ?", (matter_id,)
        ).fetchone()
        return row is not None

    def membership_role(self, user_id: str, matter_id: str) -> str | None:
        row = self.connection.execute(
            "SELECT role FROM memberships WHERE user_id = ? AND matter_id = ?",
            (user_id, matter_id),
        ).fetchone()
        return str(row[0]) if row else None

    def can_manage_matter(self, user_id: str, matter_id: str) -> bool:
        return self.membership_role(user_id, matter_id) in {"owner", "admin"}

    def list_matters(self, user_id: str) -> list[dict[str, str]]:
        rows = self.connection.execute(
            """
            SELECT m.matter_id, m.owner_id, ms.role
            FROM matters AS m
            JOIN memberships AS ms ON ms.matter_id = m.matter_id
            WHERE ms.user_id = ?
            ORDER BY m.matter_id
            """,
            (user_id,),
        ).fetchall()
        return [
            {"matter_id": str(matter_id), "owner_id": str(owner_id), "role": str(role)}
            for matter_id, owner_id, role in rows
        ]

    def _increment_version(self) -> None:
        self.connection.execute("UPDATE policy_state SET version = version + 1 WHERE id = 1")

    def current_version(self) -> int:
        row = self.connection.execute("SELECT version FROM policy_state WHERE id = 1").fetchone()
        if row is None:
            raise RuntimeError("policy state is not initialized")
        return int(row[0])

    def snapshot(self, user_id: str) -> PermissionSnapshot:
        rows = self.connection.execute(
            "SELECT matter_id FROM memberships WHERE user_id = ?", (user_id,)
        ).fetchall()
        return PermissionSnapshot(
            user_id=user_id,
            policy_version=self.current_version(),
            matter_ids=frozenset(str(row[0]) for row in rows),
        )

    def can_access(self, snapshot: PermissionSnapshot, matter_id: str | None) -> bool:
        return matter_id is not None and matter_id in snapshot.matter_ids

    def authorized_matter_ids(self, snapshot: PermissionSnapshot) -> frozenset[str]:
        return snapshot.matter_ids
