import json
import logging
import sqlite3
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.auth.policy import PolicyStore
from app.config import get_settings
from app.generation.answer import validate_generated_answer
from app.generation.ollama import LocalGenerationError, OllamaClient
from app.generation.prompt import build_evidence_prompt
from app.ingest.models import DocumentMetadata
from app.ingest.service import IngestionService
from app.retrieval.embeddings import LocalHashEmbedder
from app.retrieval.store import LocalIndex
from app.safe_logging import configure_logging, safe_event
from app.security.context import PolicyChangedError, build_authorized_context
from app.security.filter import Chunk

settings = get_settings()
configure_logging()
Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
connection = sqlite3.connect(settings.database_path, check_same_thread=False)
policy = PolicyStore(connection)
policy.initialize()
index = LocalIndex(connection, settings.embedding_dimensions)
embedder = LocalHashEmbedder(settings.embedding_dimensions)
ingestion = IngestionService(connection, index, embedder)
generator = OllamaClient(
    settings.ollama_base_url, settings.ollama_model, settings.ollama_timeout_seconds
)

app = FastAPI(title="Privacy-Preserving Legal RAG", version="0.1.0")
logger = logging.getLogger("legal_rag")


class QueryScope(BaseModel):
    public: bool = True
    matter_ids: list[str] = Field(default_factory=list)


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    scope: QueryScope = Field(default_factory=QueryScope)
    stream: bool = False


class MemberRequest(BaseModel):
    user_id: str = Field(min_length=1)
    role: str = Field(default="member", pattern="^(member|admin)$")


class MatterRequest(BaseModel):
    matter_id: str = Field(min_length=1, max_length=128)


def require_user(user_id: str | None, request_id: str) -> str:
    if not user_id or not policy.user_exists(user_id):
        raise HTTPException(
            status_code=401, detail={"request_id": request_id, "error": "unauthorized"}
        )
    return user_id


def require_matter_manager(user_id: str, matter_id: str, request_id: str) -> None:
    if not policy.matter_exists(matter_id) or not policy.can_manage_matter(user_id, matter_id):
        raise HTTPException(
            status_code=403, detail={"request_id": request_id, "error": "forbidden"}
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/query")
def query(request: QueryRequest, x_user_id: str | None = Header(default=None)) -> dict:
    request_id = str(uuid.uuid4())
    user_id = require_user(x_user_id, request_id)
    snapshot = policy.snapshot(user_id)
    requested = frozenset(request.scope.matter_ids)
    allowed_scope = requested & snapshot.matter_ids
    if requested - snapshot.matter_ids:
        safe_event(logger, "scope_denied", request_id=request_id, user_id=user_id)
    search_scope = allowed_scope if request.scope.matter_ids else snapshot.matter_ids
    evidence = index.search_hybrid(
        request.question,
        embedder.embed(request.question),
        search_scope,
        settings.retrieval_top_k,
        alpha=settings.hybrid_alpha,
        include_public=request.scope.public,
    )
    try:
        authorized = build_authorized_context(evidence, snapshot, policy)
    except PolicyChangedError:
        safe_event(logger, "policy_changed", request_id=request_id)
        return {
            "request_id": request_id,
            "error": "Your access changed. Please run the query again.",
        }
    prompt = build_evidence_prompt(request.question, authorized)
    if not authorized:
        return {
            "request_id": request_id,
            "abstained": True,
            "answer": None,
            "citations": [],
            "evidence": [],
        }
    if request.stream:
        return _stream_answer(request_id, prompt, authorized)
    try:
        generated = generator.generate(prompt)
    except LocalGenerationError:
        safe_event(logger, "generation_failed", request_id=request_id)
        raise HTTPException(
            status_code=503,
            detail={"request_id": request_id, "error": "local_generation_unavailable"},
        )
    validated = validate_generated_answer(generated, authorized)
    return {
        "request_id": request_id,
        "abstained": validated.abstained,
        "answer": validated.text if not validated.abstained else None,
        "citations": [citation.__dict__ for citation in validated.citations],
        "evidence": [
            {
                "chunk_id": chunk.chunk_id,
                "tier": chunk.tier,
                "matter_id": chunk.matter_id,
                "court": chunk.court,
                "date": chunk.date,
                "paragraph": chunk.paragraph,
            }
            for chunk in authorized
        ],
        "prompt": prompt,
    }


def _stream_answer(request_id: str, prompt: str, evidence: list[Chunk]) -> StreamingResponse:
    def tokens():
        try:
            yield json.dumps({"request_id": request_id}) + "\n"
            yield from generator.generate_stream(prompt)
        except LocalGenerationError:
            safe_event(logger, "generation_failed", request_id=request_id)
            yield json.dumps({"error": "local_generation_unavailable"}) + "\n"

    return StreamingResponse(tokens(), media_type="application/x-ndjson")


@app.get("/matters")
def list_matters(x_user_id: str | None = Header(default=None)) -> dict:
    request_id = str(uuid.uuid4())
    user_id = require_user(x_user_id, request_id)
    return {"request_id": request_id, "matters": policy.list_matters(user_id)}


@app.post("/matters", status_code=201)
def create_matter(request: MatterRequest, x_user_id: str | None = Header(default=None)) -> dict:
    request_id = str(uuid.uuid4())
    user_id = require_user(x_user_id, request_id)
    if policy.matter_exists(request.matter_id):
        raise HTTPException(
            status_code=409, detail={"request_id": request_id, "error": "already_exists"}
        )
    policy.create_matter(request.matter_id, user_id)
    return {"request_id": request_id, "matter_id": request.matter_id}


@app.post("/matters/{matter_id}/members", status_code=201)
def add_member(
    matter_id: str,
    request: MemberRequest,
    x_user_id: str | None = Header(default=None),
) -> dict:
    request_id = str(uuid.uuid4())
    user_id = require_user(x_user_id, request_id)
    require_matter_manager(user_id, matter_id, request_id)
    if not policy.user_exists(request.user_id):
        raise HTTPException(
            status_code=404, detail={"request_id": request_id, "error": "not_found"}
        )
    policy.add_member(request.user_id, matter_id, request.role)
    return {"request_id": request_id, "status": "member_added"}


@app.delete("/matters/{matter_id}/members/{member_id}")
def remove_member(
    matter_id: str,
    member_id: str,
    x_user_id: str | None = Header(default=None),
) -> dict:
    request_id = str(uuid.uuid4())
    user_id = require_user(x_user_id, request_id)
    require_matter_manager(user_id, matter_id, request_id)
    if member_id == user_id and policy.membership_role(user_id, matter_id) == "owner":
        raise HTTPException(
            status_code=400, detail={"request_id": request_id, "error": "invalid_operation"}
        )
    policy.remove_member(member_id, matter_id)
    return {"request_id": request_id, "status": "member_removed"}


@app.post("/matters/{matter_id}/documents")
async def upload_document(
    matter_id: str,
    file: UploadFile,
    x_user_id: str | None = Header(default=None),
) -> dict:
    request_id = str(uuid.uuid4())
    user_id = require_user(x_user_id, request_id)
    if not policy.matter_exists(matter_id) or not policy.can_access(
        policy.snapshot(user_id), matter_id
    ):
        raise HTTPException(
            status_code=403, detail={"request_id": request_id, "error": "forbidden"}
        )
    suffix = Path(file.filename or "").suffix.lower()
    media_types = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    if suffix not in media_types:
        raise HTTPException(
            status_code=415, detail={"request_id": request_id, "error": "unsupported_file_type"}
        )
    document_id = str(uuid.uuid4())
    metadata = DocumentMetadata(
        document_id, matter_id, Path(file.filename or "").name, media_types[suffix]
    )
    with tempfile.TemporaryDirectory() as temporary_directory:
        temporary_path = Path(temporary_directory) / metadata.filename
        temporary_path.write_bytes(await file.read())
        status = ingestion.ingest(metadata, temporary_path)
    return {"request_id": request_id, "document_id": document_id, "status": status}


@app.get("/matters/{matter_id}/documents")
def list_documents(matter_id: str, x_user_id: str | None = Header(default=None)) -> dict:
    request_id = str(uuid.uuid4())
    user_id = require_user(x_user_id, request_id)
    if not policy.matter_exists(matter_id) or not policy.can_access(
        policy.snapshot(user_id), matter_id
    ):
        raise HTTPException(
            status_code=403, detail={"request_id": request_id, "error": "forbidden"}
        )
    return {"request_id": request_id, "documents": ingestion.list_documents(matter_id)}
