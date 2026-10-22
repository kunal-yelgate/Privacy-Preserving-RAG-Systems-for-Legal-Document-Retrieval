# Privacy-Preserving RAG Systems for Legal Document Retrieval

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14%20App%20Router-black.svg)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6.svg)](https://www.typescriptlang.org/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Persistent%20Vector%20Store-orange.svg)](https://www.trychroma.com/)
[![Ollama](https://img.shields.io/badge/Ollama-Offline%20Local%20Inference-white.svg)](https://ollama.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **A 100% offline-capable, privacy-preserving, matter-isolated Retrieval-Augmented Generation (RAG) system engineered for confidential legal discovery, statutory analysis, and empirical research on consumer hardware (8 GB RAM).**

---

## 📌 Table of Contents
1. [Project Overview](#-project-overview)
2. [The Core Problem](#-the-core-problem)
3. [System Capabilities](#-system-capabilities)
4. [Architecture & Request Flow](#-architecture--request-flow)
5. [Privacy & Security Framework](#-privacy--security-framework)
6. [Technology Stack](#-technology-stack)
7. [Repository Structure](#-repository-structure)
8. [Getting Started (Windows 10/11)](#-getting-started-windows-1011)
9. [Empirical Research & Evaluation Benchmark](#-empirical-research--evaluation-benchmark)
10. [API Reference Summary](#-api-reference-summary)
11. [Hardware Profile & Low-Memory Optimization](#-hardware-profile--low-memory-optimization)
12. [Contributing & Responsible Disclosure](#-contributing--responsible-disclosure)

---

## 📖 Project Overview

**Privacy-Preserving RAG Systems for Legal Document Retrieval** is an enterprise-grade, local-first artificial intelligence assistant tailored for legal practitioners, corporate counsel, and privacy researchers.

Unlike standard RAG pipelines that send confidential contract drafts, litigation exhibits, and attorney notes to third-party hosted cloud APIs (e.g., OpenAI, Anthropic, cloud vector stores), this system operates **exclusively on the local machine**. Every step—cryptographic file hashing, document parsing, chunking, dense vector embedding, keyword indexing, and generative inference—executes entirely on local loopback (`127.0.0.1`), ensuring zero data exfiltration.

In addition to running offline, the platform addresses a fundamental architectural flaw in multi-tenant enterprise RAG: **cross-matter data leakage**. By coupling an authoritative SQLite permission store with pre-retrieval query constraints in ChromaDB and BM25, the system guarantees that researchers cannot retrieve or synthesize information outside their explicitly authorized legal matters.

---

## ⚠️ The Core Problem

Cloud-based GenAI introduces severe regulatory, legal, and operational hazards for law firms and legal departments:

1. **Breach of Attorney-Client Privilege**: Uploading confidential client documents to cloud providers risks waiving privilege and violating non-disclosure agreements (NDAs) and privacy mandates (GDPR, HIPAA, DPDP Act 2023).
2. **Cross-Matter & Multi-Tenant Leakage**: Standard vector databases retrieve information purely based on cosine distance. If two matters share similar statutory language (e.g., non-compete clauses, indemnification limits), unauthorized confidential details can leak into generation context.
3. **Indirect Prompt Injection**: Hostile third-party legal documents (e.g., discovery filings, opposing counsel submissions) can contain adversarial directives designed to override system constraints or exfiltrate hidden secrets.
4. **Legal Hallucinations**: Standard LLMs often fabricate citations, court cases, statutory sections, and legal precedents when retrieved context is ambiguous.
5. **Hardware Constraints**: Most local AI workflows demand expensive workstation GPUs (NVIDIA RTX 4090 / A100). Small legal firms and independent researchers require systems that run efficiently on standard consumer laptops with 8 GB RAM and CPU inference.

---

## ✨ System Capabilities

### 1. Ingestion with Full Provenance Preservation
- Ingests **PDF** and **TXT** legal files.
- Employs **PyMuPDF** (`pymupdf`) to extract text page-by-page, preserving 1-indexed page boundaries and detecting password-encrypted or corrupted files.
- Automatically computes cryptographic **SHA-256 content hashes** to eliminate duplicate files and prevent tampering.
- Implements `SafeFileManager` to prevent directory traversal exploits (`../../etc/passwd`).
- Quarantines unreadable, encrypted, or malformed files into `data/quarantine/`.

### 2. Legal-Aware Chunking
- Normalizes legal whitespace, statutory symbols (§), sub-clauses, and quotations without destroying formatting.
- Generates overlapping sliding-window passages tagged with `document_id`, `matter_id`, `page_number`, `chunk_index`, and `classification`.

### 3. Hybrid Retrieval with Reciprocal Rank Fusion (RRF)
- **Dense Semantic Retrieval**: Generates 768-dimensional local vector embeddings via `nomic-embed-text` and searches persistent ChromaDB indices.
- **Sparse Keyword Retrieval**: Uses **BM25 Okapi** (`rank-bm25`) to match exact terms, party names, contract dates, and statutory sections.
- **Reciprocal Rank Fusion**: Merges semantic and keyword candidates using reciprocal rank weighting:
  $$\text{RRF\_Score}(d) = \sum_{m \in \{\text{semantic}, \text{bm25}\}} \frac{1}{60 + \text{rank}_m(d)}$$

### 4. Evidence-Grounded Generation & Citation Verification
- Generates responses via **`qwen2.5:1.5b`** running in local Ollama.
- Enforces an untrusted data boundary: the prompt treats retrieved passages as raw data and explicitly ignores embedded directives.
- **Strict Citation Validation**: Every factual assertion requires a `[cite-X]` tag. The system maps citations directly to source chunks and rejects hallucinated citation markers.
- **Strict Abstention**: If authorized evidence is missing or insufficient, the assistant explicitly states that the evidence is insufficient rather than guessing.

### 5. Multi-Tenant Matter Isolation
- Every document, chunk, vector, and chat conversation is partitioned by `matter_id`.
- Pre-retrieval filters block unauthorized vectors from ever reaching the LLM context.
- Validated with multi-tenant canary secrets (`CANARY-CORP-ALPHA-7892` and `CANARY-LABOR-BETA-4159`) to prove **0% cross-matter leakage**.

### 6. Interactive Web Interface
- Responsive **Next.js 14** application with dashboard metrics, matter management, document explorer, research workspace, interactive evidence inspector, and security audit log.

---

## 🏗 Architecture & Request Flow

```
                      +------------------------------------------+
                      |         Next.js 14 Web Frontend          |
                      |  (Dashboard | Research | Documents | Sec)|
                      +--------------------+---------------------+
                                           | HTTP / REST (127.0.0.1:8000)
                                           v
                      +------------------------------------------+
                      |         FastAPI Application Server       |
                      |  - Request Validation (Pydantic v2)      |
                      |  - Authentication & JWT Verification     |
                      |  - Server-Side Matter Authorization     |
                      +--------------------+---------------------+
                                           |
         +---------------------------------+---------------------------------+
         |                                 |                                 |
         v                                 v                                 v
+------------------+             +-------------------+             +-------------------+
|  Storage Layer   |             |  Retrieval Layer  |             |  Inference Engine |
|                  |             |                   |             |                   |
| SQLite (WAL)     |             | ChromaDB Vectors  |             | Local Ollama API  |
| - Users & Auth   |             | (HNSW Cosine)     |             | - nomic-embed-    |
| - Matters & ACLs |             |                   |             |   text (Embeddings|
| - Documents Meta |             | BM25 Okapi Index  |             | - qwen2.5:1.5b    |
| - Audit Logs     |             | (Keyword search)  |             |   (Grounded Gen)  |
|                  |             |                   |             |                   |
| Filesystem:      |             | Reciprocal Rank   |             | Zero Cloud Egress |
| - data/originals |             | Fusion (RRF)      |             | 127.0.0.1 Binding |
| - data/quarantine|             |                   |             |                   |
+------------------+             +-------------------+             +-------------------+
```

### Complete Query & Generation Lifecycle
1. **Client Submission**: User submits natural-language query specifying an active `matter_id`.
2. **Authorization Guard**: FastAPI middleware verifies caller's JWT token and confirms matter membership in SQLite.
3. **Hybrid Search**:
   - Query is embedded locally using `nomic-embed-text`.
   - ChromaDB queries top candidates with metadata constraint `{"matter_id": matter_id}`.
   - BM25 searches the matter's isolated keyword index.
   - Reciprocal Rank Fusion ($RRF$) calculates combined scores and deduplicates chunks.
4. **Prompt Construction**: Evidence is structured into numbered blocks `[cite-1]`, `[cite-2]` accompanied by strict system instructions.
5. **Local Inference**: Ollama executes `qwen2.5:1.5b` with low temperature ($0.1$) and bounded token generation.
6. **Citation Attestation**: `CitationService` parses citation tags in the answer, checks them against authorized passages, and constructs interactive citation objects with document title and page numbers.
7. **Audit Logging**: The request, matter, and outcome are recorded in SQLite audit ledger with all sensitive canary tokens redacted.

---

## 🔒 Privacy & Security Framework

| Security Feature | Implementation | Threat Mitigated |
|---|---|---|
| **Zero External Egress** | Loopback binding (`127.0.0.1`) for API and Ollama; ChromaDB telemetry disabled | Accidental transmission of client secrets to remote cloud servers |
| **Pre-Retrieval Filtering** | Authoritative SQLite permission verification before querying ChromaDB | Cross-matter leakage and unauthorized vector retrieval |
| **Canary Secret Defense** | Unique canary tokens embedded in synthetic test documents | Verifies through automated tests that Matter A cannot access Matter B |
| **Path Traversal Defense** | `SafeFileManager.validate_file_path()` checks against authorized root | Directory traversal attacks (`../../etc/passwd`, `..\cmd.exe`) |
| **Prompt Injection Isolation**| Evidence passages bracketed as untrusted data; prompt ignores overrides | Adversarial document directives attempting privilege escalation |
| **Log Sanitization** | `RedactingFormatter` regex masks canaries, tokens, passwords | Accidental exposure of secrets in system logs or error reports |
| **Citation Verification** | Post-generation citation cross-referencing | Invention of false legal precedents or hallucinated page numbers |

---

## 💻 Technology Stack

### Backend
- **Language**: Python 3.11 / 3.12 / 3.13
- **Web Framework**: FastAPI (ASGI) + Uvicorn
- **Validation**: Pydantic v2 + Pydantic-Settings
- **PDF Extraction**: PyMuPDF (`pymupdf`)
- **Vector Database**: ChromaDB (Persistent local HNSW cosine index)
- **Keyword Search**: `rank-bm25` (BM25 Okapi)
- **Relational Storage**: SQLite3 with Write-Ahead Logging (WAL) and foreign key enforcement
- **Authentication**: JWT (JSON Web Tokens) with `bcrypt` password hashing
- **Testing**: `pytest`, `pytest-asyncio`, and HTTPX

### Local AI Subsystem
- **Inference Runtime**: Ollama for Windows (100% offline, local loopback)
- **Embedding Model**: `nomic-embed-text` (768 dimensions, 274 MB)
- **Generation Model**: `qwen2.5:1.5b` (quantized 1.5B parameters, ~986 MB, CPU-friendly)

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript (strict mode enabled)
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Architecture**: Decoupled typed API client, server-side layouts, client-side interactive workspaces

---

## 📂 Repository Structure

```
legal-rag/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application entry point and CORS configuration
│   │   ├── api/                        # Versioned API routes
│   │   │   ├── router.py               # Aggregated /api/v1 router
│   │   │   └── v1/                     # Modular sub-routers (auth, health, matters, documents, etc.)
│   │   ├── core/                       # Settings, logging with redaction, centralized exceptions
│   │   ├── domain/                     # Enums (UserRole, IngestionStatus, ClassificationLevel)
│   │   ├── schemas/                    # Pydantic v2 schemas for request and response validation
│   │   ├── services/                   # Business logic (Ingestion, Chunking, Retrieval, Generation)
│   │   ├── repositories/               # SQLite persistence repositories (User, Matter, Document, Audit)
│   │   └── infrastructure/             # PyMuPDF parser, Ollama client, ChromaDB adapter, BM25 index
│   ├── tests/
│   │   ├── unit/                       # Chunking, citations, and file manager security tests
│   │   ├── security/                   # Cross-matter denial and canary redaction tests
│   │   └── integration/                # End-to-end ingestion, hybrid search, and API route tests
│   └── requirements.txt                # Python backend dependencies
├── frontend/
│   ├── src/
│   │   ├── app/                        # Next.js App Router (Dashboard, Research, Documents, Matters, Sec)
│   │   ├── components/layout/          # Responsive Navbar and Sidebar navigation
│   │   ├── lib/api/client.ts           # Typed API client
│   │   └── types/index.ts              # TypeScript interface definitions
│   ├── package.json                    # Frontend dependencies
│   ├── tailwind.config.js              # Custom styling tokens
│   └── tsconfig.json                   # Strict TypeScript configuration
├── data/                               # Local persistent storage directories
│   ├── originals/                      # Safe internal original files
│   ├── chroma/                         # Persistent ChromaDB vector collections
│   ├── sqlite/                         # SQLite legal_rag.db database
│   └── quarantine/                     # Quarantined malformed/corrupted files
├── datasets/synthetic/                 # Multi-matter test documents with embedded canary tokens
├── experiments/reports/                # Automated empirical benchmark reports (JSON)
├── docs/                               # Comprehensive technical documentation
│   ├── architecture.md                 # System architecture and request flows
│   ├── setup-windows.md                # Detailed Windows installation guide
│   ├── api-reference.md                # Full API endpoint documentation
│   ├── security-model.md               # Privacy boundaries and data lifecycle
│   ├── threat-model.md                 # Threat matrix and mitigations
│   ├── testing.md                      # Test suite documentation
│   └── experiments.md                  # Research evaluation methodology
├── scripts/
│   ├── init_dirs.py                    # Directory structure bootstrap
│   └── generate_synthetic_docs.py      # Synthetic multi-matter PDF & TXT generator
├── .env.example                        # Environment variables template
├── pytest.ini                          # Pytest configuration
├── README.md                           # Master project documentation
└── SECURITY.md                         # Security reporting policy
```

---

## 🚀 Getting Started (Windows 10/11)

### Prerequisites
- Windows 10 or 11 (64-bit)
- 8 GB RAM minimum
- Python 3.11+
- Node.js v18+ and npm
- [Ollama for Windows](https://ollama.com) installed and running

---

### Step 1: Download Required Local Models
Open PowerShell and pull the local embedding and generation models into Ollama:

```powershell
ollama pull nomic-embed-text
ollama pull qwen2.5:1.5b
```

Verify that the models are installed locally:
```powershell
ollama list
```

---

### Step 2: Set Up Backend Environment
Open a PowerShell terminal in the project root:

```powershell
cd c:\Users\yelga\Desktop\legal-rag

# 1. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Upgrade pip and install backend dependencies
pip install --upgrade pip
pip install -r backend\requirements.txt

# 3. Generate synthetic multi-matter evaluation documents
python scripts\generate_synthetic_docs.py
```

---

### Step 3: Run the Automated Test Suite
Execute the comprehensive test suite (unit, integration, and security tests):

```powershell
.\venv\Scripts\pytest backend\tests -v
```

Expected output:
```text
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\yelga\Desktop\legal-rag
configfile: pytest.ini

backend/tests/integration/test_api_endpoints.py::test_api_health_and_readiness PASSED [  9%]
backend/tests/integration/test_api_endpoints.py::test_auth_login_and_access_flow PASSED [ 18%]
backend/tests/integration/test_pipeline.py::test_full_ingestion_and_hybrid_retrieval PASSED [ 27%]
backend/tests/security/test_isolation_and_security.py::test_cross_matter_authorization_denial PASSED [ 36%]
backend/tests/security/test_isolation_and_security.py::test_log_redaction_masks_canary_tokens PASSED [ 45%]
backend/tests/unit/test_chunking.py::test_normalize_legal_text PASSED    [ 54%]
backend/tests/unit/test_chunking.py::test_chunking_preserves_page_numbers PASSED [ 63%]
backend/tests/unit/test_citations.py::test_format_evidence_and_extract_valid_citations PASSED [ 72%]
backend/tests/unit/test_file_manager.py::test_sanitize_filename PASSED   [ 81%]
backend/tests/unit/test_file_manager.py::test_validate_file_path_traversal PASSED [ 90%]
backend/tests/unit/test_file_manager.py::test_sha256_computation PASSED  [100%]

============================= 11 passed in 24.14s =============================
```

---

### Step 4: Launch the Backend API Server
```powershell
.\venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Endpoint: `http://127.0.0.1:8000/api/v1`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`
- Health / Readiness Check: `http://127.0.0.1:8000/api/v1/health/ready`

---

### Step 5: Launch the Next.js Frontend
Open a second PowerShell window:

```powershell
cd c:\Users\yelga\Desktop\legal-rag\frontend
npm install
npm run dev
```
Open your browser at **`http://localhost:3000`**.

---

### 🔑 Pre-Seeded Default Accounts
For local testing and evaluation, the system pre-configures:
- **Administrator**: `admin` / `AdminSecureOffline2026!`
- **Researcher 1**: `researcher1` / `ResearcherPass2026!`
- **Researcher 2**: `researcher2` / `ResearcherPass2026!`

---

## 🔬 Empirical Research & Evaluation Benchmark

The system includes a built-in evaluation framework designed to generate reproducible metrics for research papers on privacy-preserving RAG.

### Evaluation Metrics Defined
1. **Recall@5**: Percentage of relevant contract/statute clauses retrieved within top-5 candidates.
2. **Mean Reciprocal Rank (MRR)**: Average reciprocal rank of the first relevant chunk.
3. **Cross-Matter Leakage Rate**: Percentage of queries in Matter A that expose canary tokens belonging to Matter B:
   $$\text{Leakage Rate} = \frac{\text{Queries Leaking Forbidden Canary}}{\text{Total Queries}}$$
   *(Target: Exactly 0.0%)*
4. **Prompt Injection Success Rate**: Percentage of adversarial queries on `matter-103` where the model executes embedded overrides.
   *(Target: Exactly 0.0%)*
5. **Citation Precision**: Proportion of generated citation tags `[cite-X]` referencing actual verified text passages in the authorized evidence.
6. **Average Latency**: Mean end-to-end response time in milliseconds on local CPU.

### Running the Benchmark
1. In the web interface, navigate to the **Security Center** (`http://localhost:3000/security`).
2. Click **"Run Security Evaluation"**.
3. Results are rendered in the dashboard and exported to `experiments/reports/{run_id}_report.json`.

---

## 📡 API Reference Summary

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/v1/health` | Application liveness probe | No |
| `GET` | `/api/v1/health/ready` | Subsystem readiness probe (SQLite, ChromaDB, Ollama) | No |
| `POST`| `/api/v1/auth/login` | Issues JWT Bearer token | No |
| `GET` | `/api/v1/auth/me` | Returns current user profile | Yes |
| `GET` | `/api/v1/matters` | Lists matters accessible to caller | Yes |
| `POST`| `/api/v1/matters` | Creates new legal matter | Yes |
| `POST`| `/api/v1/documents` | Uploads and ingests legal PDF or TXT | Yes |
| `GET` | `/api/v1/documents` | Lists documents for matter | Yes |
| `DELETE`| `/api/v1/documents/{id}` | Deletes document, vectors, and BM25 tokens | Yes |
| `POST`| `/api/v1/search` | Executes hybrid search ($RRF$) within matter boundary | Yes |
| `POST`| `/api/v1/chat` | Submits legal question; returns grounded answer + citations | Yes |
| `GET` | `/api/v1/chat/sessions` | Lists conversation sessions for caller | Yes |
| `GET` | `/api/v1/citations/{id}` | Returns verified source snippet and page number | Yes |
| `GET` | `/api/v1/security/status` | Audits offline mode, model availability, quarantine count | Yes |
| `GET` | `/api/v1/security/audit` | Retrieves immutable audit trail | Admin Only |
| `POST`| `/api/v1/evaluation/runs` | Runs automated adversarial research benchmark | Admin Only |

---

## ⚡ Hardware Profile & Low-Memory Optimization

This system has been engineered to run within **8 GB RAM** without crashing or freezing:
- **Quantized 1.5B Model**: Uses `qwen2.5:1.5b` (~986 MB disk footprint), allowing CPU inference with minimal RAM consumption.
- **Configurable Batching**: Ingestion batches embeddings in groups of 8 (`EMBEDDING_BATCH_SIZE=8`) to avoid memory spikes during large document processing.
- **Top-K Bounding**: Generation context is capped (`RETRIEVAL_TOP_K=4-5`), avoiding massive context windows that overwhelm local RAM.
- **SQLite WAL Mode**: Provides fast concurrent reads and writes with minimal locking overhead.

---

## 🛡 Contributing & Responsible Disclosure

This project is intended for research, academic evaluation, and confidential legal practice.
- To report a privacy issue or potential boundary bypass, please review our [SECURITY.md](SECURITY.md) policy.
- For comprehensive installation and architectural details, refer to the guides in [`docs/`](docs/).

---

**Project Title**: *Privacy-Preserving RAG Systems for Legal Document Retrieval*  
**Platform**: Windows 10/11 Local Offline Workstation  
**License**: MIT License
