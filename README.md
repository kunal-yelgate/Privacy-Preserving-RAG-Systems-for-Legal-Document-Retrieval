# Privacy-Preserving Legal RAG

This is the first local-firm MVP of the Indian-law research assistant described in
[PRD.md](./PRD.md). The current implementation focuses on Tier 2 synthetic matters and
the security boundary: private content is filtered in the index query, checked again in
application code, and revalidated against the policy version before prompt construction.

## Environment

- Windows development machine
- Python 3.11 or newer (validated here with Python 3.13.7)
- Local Ollama is the intended generation runtime
- Selected Ollama model: `qwen2.5:1.5b`
- SQLite and NumPy are used for the initial local index
- Retrieval uses SQLite FTS5 plus deterministic dense embeddings with configurable
  hybrid weighting (`HYBRID_ALPHA`)
- No cloud model, embedding, OCR, telemetry, or analytics calls are used
- PDF and DOCX extraction is local; scanned PDFs are quarantined until a local
  Tesseract OCR runtime is installed

## Setup

```powershell
cd "Privacy Preserving RAG Systems for Legal Document Retrieval"
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload
```

The health endpoint is `GET /health`. The query endpoint is `POST /query` and requires
the `X-User-Id` header. The current endpoint returns the authorized evidence and the
evidence-only prompt; generation is intentionally kept behind the local Ollama adapter
until a model is selected and downloaded.

Matter management is available through `POST /matters`, `GET /matters`,
`POST /matters/{matter_id}/members`, and
`DELETE /matters/{matter_id}/members/{user_id}`. Document upload and listing use
`POST` and `GET /matters/{matter_id}/documents`. Every endpoint requires a known
`X-User-Id`; matter membership changes increment `policy_version` immediately.

The ingestion service accepts private matter metadata plus a local PDF or DOCX path.
It preserves page and paragraph references, detects section headings, embeds only
private chunks tagged with their matter ID, and records malformed or unextractable
documents as `quarantined` rather than indexing them.

Hybrid retrieval combines normalized dense cosine scores with normalized FTS5 scores.
Both retrieval paths apply the same public/matter scope filter before ranking.

The offline adversarial harness is available under `app/eval`. It uses 50 fictional
queries across authorized, direct cross-matter, indirect cross-matter, prompt-injection,
and unanswerable categories. It evaluates three hybrid configurations (`alpha=0.3`,
`0.7`, and `1.0`) and reports URR and CMDR without using Ollama or real documents.

The comparative M8 evaluation can be generated with:

```powershell
python -m app.eval.report
```

It reports lexical and dense unrestricted synthetic baselines alongside the filtered
hybrid proposal, including Wilson 95% confidence intervals. Unrestricted configurations
are deliberately isolated to the fictional corpus and must never be run against real
documents.

When `POST /query` uses the default `stream=false`, the local Ollama answer is accepted
only when every parsed citation belongs to the authorized evidence set and at least one
authorized citation is present. Unsupported or missing citations cause an abstention.
`stream=true` returns local Ollama NDJSON tokens after authorization and context
validation; clients should run the completed text through the same citation validator.

Run the security tests:

```powershell
python -m pytest
python -m ruff check app tests
python -m black --check app tests
```

Do not place real client files in this repository. Use synthetic matter data for
security and baseline experiments.
