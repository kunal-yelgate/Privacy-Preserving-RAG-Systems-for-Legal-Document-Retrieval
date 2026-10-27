from collections.abc import Iterable
from dataclasses import dataclass

from app.auth.policy import PermissionSnapshot


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_id: str
    text: str
    tier: str
    matter_id: str | None
    court: str | None = None
    date: str | None = None
    paragraph: int | None = None
    status: str = "active"


def is_valid_metadata(chunk: Chunk) -> bool:
    if not chunk.chunk_id or not chunk.document_id or chunk.status != "active":
        return False
    if chunk.tier == "public":
        return chunk.matter_id is None
    return chunk.tier == "private" and bool(chunk.matter_id)


def is_authorized(chunk: Chunk, snapshot: PermissionSnapshot) -> bool:
    if not is_valid_metadata(chunk):
        return False
    if chunk.tier == "public":
        return True
    return chunk.matter_id in snapshot.matter_ids


def filter_authorized(chunks: Iterable[Chunk], snapshot: PermissionSnapshot) -> list[Chunk]:
    return [chunk for chunk in chunks if is_authorized(chunk, snapshot)]
