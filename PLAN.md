# PLAN.md — Local Legal RAG with Matter-Level Access Control

> Status: DRAFT v0.1 — built from the research paper. Items marked **(ASSUMPTION)** need confirmation.

## 1. Goal

Build a **locally-run RAG system for legal documents** where a user can only ever retrieve, see, or get answers from matters they are authorized for. Privacy and data-leak prevention come first; speed, accuracy and scalability are tuned *without ever weakening* the security rule.

**Core invariant (never violated):** `R(u, q) ⊆ A(u)` — every chunk given to the LLM must belong to the user's authorized set.

## 1A. Product Vision (from team)

Lawyers spend a large share of their time reading case material to understand a case and find proof for their claims. This platform is an **online legal research assistant for Indian law**: a RAG system over a knowledge base of Indian laws, regulations and judgments. A lawyer or user describes a case and receives **verified key points, claims, and supporting proof**, each tied to a source. New cases are added **daily / regularly**, and past cases are reused for future research and study.

**Users:** practicing lawyers (main), law students (secondary). **(ASSUMPTION)**

### Two-tier knowledge base (key design decision)

| Tier | Content | Who can read | Security rule |
|---|---|---|---|
| Tier 1 — Public law base | Statutes, regulations, public judgments, daily new cases | All signed-in users | Read-only, source-verified |
| Tier 2 — Private matter workspace | A lawyer's own case files, notes, evidence | Only users authorized for that matter | Matter-level authorization (the paper's core invariant) |

Answers may combine Tier 1 + the user's own Tier 2, never another user's Tier 2.
Updated invariant: `R(u, q) ⊆ Public ∪ A(u)`.

**Rule:** a user's private case is never promoted into the public base without explicit consent and redaction. "Past cases help the future" applies to public judgments, not to client files.

### What a case answer contains
1. Key issues and facts extracted from the user's query / uploaded case
2. Relevant statutes and sections
3. Supporting precedents with pinpoint citations (court, date, paragraph)
4. Claims mapped to the evidence that supports each one
5. Counter-arguments / adverse precedents
6. Verification status per claim: supported, partially supported, not found
7. Abstention when evidence is insufficient

### "Next-level" over a normal RAG

| Normal RAG | This project |
|---|---|
| Ranks only by similarity | Default-deny authorization filter before ranking |
| Trusts the prompt for safety | Security enforced in code, not in the prompt |
| Cloud embeddings / LLM | Everything local (embeddings, index, LLM) |
| Citations unchecked | Citation validator against authorized evidence only |
| Logs raw text | Logs IDs + policy decisions only |
| Accuracy only | Measured privacy–utility trade-off (URR, CMDR, Recall@k, latency) |

## 1.1 Leak Risks This Platform Targets

Existing online legal RAG platforms can leak a lawyer's case details and questions through: the platform operator, other organisations on the same system, logs and backups, or an external LLM/embedding provider.

Design response:
- Private data is never written into the shared public index or used to improve shared results.
- Every result carries a provenance label (public / private matter X).
- Queries, retrieved passages and answers are treated as confidential: no raw-text logging, no external LLM or embedding API.
- Check the licence and terms of use of every public data source before bulk ingestion.

**What "verified" means here:** each key point is traceable to a real, authorized source passage (citation validator). It does not mean legally correct; a lawyer must still review it.

## 2. Non-Goals (stated limitations)

- No formal differential privacy or cryptographic PIR.
- No defense against compromised OS, admin, or stolen credentials.
- No side-channel guarantees (latency / refusal wording).
- No claim that LLM answers are legally correct.

## 3. Constraints

- Windows dev machine, ~8 GB RAM, GPU unknown → small quantized LLM + compact embedding model.
- Unprotected baselines run **only** on synthetic fictional data in isolation.
- Fixed, recorded configuration for reproducibility.

## 4. Architecture

```
Documents (PDF/DOCX) → Extract (+OCR if scanned) → Normalize → Chunk
   → Metadata tagging (matterID, policy) → Local embeddings → Vector index + BM25 index

User query + identity → Auth service (permission snapshot + policy version)
   → Candidate retrieval (hybrid, matter-filtered in query)
   → Authorization filter (2nd check, default deny)
   → Rerank (authorized only) → Context revalidation (policy version re-read)
   → Local LLM → Citation validation / abstention → Answer
```

Security-critical components: **Authorization filter** and **Context revalidation**. UI/API are separate so these can be unit-tested alone.

## 5. Proposed Tech Stack (ASSUMPTION — final choices recorded during build)

| Layer | Choice | Why |
|---|---|---|
| API | FastAPI | Simple, async, testable |
| UI | Streamlit first, React later | Fast to build |
| Extraction | PyMuPDF, python-docx, Tesseract (OCR only if needed) | Local, light |
| Embeddings | bge-small-en-v1.5 or all-MiniLM-L6-v2 | Small, fast on CPU |
| Vector index | Qdrant (local) or LanceDB/Chroma | Payload filtering inside the query |
| Lexical search | SQLite FTS5 or rank_bm25 | Exact section numbers, case names |
| Reranker | bge-reranker-base (optional, toggle) | Accuracy boost, measure latency cost |
| LLM | Ollama / llama.cpp, 3B–4B model, Q4 quantized | Fits 8 GB RAM |
| Auth store | SQLite: users, matters, memberships, policy_version | Auditable, simple |
| Tests | pytest | Security unit tests |

## 6. Data Model

**Chunk metadata:** `documentID, matterID, page, section, type, date, jurisdiction, access_policy, chunk_id`
Missing/malformed metadata → **quarantine**, never indexed as searchable.

**Auth tables:** `users(user_id)`, `matters(matter_id)`, `memberships(user_id, matter_id)`, `policy_version` (incremented on any permission change).

## 7. Milestones (8 weeks, from paper)

### M1 — Skeleton (Week 1)
- [ ] Repo structure, config files, structured logging, pytest setup
- [ ] Local LLM runtime working (hello-world generation)
- [ ] Synthetic matter schema defined

### M2 — Ingestion (Week 2)
- [ ] PDF/DOCX extraction preserving page and section references
- [ ] OCR fallback for scanned PDFs
- [ ] Section-aware chunking (legal structure, with overlap)

### M3 — Indexing (Week 3)
- [ ] Local embeddings + vector index with metadata payload
- [ ] BM25/FTS index with same metadata
- [ ] Reproducibility test (same input → same index)

### M4 — Identity & Policy (Week 4)
- [ ] Users, matters, memberships, default-deny
- [ ] Permission snapshot + policy version
- [ ] Unit tests: positive, negative, malformed metadata, revoked access

### M5 — Secure Retrieval (Week 4–5)
- [ ] Metadata filter inside vector/lexical query
- [ ] Application-side second authorization check
- [ ] Context builder re-reads policy version (TOCTOU defense); restart or abort on change
- [ ] Test: denied chunks provably never reach model input

### M6 — Generation (Week 5)
- [ ] Evidence-only prompt, retrieved text labelled as untrusted data
- [ ] Citation validator; abstain when evidence is insufficient
- [ ] Safe logging (IDs, decisions, timestamps; no raw text)

### M7 — Adversarial Harness (Week 6)
- [ ] Synthetic multi-matter corpus with ground-truth labels
- [ ] Query sets: authorized, direct cross-matter, indirect/paraphrased, prompt-injection, unanswerable
- [ ] Pilot: ≥50 templates × 3 configs, up to 5 variants each

### M8 — Evaluation & Report (Weeks 7–8)
- [ ] Baseline A (conventional), Baseline B (local, no filter), Proposed
- [ ] Ablations (see §10), 95% CIs, McNemar / Wilcoxon
- [ ] Document failures; update paper with real results only

## 7A. Knowledge Base and Daily Update Pipeline

**Sources (ASSUMPTION, check licensing and terms of use for each):** India Code (central acts), Supreme Court and High Court judgment portals, eCourts, gazette notifications, regulator sites (SEBI, RBI, etc.).

**Daily update flow:**
```
Scheduler (daily) → Fetch new judgments/notifications → Deduplicate (hash + citation)
 → Parse (court, bench, date, case no., citation, statutes cited, paragraphs)
 → Chunk by paragraph/section → Embed incrementally → Add to Tier 1 index
 → Update citation graph → Version the index snapshot
```

**Legal-specific accuracy features:**
- **Pinpoint citations:** keep paragraph numbers so every claim can link to an exact passage
- **Citation graph:** which case cites, follows, distinguishes or overrules which
- **Good-law check:** flag overruled / amended / repealed material (statute amendment dates matter)
- **Court hierarchy weighting:** Supreme Court > High Court > lower courts, binding vs persuasive
- **Jurisdiction and date filters:** apply as metadata before ranking

**Scalability notes:** incremental indexing only (no full rebuild), index snapshots with rollback, ingest quarantine for failed parses, separate Tier 1 and Tier 2 indexes so private data is never mixed into the shared index.

## 8. Performance Plan

### Speed (targets are ASSUMPTIONS, to be validated on your hardware)
| Stage | Target | Technique |
|---|---|---|
| Retrieval + auth filter | < 300 ms | In-query filtering, HNSW index, small embedding model |
| Rerank (optional) | < 500 ms | Rerank only top 20–30 authorized candidates |
| Generation | 5–20 s | 3–4B Q4 model, limited context (4–6 chunks), streaming output |
| Embedding at ingest | Batch | Batched embedding, ingest runs offline |

Caching: cache embeddings of repeated queries, **keyed by user + policy_version** so a permission change invalidates the cache. Never share cached results across users.

### Accuracy
- Hybrid retrieval (lexical + semantic), tune `α` with normalized scores
- Legal-aware chunking by section/clause, not fixed size only
- Metadata-aware boosting (jurisdiction, date)
- Reranker on authorized candidates only
- Abstain on weak evidence instead of guessing
- Metrics: Recall@k, Precision@k, MRR, nDCG@k, citation existence and citation support (reported separately)

### Scalability
- Partition/filter index by `matterID` so queries only search authorized slices
- Incremental ingestion (add documents without full re-index)
- Pluggable vector store interface (swap Chroma → Qdrant → pgvector)
- Stateless API so it can scale to multiple workers later
- Stress test at 1K → 10K → 100K chunks; record latency, RAM, index size

## 9. Security Checklist (must pass before any release)

- [ ] Default-deny on missing/unknown permissions
- [ ] Two authorization checks (query-time and pre-context)
- [ ] Policy version re-read right before prompt build
- [ ] High relevance score can never override a denied permission
- [ ] Injected text in documents cannot expand scope
- [ ] Citations outside the authorized set are rejected
- [ ] Logs contain no raw prompts, passages, or answers
- [ ] Secrets are not in source code or logs
- [ ] Unprotected baseline never touches real data

## 10. Evaluation

**Metrics:** URR (unauthorized retrieval rate), CMDR (cross-matter disclosure rate), retrieval utility, citation correctness, answer quality (rubric, 2 annotators if possible), latency, peak memory, index size.

**Hypotheses:** H1 reduces URR; H2 reduces CMDR; H3 quantifies utility/latency cost.

**Ablations (one factor at a time):**
1. Filtering on vs off
2. In-query filter only vs in-query + app-side validation
3. Lexical vs semantic vs hybrid
4. Vary `α` and `k`
5. Citation validation on vs off
6. Reranker on vs off (speed vs accuracy)

## 11. Suggested Repo Layout

```
legal-rag/
├── app/
│   ├── api/            # FastAPI routes
│   ├── auth/           # users, matters, policy, snapshots
│   ├── ingest/         # extract, ocr, chunk, tag
│   ├── retrieval/      # embeddings, vector store, bm25, hybrid, rerank
│   ├── security/       # authz filter, context revalidation, citation validator
│   ├── generation/     # prompt builder, LLM client
│   └── logging/        # safe structured logs
├── eval/               # synthetic data, query sets, metrics, ablations
├── tests/              # security unit tests first
├── configs/            # models, params, versions
├── PLAN.md
└── README.md
```

## 12. Risks

| Risk | Mitigation |
|---|---|
| Local LLM too slow on 8 GB | Smaller quantized model, shorter context, report retrieval vs generation time |
| Utility drops after filtering | Check metadata quality first; **never relax permissions to gain utility** |
| Bad metadata leaks data | Quarantine + default deny |
| Prompt injection | Keep unauthorized content out of context; label evidence as untrusted |
| Scope creep | Finish M1–M6 before any "extra" features |

## 13. Future Upgrades (after core works)

- Role-based and document-level permissions (beyond matter-level)
- Graph-based legal context (HyRAG / LegalGraphRAG ideas)
- Query-side privacy (PIR-style) as a separate study
- Multi-user deployment with real auth (OAuth/JWT)
- Encryption at rest for index and backups

## 14. Open Questions

**Answered:** users are lawyers, case teams and students; corpus is Indian law plus private matter files; goal is to cut case-study time with verified key points and proof.

**Still open:**
1. Deployment model: installed locally per firm (strongest privacy), or one hosted platform with tenant isolation?
2. Scope of the first version: Tier 1 public search only, or Tier 1 + private Tier 2 workspace from the start?
3. Which courts first (Supreme Court only, or also one High Court)?
4. How many past judgments for the first corpus (e.g. 1K, 10K, more)?
5. Team size and weekly hours available?
6. Hard deadline (paper submission, college review)?
7. Must it support Hindi/Marathi documents?
