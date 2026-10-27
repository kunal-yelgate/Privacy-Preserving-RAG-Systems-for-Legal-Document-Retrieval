from app.auth.policy import PermissionSnapshot, PolicyStore
from app.security.filter import Chunk, filter_authorized


class PolicyChangedError(RuntimeError):
    """Raised when permissions change between retrieval and prompt construction."""


def build_authorized_context(
    chunks: list[Chunk],
    snapshot: PermissionSnapshot,
    policy_store: PolicyStore,
) -> list[Chunk]:
    if policy_store.current_version() != snapshot.policy_version:
        raise PolicyChangedError("authorization changed during request")
    authorized = filter_authorized(chunks, snapshot)
    if len(authorized) != len(chunks):
        raise PermissionError("retrieval returned unauthorized content")
    return authorized
