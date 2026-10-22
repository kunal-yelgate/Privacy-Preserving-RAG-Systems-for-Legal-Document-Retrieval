# API Reference: Privacy-Preserving Offline Legal RAG

All endpoints are versioned under `/api/v1`. Interactive OpenAPI documentation is accessible at `http://127.0.0.1:8000/docs` in development mode.

## 1. Authentication
- `POST /api/v1/auth/login`
  - Body: `{"username": "admin", "password": "..."}`
  - Returns: JWT Bearer access token and user metadata.
- `POST /api/v1/auth/register`
  - Body: `{"username": "...", "password": "...", "role": "researcher"}`
- `GET /api/v1/auth/me`
  - Returns authenticated user details.

## 2. Health & Subsystem Readiness
- `GET /api/v1/health`
  - Liveness probe. Returns `{ "status": "healthy", "offline_mode": true }`.
- `GET /api/v1/health/ready`
  - Readiness probe. Verifies SQLite connection, ChromaDB persistence, local Ollama API, and model availability. Returns HTTP 200 if all ready, or 503 if any subsystem is offline.

## 3. Matters
- `GET /api/v1/matters`
  - Lists matters accessible to the caller.
- `POST /api/v1/matters`
  - Creates a new matter and assigns the creator researcher membership.
- `GET /api/v1/matters/{matter_id}`
  - Retrieves matter metadata with document counts.
- `PATCH /api/v1/matters/{matter_id}`
  - Updates matter description, counsel, or status.
- `DELETE /api/v1/matters/{matter_id}`
  - Deletes a matter and all associated documents.
- `POST /api/v1/matters/{matter_id}/members`
  - Grants user access to a matter.

## 4. Documents
- `POST /api/v1/documents`
  - Multipart form upload (`file`, `matter_id`, optional `title`, `classification`).
  - Executes parsing, chunking, embedding generation, ChromaDB vector indexing, and BM25 indexing.
- `GET /api/v1/documents?matter_id={id}`
  - Lists all documents under the authorized matter.
- `GET /api/v1/documents/{document_id}`
  - Retrieves document metadata, hash, and total chunk counts.
- `DELETE /api/v1/documents/{document_id}`
  - Purges original file, vector chunks, BM25 tokens, and SQLite metadata.
- `GET /api/v1/documents/{document_id}/status`
  - Returns ingestion lifecycle state (`pending`, `parsing`, `chunking`, `indexing`, `completed`, `failed`).

## 5. Search
- `POST /api/v1/search`
  - Body: `{"query": "...", "matter_id": "...", "top_k": 5}`
  - Executes hybrid semantic and BM25 retrieval with Reciprocal Rank Fusion within authorized matter boundaries.

## 6. Research / Chat
- `POST /api/v1/chat`
  - Body: `{"question": "...", "matter_id": "...", "top_k": 4, "session_id": "..."}`
  - Retrieves authorized chunks, generates answer via local Ollama LLM, validates citations, and persists conversation.
- `GET /api/v1/chat/sessions`
  - Lists conversation sessions for the authenticated user.
- `GET /api/v1/chat/sessions/{session_id}/messages`
  - Retrieves chat message history and verified citation tags.

## 7. Citations
- `GET /api/v1/citations/{chunk_id}`
  - Fetches the verified document title, page number, and source text snippet for a citation chunk after confirming matter authorization.

## 8. Security & Evaluation
- `GET /api/v1/security/status`
  - Audits offline mode, loopback configuration, model availability, and quarantine count.
- `GET /api/v1/security/audit`
  - Lists recent security authorization events (Admin only).
- `POST /api/v1/evaluation/runs`
  - Executes automated adversarial evaluation benchmark and records research metrics.
- `GET /api/v1/evaluation/runs`
  - Lists completed evaluation benchmark reports.
