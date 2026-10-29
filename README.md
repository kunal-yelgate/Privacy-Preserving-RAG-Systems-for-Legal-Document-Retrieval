# Privacy-Preserving Legal RAG

A local legal-document retrieval and question-answering prototype with matter-level
authorization. The system retrieves only public documents and private documents that
the requesting user is allowed to access. Authorization is enforced in the retrieval
query, checked again in application code, and revalidated before evidence is sent to
the local language model.

> **Important:** This project is research software and provides research support only.
> It is not legal advice. Do not add real client documents to this repository or to an
> unprotected development machine.

## Features

- Local FastAPI API with a SQLite database.
- PDF and DOCX ingestion with page, paragraph, and section references.
- Matter-level users, memberships, roles, and policy-version checks.
- Hybrid retrieval using SQLite FTS5 lexical search and deterministic dense embeddings.
- Evidence-only prompts and citation validation.
- Optional local answer generation through Ollama.
- Optional Streamlit user interface.
- Public-source ingestion with source and licence metadata.
- Synthetic adversarial evaluation for unauthorized-disclosure testing.
- No cloud model, OCR, telemetry, or analytics calls are required by the core app.

## Requirements

The following tools are required:

1. **Windows 10 or later**
2. **Python 3.11 or newer**
3. **Git** (only needed when cloning the repository)

The following are optional:

- **Ollama** for generated answers. The API, ingestion, retrieval, and tests can run
  without Ollama, but `/query` returns a generation-unavailable error when an answer
  is requested and Ollama is not running.
- **Streamlit** for the browser UI. It is installed by the `ui` extra.
- **Tesseract OCR** for scanned PDFs. OCR is not currently enabled by default; scanned
  PDFs are quarantined instead of being indexed.

## Installation on Windows

Open PowerShell and change to the project directory:

```powershell
cd "C:\Users\yelga\Desktop\legal-rag\Privacy Preserving RAG Systems for Legal Document Retrieval"
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation for the current user, run this once and then repeat
the activation command:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Install the application and development dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

For the optional Streamlit UI, install the UI extra as well:

```powershell
python -m pip install -e ".[dev,ui]"
```

Create the local environment file:

```powershell
Copy-Item .env.example .env
```

The default `.env` values are suitable for local development:

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | Application environment name |
| `DATABASE_PATH` | `data/legal_rag.sqlite3` | SQLite database location |
| `EMBEDDING_DIMENSIONS` | `384` | Size of deterministic local embeddings |
| `RETRIEVAL_TOP_K` | `8` | Maximum number of retrieved chunks |
| `HYBRID_ALPHA` | `0.7` | Dense-retrieval weight, from `0.0` to `1.0` |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Local Ollama endpoint |
| `OLLAMA_MODEL` | `qwen2.5:1.5b` | Ollama model used for generation |
| `OLLAMA_TIMEOUT_SECONDS` | `60` | Generation request timeout |

## Optional: install Ollama

Install Ollama from [ollama.com](https://ollama.com), start the Ollama service, and
download the configured model:

```powershell
ollama pull qwen2.5:1.5b
```

The model is downloaded and run locally. If you choose a different Ollama model, set
the same value in `.env`:

```text
OLLAMA_MODEL=your-local-model
```

## First run

### 1. Create a demo user and matter

From the project directory, with the virtual environment activated:

```powershell
python -m app.bootstrap
```

This creates:

- user ID: `demo-user`
- matter ID: `demo-matter`

To use different IDs:

```powershell
python -m app.bootstrap `
  --user-id alice `
  --display-name "Alice Example" `
  --matter-id case-001
```

The bootstrap command is for local development only. It does not expose an
unauthenticated user-creation API.

### 2. Start the API

```powershell
python -m uvicorn app.main:app --reload
```

The API is available at <http://127.0.0.1:8000>. Interactive API documentation is
available at <http://127.0.0.1:8000/docs>.

Check that the API is running:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected response:

```text
status
------
ok
```

### 3. Start the optional UI

Keep the API running, open a second PowerShell window, activate the virtual environment,
and run:

```powershell
cd "C:\Users\yelga\Desktop\legal-rag\Privacy Preserving RAG Systems for Legal Document Retrieval"
.\.venv\Scripts\Activate.ps1
streamlit run app/ui.py
```

Open the URL printed by Streamlit, normally
<http://localhost:8501>, and sign in with `demo-user`.

## API examples

Every protected endpoint requires the `X-User-Id` header. The following example asks
about all documents that `demo-user` is authorized to access:

```powershell
$headers = @{ "X-User-Id" = "demo-user" }
$body = @{
  question = "What evidence supports this claim?"
  scope = @{
    public = $true
    matter_ids = @("demo-matter")
  }
  stream = $false
} | ConvertTo-Json -Depth 4

Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/query `
  -Method Post `
  -Headers $headers `
  -ContentType "application/json" `
  -Body $body
```

Available endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Service health check |
| `POST` | `/query` | Secure hybrid retrieval and answer generation |
| `GET` | `/matters` | List matters visible to the user |
| `POST` | `/matters` | Create a matter for the authenticated user |
| `POST` | `/matters/{matter_id}/members` | Add a known user to a matter |
| `DELETE` | `/matters/{matter_id}/members/{user_id}` | Remove a matter member |
| `POST` | `/matters/{matter_id}/documents` | Upload a PDF or DOCX |
| `GET` | `/matters/{matter_id}/documents` | List matter documents |
| `GET` | `/audit` | View the authenticated user’s recent audit events |

## Upload a document

The API accepts `.pdf` and `.docx` files. Uploads are processed locally and receive a
status such as `indexed` or `quarantined`:

```powershell
curl.exe `
  -X POST `
  -H "X-User-Id: demo-user" `
  -F "file=@C:\path\to\document.pdf" `
  http://127.0.0.1:8000/matters/demo-matter/documents
```

Documents with unsupported formats, invalid metadata, or extraction failures are not
silently indexed.

## Ingest a licensed public document

Public documents must include explicit source and licence metadata:

```powershell
python -m app.ingest.public_update "C:\path\to\judgment.docx" `
  --source-id court-judgments `
  --source-title "Court judgments" `
  --license "Open Government Licence" `
  --source-url "https://example.test/judgment"
```

Confirm that the source licence permits local storage and indexing before ingestion.

## Evaluation and tests

Run the complete test suite:

```powershell
python -m pytest
```

Run formatting and lint checks:

```powershell
python -m ruff check app tests
python -m black --check app tests
```

Run the offline comparative evaluation report:

```powershell
python -m app.eval.report
```

The evaluation uses fictional data and reports retrieval/disclosure metrics, ablations,
latency, memory usage, index size, and Wilson 95% confidence intervals. Unrestricted
baselines are intentionally isolated from real documents.

## Security and privacy notes

- Access is default-deny and scoped by user identity and matter membership.
- Private matter IDs are applied as retrieval filters before ranking.
- Retrieved chunks are checked again before prompt construction.
- Policy changes invalidate a stale authorization snapshot.
- Generated answers are accepted only when citations refer to authorized evidence.
- The `X-User-Id` header is a local development identity mechanism, not production
  authentication.
- Do not commit `.env`, private documents, generated indexes, or client data.
- For production use, replace the development identity mechanism and review deployment,
  storage encryption, logging, backups, and access controls.

## Project layout

```text
app/
  auth/          User, matter, and membership policy
  eval/          Synthetic adversarial harness and evaluation reports
  generation/    Evidence prompts, Ollama adapter, citation validation
  ingest/        PDF/DOCX extraction, chunking, and metadata pipelines
  retrieval/     Local embeddings and SQLite hybrid index
  security/      Authorization filtering and context validation
  main.py        FastAPI application
  ui.py          Optional Streamlit interface
tests/           Security, ingestion, generation, and evaluation tests
data/            Local SQLite database location
```

Additional design and project documents are available in
[ARCHITECTURE.md](./ARCHITECTURE.md), [DESIGN.md](./DESIGN.md), [PRD.md](./PRD.md),
and [RULES.md](./RULES.md).
