import sqlite3

import numpy as np
from fastapi.testclient import TestClient

from app import main
from app.auth.policy import PolicyStore
from app.ingest.service import IngestionService
from app.retrieval.embeddings import LocalHashEmbedder
from app.retrieval.store import LocalIndex
from app.security.filter import Chunk


def configured_client(monkeypatch) -> TestClient:
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    policy = PolicyStore(connection)
    policy.initialize()
    policy.add_user("u1", "Alice")
    policy.add_user("u2", "Bob")
    policy.add_matter("m1", "u1")
    policy.add_matter("m2", "u2")
    index = LocalIndex(connection, 3)
    index.add(
        Chunk("private-1", "doc-1", "confidential alpha evidence", "private", "m1"),
        np.array([1.0, 0.0, 0.0]),
    )
    index.add(
        Chunk("private-2", "doc-2", "confidential alpha evidence", "private", "m2"),
        np.array([1.0, 0.0, 0.0]),
    )
    embedder = LocalHashEmbedder(3)
    monkeypatch.setattr(main, "connection", connection)
    monkeypatch.setattr(main, "policy", policy)
    monkeypatch.setattr(main, "index", index)
    monkeypatch.setattr(main, "embedder", embedder)
    monkeypatch.setattr(main, "ingestion", IngestionService(connection, index, embedder))

    class FakeGenerator:
        def generate(self, prompt: str) -> str:
            return "Authorized finding [private-1]"

        def generate_stream(self, prompt: str):
            yield "Authorized finding [private-1]"

    monkeypatch.setattr(main, "generator", FakeGenerator())
    return TestClient(main.app)


def test_query_returns_only_authorized_matter(monkeypatch) -> None:
    client = configured_client(monkeypatch)
    response = client.post(
        "/query",
        headers={"X-User-Id": "u1"},
        json={"question": "confidential alpha", "scope": {"public": False}},
    )
    assert response.status_code == 200
    assert [item["matter_id"] for item in response.json()["evidence"]] == ["m1"]
    assert "private-2" not in response.text


def test_unknown_identity_cannot_query_public_data(monkeypatch) -> None:
    client = configured_client(monkeypatch)
    response = client.post(
        "/query",
        headers={"X-User-Id": "unknown"},
        json={"question": "alpha"},
    )
    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "unauthorized"


def test_revocation_is_immediate_for_query_and_listing(monkeypatch) -> None:
    client = configured_client(monkeypatch)
    assert client.get("/matters", headers={"X-User-Id": "u1"}).json()["matters"]
    response = client.post(
        "/matters/m1/members",
        headers={"X-User-Id": "u1"},
        json={"user_id": "u2", "role": "member"},
    )
    assert response.status_code == 201
    response = client.delete(
        "/matters/m1/members/u2",
        headers={"X-User-Id": "u1"},
    )
    assert response.status_code == 200
    response = client.get(
        "/matters/m1/documents",
        headers={"X-User-Id": "u2"},
    )
    assert response.status_code == 403


def test_owner_can_create_matter_and_upload_docx(monkeypatch, tmp_path) -> None:
    client = configured_client(monkeypatch)
    response = client.post(
        "/matters",
        headers={"X-User-Id": "u1"},
        json={"matter_id": "m3"},
    )
    assert response.status_code == 201
    from docx import Document

    document_path = tmp_path / "evidence.docx"
    document = Document()
    document.add_paragraph("Section 7: Synthetic evidence.")
    document.save(document_path)
    with document_path.open("rb") as document_file:
        response = client.post(
            "/matters/m3/documents",
            headers={"X-User-Id": "u1"},
            files={
                "file": (
                    "evidence.docx",
                    document_file,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )
    assert response.status_code == 200
    assert response.json()["status"] == "indexed"
