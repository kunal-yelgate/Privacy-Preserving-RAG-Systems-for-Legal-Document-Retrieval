# MEMORY — Project Context and Decision Log

> Living file. Humans and AI assistants read this first, then update it after each task. Keep entries short and dated. Do not store secrets, real client data or personal data here.

## 1. Project Snapshot
- **Name:** Privacy-Preserving Legal RAG (Indian law)
- **Team:** Kunal Yelgate, Aditya Kandle (SGGSIE&T, Nanded)
- **Goal:** Legal research assistant where private case data cannot leak across users or organisations, while keeping useful retrieval quality and acceptable speed.
- **Core invariant:** `R(u,q) ⊆ Public ∪ A(u)`
- **Status:** MVP foundation implemented; ingestion, UI, evaluation, and Tier 1 remain.
- **Related paper:** "Privacy-Preserving RAG Systems for Legal Document Retrieval"; no experimental results exist yet.

## 2. Environment Facts
- Dev machine: Windows, about 8 GB RAM, GPU uncertain (confirm and record)
- LLM: Ollama, selected model `mistral:latest` for local grounded generation
- Embeddings: deterministic local hash baseline for the MVP; replaceable local model interface
- Vector store: SQLite with NumPy vectors for the MVP
- Ingestion: local PyMuPDF and python-docx extraction; scanned-PDF OCR fails closed until a local Tesseract runtime is approved and installed
- Confirmed 2026-10-27: local per firm, Tier 2 synthetic matters first, English only, individual developer at 40 hours/week, no hard deadline
- Machine probe 2026-10-27: Python 3.13.7, AMD Ryzen 3 7320U, approximately 5.83 GB visible RAM, 46.2 GB free on C:, Ollama installed, GPU not verified

## 3. Decisions Log
| Date | Decision | Reason | Status |
|---|---|---|---|
| 2026-10-27 | Two-tier knowledge base (public Tier 1, private Tier 2) | Public law is not confidential; client files are | Accepted |
| 2026-10-27 | Security enforced in code, not prompts | LLM cannot be trusted as boundary | Accepted |
| 2026-10-27 | Everything local in v1 | Avoid external leakage | Accepted |
| 2026-10-27 | Unprotected baselines only on synthetic data | Safety condition from paper | Accepted |
| 2026-10-27 | SQLite + NumPy local index for MVP | Keeps the prototype local and dependency-light while preserving a metadata-filtering interface | Accepted |
| 2026-10-27 | Ollama adapter with explicit local-runtime errors | Supports local generation without cloud fallback or silent success | Accepted |
| 2026-10-27 | Native PDF/DOCX extraction with quarantine on failure | Keeps private ingestion local and prevents unparseable content from entering the index | Accepted |
| 2026-10-27 | SQLite FTS5 plus deterministic dense hybrid retrieval | Supports legal exact-term search while retaining semantic baseline, with all scope filters applied before ranking | Accepted |
| 2026-10-27 | API requires known users and role-checks matter operations | Header identity alone must not grant access; membership changes must be immediate | Accepted |
| 2026-10-27 | Generated answers require authorized citations | Prevents untraceable local-model claims from being presented as supported research | Accepted |
| 2026-10-27 | Adversarial harness uses fictional data and no LLM | Measures retrieval disclosure independently and safely under the synthetic-data-only baseline rule | Accepted |
| | First court(s) for Tier 1 corpus | | **OPEN** |

## 4. Open Questions
1. First court(s) and corpus size? Open until Tier 1 work begins.
2. Hindi/Marathi support in v1? Deferred; English-only MVP.

## 5. Data Sources Register
| Source | Licence / terms checked? | Date | Notes |
|---|---|---|---|
| India Code | not yet | | |
| Supreme Court portal | not yet | | |
| High Court portals | not yet | | |
| eCourts | not yet | | |

## 6. Known Issues and Lessons
(Empty. Add entries like: `date | issue | cause | fix`.)

## 7. Experiment Records
Record each run: date, config file, model versions, hardware, dataset version, query set version, results location.

## 8. Glossary
- **Matter:** one legal case/engagement with its own access list
- **Tier 1 / Tier 2:** public law base / private matter workspace
- **URR:** unauthorized retrieval rate
- **CMDR:** cross-matter disclosure rate
- **TOCTOU:** time-of-check to time-of-use (permission changes between check and use)
- **Good law:** a judgment or statute not overruled, repealed or superseded
