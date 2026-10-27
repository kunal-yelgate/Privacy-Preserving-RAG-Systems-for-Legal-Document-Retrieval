import sqlite3

import numpy as np
import pytest

from app.auth.policy import PolicyStore
from app.retrieval.store import LocalIndex
from app.security.context import PolicyChangedError, build_authorized_context
from app.security.filter import Chunk, filter_authorized


def make_policy() -> PolicyStore:
    store = PolicyStore(sqlite3.connect(":memory:"))
    store.initialize()
    store.add_user("u1", "Alice")
    store.add_user("u2", "Bob")
    store.add_matter("m1", "u1")
    store.add_matter("m2", "u2")
    return store


def test_public_and_authorized_private_chunks_pass() -> None:
    store = make_policy()
    snapshot = store.snapshot("u1")
    chunks = [
        Chunk("public", "d1", "law", "public", None),
        Chunk("private", "d2", "secret", "private", "m1"),
        Chunk("denied", "d3", "other", "private", "m2"),
    ]
    assert [chunk.chunk_id for chunk in filter_authorized(chunks, snapshot)] == [
        "public",
        "private",
    ]


def test_malformed_metadata_is_denied() -> None:
    store = make_policy()
    snapshot = store.snapshot("u1")
    assert filter_authorized([Chunk("bad", "d", "x", "private", None)], snapshot) == []


def test_context_rejects_denied_candidates() -> None:
    store = make_policy()
    snapshot = store.snapshot("u1")
    with pytest.raises(PermissionError):
        build_authorized_context([Chunk("denied", "d", "secret", "private", "m2")], snapshot, store)


def test_context_rejects_revoked_access() -> None:
    store = make_policy()
    snapshot = store.snapshot("u1")
    store.remove_member("u1", "m1")
    with pytest.raises(PolicyChangedError):
        build_authorized_context([], snapshot, store)


def test_index_query_filters_private_matters_inside_query() -> None:
    store = make_policy()
    index = LocalIndex(sqlite3.connect(":memory:"), 3)
    index.add(Chunk("m1", "d1", "alpha", "private", "m1"), np.array([1.0, 0.0, 0.0]))
    index.add(Chunk("m2", "d2", "alpha", "private", "m2"), np.array([1.0, 0.0, 0.0]))
    results = index.search(np.array([1.0, 0.0, 0.0]), store.snapshot("u1").matter_ids, 10)
    assert [chunk.chunk_id for chunk in results] == ["m1"]


def test_lexical_query_filters_unauthorized_matter() -> None:
    store = make_policy()
    index = LocalIndex(sqlite3.connect(":memory:"), 3)
    index.add(Chunk("m1", "d1", "specific section alpha", "private", "m1"), np.ones(3))
    index.add(Chunk("m2", "d2", "specific section alpha", "private", "m2"), np.ones(3))
    results = index.search_lexical("section alpha", store.snapshot("u1").matter_ids, 10)
    assert [chunk.chunk_id for chunk, _ in results] == ["m1"]


def test_hybrid_search_is_reproducible() -> None:
    store = make_policy()
    first = LocalIndex(sqlite3.connect(":memory:"), 3)
    second = LocalIndex(sqlite3.connect(":memory:"), 3)
    chunks = [
        Chunk("a", "d1", "contract termination notice", "private", "m1"),
        Chunk("b", "d2", "unrelated property evidence", "private", "m1"),
    ]
    vectors = [np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0])]
    for index in (first, second):
        for chunk, vector in zip(chunks, vectors, strict=True):
            index.add(chunk, vector)
    query = np.array([1.0, 0.0, 0.0])
    first_ids = [
        chunk.chunk_id
        for chunk in first.search_hybrid(
            "contract termination", query, store.snapshot("u1").matter_ids, 2
        )
    ]
    second_ids = [
        chunk.chunk_id
        for chunk in second.search_hybrid(
            "contract termination", query, store.snapshot("u1").matter_ids, 2
        )
    ]
    assert first_ids == second_ids == ["a", "b"]
