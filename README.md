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

The optional public knowledge base is stored in the local SQLite database. It starts
empty until public legal documents are ingested. Questions include the indexed public
sources alongside documents from the selected authorized case. The Constitution
instructions below show one way to add a public source.

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

The default LLM for local answer generation is:

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

Other model options:

| Computer | Model | Recommendation |
|---|---|---|


If you select another model, update `.env`:

```text
OLLAMA_MODEL=mistral:latest
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
| `RETRIEVAL_TOP_K` | `12` | Maximum retrieved passages |
| `HYBRID_ALPHA` | `0.7` | Dense-search weight from `0.0` to `1.0` |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Local Ollama address |
| `OLLAMA_MODEL` | `mistral:latest` | Local answer model |
| `OLLAMA_TIMEOUT_SECONDS` | `300` | Ollama request timeout |

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

Open PowerShell in the repository root, then install the locked frontend dependencies:

```powershell
Set-Location .\frontend
npm ci
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

## Run the project after setup

Complete the backend, Ollama, and frontend installation sections above once. For each
later run, open three PowerShell terminals. Start Terminals 2 and 3 in the repository
root (the folder containing `README.md`) and keep them open while using the application.

### Terminal 1: start Ollama

The Ollama service must be running and `mistral:latest` must already be installed. The
model download is a one-time step; check it with:

```powershell
ollama pull mistral:latest
ollama list
```

If Ollama is not already running as a Windows service or desktop app, start it in this
terminal and leave it open. Do not run this command when the Ollama service is already active:

```powershell
ollama serve
```

### Terminal 2: start the backend

From the repository root, initialize the local demo user/case (safe to rerun), then
start the API server. Use the project virtual environment's Python executable:

```powershell
.\.venv\Scripts\python.exe -m app.bootstrap
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
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

Run `npm ci` once during setup; on later runs, start the development server with:

```powershell
Set-Location .\frontend
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

By default, questions include any documents already in the public knowledge base. To ask
only about a private case document, the frontend/API can disable the public scope. If you
ingest the Constitution PDF using the instructions below, its source is identified as:

```text
The Constitution of India (as on 1 May 2024)
Source: Government of India, Legislative Department
```

### Rebuild the Constitution knowledge base

The indexed SQLite database is local and is intentionally ignored by Git. To build or
rebuild the public Constitution index, place a text-based PDF at the repository root as
`Constitution of India.pdf` and run:

```powershell
python -m app.ingest.public_update "Constitution of India.pdf" `
  --source-id constitution-of-india `
  --source-title "The Constitution of India (as on 1 May 2024)" `
  --license "Government of India public access" `
  --source-url "https://legislative.gov.in/constitution-of-india/"
```

The PDF must contain selectable text. Image-only scans are quarantined unless a local
OCR runtime is installed and configured.

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

Start the backend from the repository root using the project virtual environment:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

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
