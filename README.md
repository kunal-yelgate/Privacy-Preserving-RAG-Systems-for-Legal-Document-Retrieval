# Privacy-Preserving Legal RAG

Privacy-Preserving Legal RAG is a **local legal research assistant**. A user uploads
case documents, asks a question in normal language, and receives an answer based on
the uploaded evidence. The answer includes source references and is refused when the
system cannot find enough supporting evidence.

The project is designed for privacy: documents, search, embeddings, and answer
generation can all run on the user’s computer. Documents are not sent to a cloud AI
provider by this application.

> **Important:** This is research software, not legal advice. Always have a qualified
> legal professional review important decisions. Do not place real client documents in
> an unprotected development environment.

## What does the project do?

The application provides a simple web workflow:

1. Create or choose a case.
2. Upload a PDF or DOCX document.
3. The system reads and indexes the document locally.
4. Ask a question about the case.
5. The system finds relevant authorized passages.
6. Ollama writes an answer using only those passages.
7. The interface displays the answer and the documents/passages used as sources.

The system also keeps private cases separated. A user can only retrieve documents
from matters to which that user has access.

## What is RAG?

**RAG** means **Retrieval-Augmented Generation**. It is a safer way to use an AI model
with private documents:

```text
Your question
      |
      v
1. Retrieve relevant passages from your local documents
      |
      v
2. Check that the passages belong to a case the user may access
      |
      v
3. Give only the authorized passages to the local AI model
      |
      v
4. Generate an answer with citations
```

The model does not automatically know the contents of your uploaded documents. The
retrieval step supplies the relevant evidence for each question. This reduces
unsupported answers and keeps the model from receiving unrelated private matters.

## RAG pipeline used in this project

### 1. Document upload

The Next.js web interface sends a PDF or DOCX file to the local FastAPI server.

### 2. Text extraction

- PDFs are read with **PyMuPDF**.
- DOCX files are read with **python-docx**.
- Page, paragraph, and section information is retained.
- Documents that cannot be safely extracted are quarantined instead of silently
  entering the index.

### 3. Chunking

Long documents are split into smaller passages. Each passage keeps metadata such as:

- document ID
- case/matter ID
- page number
- paragraph number
- section heading

### 4. Local embeddings

The project currently uses a deterministic local **hash-based embedder** implemented
in `app/retrieval/embeddings.py`. It creates a 384-dimensional vector without
calling an external embedding API.

This is useful for a privacy-first prototype because it has no model download or
network requirement. For higher-quality production retrieval, a local embedding model
such as `nomic-embed-text` or `bge-m3` can be added later.

### 5. Hybrid retrieval

The local index combines two search methods:

- **SQLite FTS5** for keyword/lexical matching.
- **Dense cosine similarity** for approximate semantic matching.

The two scores are normalized and combined using `HYBRID_ALPHA`. Before ranking,
private matter scope filters are applied.

### 6. Authorization filtering

Authorization is enforced more than once:

- The database retrieval query applies the matter filter.
- Application code checks the returned chunks again.
- The policy version is checked before prompt construction.
- Revoked or unknown users are denied by default.

### 7. Evidence-only prompt

The selected passages are placed into a prompt that tells Ollama:

- documents are evidence, not instructions;
- answers must use only the supplied evidence;
- factual claims must include an evidence citation;
- the model must abstain when evidence is insufficient.

The current date is also supplied so relative dates such as “today” or “last year”
can be interpreted. This is context, not model retraining.

### 8. Local answer generation and validation

Ollama generates the draft answer locally. The application then validates every
citation against the authorized evidence. Unsupported or missing citations cause the
system to abstain instead of presenting an unsupported answer.

## Technologies used

| Area | Technology | Purpose |
|---|---|---|
| User interface | Next.js 15, React 19, TypeScript | Simple browser experience |
| API server | FastAPI, Uvicorn | Local upload, query, and case APIs |
| Database | SQLite | Local users, cases, documents, chunks, and audit records |
| Keyword search | SQLite FTS5 | Lexical document retrieval |
| Dense retrieval | NumPy + local hash embedder | Private, deterministic vector search |
| PDF processing | PyMuPDF | Local PDF text extraction |
| DOCX processing | python-docx | Local Word document extraction |
| Generation | Ollama | Local language-model answers |
| Validation | Pytest, Ruff, Black | Tests, linting, and formatting |

## Ollama model

The default model is:

```text
mistral:latest
```

Install it locally:

```powershell
ollama pull mistral:latest
```

This model is used for **answer generation**, not for document parsing or embedding.
Document parsing is handled by PyMuPDF/python-docx, and retrieval uses the local
embedding/index pipeline described above.

Recommended model sizes:

| Computer | Model | Recommendation |
|---|---|---|
| 8 GB RAM | `qwen2.5:1.5b` | Fastest, but weaker legal answers |
| 16 GB RAM | `mistral:latest` | Default for this setup |
| 16 GB RAM | `qwen3:8b` | Better reasoning, more memory required |
| 32 GB RAM or a capable GPU | `qwen3:14b` | Higher quality, slower locally |

If you select another model, update `.env`:

```text
OLLAMA_MODEL=qwen3:8b
```

The model is not trained or fine-tuned on uploaded documents. Each question receives
only the authorized retrieved evidence. This is the intended privacy-preserving
behavior.

## Requirements

Required:

- Windows 10 or later
- Python 3.11 or newer
- Node.js 18.18 or newer
- npm
- Git

Required for generated answers:

- Ollama installed and running locally
- The configured Ollama model downloaded

Optional:

- Tesseract OCR for a future scanned-PDF OCR integration. Scanned PDFs are currently
  quarantined when no extractable text is available.

## Clone the project

Open PowerShell and run:

```powershell
git clone https://github.com/kunal-yelgate/Privacy-Preserving-RAG-Systems-for-Legal-Document-Retrieval.git
cd Privacy-Preserving-RAG-Systems-for-Legal-Document-Retrieval
```

If you already downloaded the project, only run the `cd` command using the actual
project path.

## Install the backend

Create a Python virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell refuses to activate the environment:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Install the Python application and development requirements:

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Create the backend configuration file:

```powershell
Copy-Item .env.example .env
```

The default configuration is:

| Variable | Default | Meaning |
|---|---|---|
| `APP_ENV` | `development` | Local environment name |
| `DATABASE_PATH` | `data/legal_rag.sqlite3` | Local SQLite database |
| `EMBEDDING_DIMENSIONS` | `384` | Local vector size |
| `RETRIEVAL_TOP_K` | `8` | Maximum retrieved passages |
| `HYBRID_ALPHA` | `0.7` | Dense-search weight from `0.0` to `1.0` |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Local Ollama address |
| `OLLAMA_MODEL` | `mistral:latest` | Local answer model |
| `OLLAMA_TIMEOUT_SECONDS` | `60` | Ollama request timeout |

## Install and configure Ollama

Install Ollama from <https://ollama.com>, start it, and download the model:

```powershell
ollama pull mistral:latest
```

Check that the model is available:

```powershell
ollama list
```

Ollama normally listens at `http://127.0.0.1:11434`. Keep Ollama running while asking
questions through the application.

## Install the frontend

Open a second PowerShell window:

```powershell
cd "C:\path\to\Privacy-Preserving-RAG-Systems-for-Legal-Document-Retrieval\frontend"
npm install
```

The frontend uses these defaults:

```text
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_USER_ID=demo-user
```

To customize them, copy the example:

```powershell
Copy-Item .env.example .env.local
```

Then edit `frontend/.env.local`.

## Run the complete project

Three local processes are used.

### Terminal 1: start Ollama

Make sure the Ollama application/service is running and that `mistral:latest` is installed.

### Terminal 2: start the backend

From the repository root, with the Python virtual environment activated:

```powershell
python -m app.bootstrap
python -m uvicorn app.main:app --reload
```

The backend runs at:

- API: <http://127.0.0.1:8000>
- API documentation: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>

Verify the backend:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected result:

```text
status
------
ok
```

### Terminal 3: start the frontend

```powershell
cd "C:\path\to\Privacy-Preserving-RAG-Systems-for-Legal-Document-Retrieval\frontend"
npm run dev
```

Open <http://localhost:3000>.

The default development user is `demo-user`, and the bootstrap command creates the
default case `demo-matter`.

## Use the application

1. Open <http://localhost:3000>.
2. Choose `demo-matter`, or enter a name to create a new case.
3. Click **Choose a document**.
4. Select a text-based PDF or DOCX file.
5. Click **Upload document**.
6. Wait for the message that the document is ready.
7. Type a question such as:

   ```text
   What evidence supports the contract breach claim?
   ```

8. Click **Find my answer**.
9. Review the answer and the sources shown below it.

If the answer cannot be supported by authorized passages, the system abstains. That
behavior is intentional.

## Test the project

Run the backend tests:

```powershell
python -m pytest
```

Run linting and formatting checks:

```powershell
python -m ruff check app tests
python -m black --check app tests
```

Build the frontend:

```powershell
cd frontend
npm run build
```

Run the offline synthetic evaluation:

```powershell
python -m app.eval.report
```

The evaluation uses fictional documents and tests authorized queries, cross-matter
queries, indirect disclosure attempts, prompt injection, and unanswerable questions.

## Troubleshooting

### “Cannot connect to the API”

Start the backend from the repository root:

```powershell
python -m uvicorn app.main:app --reload
```

### “Local generation unavailable”

Check Ollama and the model:

```powershell
ollama list
ollama pull mistral:latest
```

Then retry the question.

### The document is quarantined

Use a normal text-based PDF or DOCX. Scanned/image-only PDFs are not currently
processed because OCR is not enabled by default.

### The frontend cannot find a case

Run:

```powershell
python -m app.bootstrap
```

Then refresh <http://localhost:3000>.

## Privacy and security

- All core processing is local.
- Matter access is default-deny.
- Unknown users cannot query documents.
- Private matter filters are applied before ranking.
- Retrieved chunks are checked again before reaching Ollama.
- Policy changes invalidate stale authorization snapshots.
- Answers must cite authorized evidence.
- `.env`, private documents, and local database files must not be committed.

The current `X-User-Id` identity is a local development mechanism, not production
authentication. Production deployment requires real authentication, encrypted storage,
secure sessions, protected audit logs, backups, and a threat-model review.

## Project structure

```text
app/
  auth/          Users, cases, memberships, and authorization policy
  eval/          Synthetic security evaluation and reports
  generation/    Evidence prompts, Ollama client, citation validation
  ingest/        PDF/DOCX extraction, chunking, and metadata
  retrieval/     Local embeddings and SQLite hybrid retrieval
  security/      Scope filtering and authorization revalidation
  main.py        FastAPI backend
frontend/
  app/page.tsx   Case selection, upload, questions, and answers
  app/globals.css
tests/           Security, ingestion, generation, and API tests
data/            Local SQLite database location
```

Additional project documents:

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [DESIGN.md](./DESIGN.md)
- [PRD.md](./PRD.md)
- [RULES.md](./RULES.md)
