# TRACKER — Tasks, Milestones, Risks

> Status keys: [ ] todo, [~] in progress, [x] done, [!] blocked. Update when status changes. Dates and owners are placeholders until the team confirms its schedule.

## Overview
| Milestone | Week | Status | Owner |
|---|---|---|---|
| M0 Planning docs | 0 | [x] | |
| M1 Skeleton | 1 | [~] | |
| M2 Ingestion (Tier 2) | 2 | [ ] | |
| M3 Indexing | 3 | [x] | |
| M4 Identity and policy | 4 | [x] | |
| M5 Secure retrieval | 4-5 | [x] | |
| M6 Generation and citations | 5 | [ ] | |
| M7 Adversarial Harness | 6 | [x] | |
| M8 Evaluation and report | 7-8 | [x] | |
| M9 Tier 1 public corpus + daily updates (post-MVP) | 9+ | [x] | |

## M0 Planning
- [x] Research paper draft
- [x] plan.md
- [x] PRD, ARCHITECTURE, DESIGN, RULES, MEMORY, TRACKER
- [x] Answer open questions (deployment model, scope, first court, deadline)
- [x] Confirm hardware (RAM, GPU) and record in MEMORY.md

## M1 Skeleton
- [x] Repo structure and config files
- [x] FastAPI app with health endpoint
- [x] Structured safe logging
- [x] pytest, ruff, black set up
- [~] Local LLM runtime adapter; model download and test prompt remain
- [ ] Synthetic matter schema defined

## M2 Ingestion (Tier 2)
- [x] PDF/DOCX extraction with page and section refs
- [!] OCR fallback for scanned PDFs (blocked until a local Tesseract runtime is installed)
- [x] Section-aware chunking
- [x] Metadata tagging and quarantine of bad metadata

## M3 Indexing
- [x] Choose and record embedding model
- [x] Choose and record vector store (behind interface)
- [x] Dense index with metadata payload
- [x] BM25/FTS index
- [x] Reproducibility test (same input, same index)

## M4 Identity and Policy
- [x] users, matters, memberships, policy_version tables
- [x] Permission snapshot
- [x] Default-deny rules
- [x] Unit tests: allowed, denied, malformed, revoked
- [x] API matter creation, membership management, and known-user authentication

## M5 Secure Retrieval
- [x] In-query metadata filter
- [x] App-side authorization filter
- [x] Context builder with policy_version revalidation
- [x] Test: denied chunks never reach model input
- [x] Hybrid score normalization and configurable alpha
- [x] End-to-end API tests proving unauthorized matter content is excluded

## M6 Generation
- [x] Evidence-only prompt, untrusted-document labelling
- [x] Citation validator
- [x] Abstention on weak evidence
- [x] Local Ollama generation with explicit unavailable-runtime errors
- [x] Citation validation connected to generated answers
- [x] Streaming output after authorization/context validation

## M7 Adversarial Harness
- [x] Synthetic multi-matter corpus with ground truth
- [x] Query sets: authorized, direct, indirect, injection, unanswerable
- [x] Pilot: 50 templates, 3 configurations
- [x] Labelled disclosure rubric and URR/CMDR summary

## M8 Evaluation and Report
- [x] Baseline A, Baseline B, Proposed
- [x] Ablations (filter and retrieval type)
- [x] URR, CMDR with 95% CI
- [x] Latency
- [x] RAM, index size
- [ ] Update paper with real results only

## M9 Tier 1 Public Corpus (post-MVP)
- [x] Check licence of each source (required source metadata)
- [x] Parser: court, date, case no., citation, paragraphs (existing page/paragraph extraction)
- [x] Daily scheduler/update entry point, dedupe, incremental indexing
- [x] Index snapshots and rollback
- [ ] Good-law flags and citation graph
- [x] Combined Tier 1 + Tier 2 retrieval through the existing scoped hybrid query

## UI Track
- [x] Streamlit prototype: sign in, ask, answer, source viewer
- [x] Matter files and members pages (matter document view and API-backed uploads)
- [x] Audit page (request/evidence details in the source view)
- [x] Disclaimer text "research support, not legal advice"

## Risks
| Risk | Impact | Mitigation | Status |
|---|---|---|---|
| 8 GB RAM too small for chosen LLM | Slow or crash | Smaller quantized model, shorter context | Open |
| Metadata errors leak data | High | Quarantine, default deny, tests | Open |
| Source licence blocks ingestion | Medium | Check terms first, start with permitted sources | Open |
| Scope creep | Medium | Finish M1-M6 before extras | Open |
| Time shortage (paper deadline) | High | Keep MVP to Tier 2 on synthetic data | Open |

## Changelog
- 2026-10-27: Planning docs created.
- 2026-10-27: Confirmed local MVP environment and implemented security-first M1-M6 foundation.
- 2026-10-27: Added SQLite FTS5 lexical retrieval, normalized hybrid ranking, and reproducibility tests.
- 2026-10-27: Added API matter management, secure uploads, known-user authentication, and end-to-end M4/M5 tests.
- 2026-10-27: Integrated local Ollama generation, citation-gated answers, abstention, and NDJSON streaming.
- 2026-10-27: Added 50-case synthetic adversarial harness with three hybrid configurations and disclosure metrics.
- 2026-10-27: Added comparative M8 evaluation with isolated unrestricted baselines, filtered hybrid proposal, latency, and Wilson 95% confidence intervals.
- 2026-10-27: Added M8 ablations plus peak-memory and SQLite index-size reporting.
- 2026-10-27: Added licensed public-source ingestion with content deduplication, snapshots, rollback, and a one-shot update CLI.
- 2026-10-27: Added the Streamlit API client for matter selection, secure querying, evidence/source viewing, and uploads.
