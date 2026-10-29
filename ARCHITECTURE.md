# ARCHITECTURE

> Version 0.1 (DRAFT). Stack choices are ASSUMPTIONS until recorded in configs/ at build time.

## 1. Principles
1. **Security in code, not prompts.** The LLM is never the security boundary.
2. **Default deny.** Missing or malformed permission or metadata means no access.
3. **Unauthorized content never enters the model context.**
4. **Private data never enters the shared index.**
5. **Everything local** in v1: embeddings, index, LLM.

## 2. System Overview
```
                         ┌───────────────────────────┐
  Browser UI  ──HTTPS──► │  API (FastAPI)            │
                         │  authN, request IDs       │
                         └────────────┬──────────────┘
                                      │ identity
                         ┌────────────▼──────────────┐
                         │ Auth / Policy Service     │  SQLite: users, matters,
                         │ permission snapshot +     │  memberships, policy_version
                         │ policy_version            │
                         └────────────┬──────────────┘
                                      │ authorized scope
        ┌─────────────────────────────▼─────────────────────────────┐
        │ Retrieval Orchestrator                                    │
        │  1. Query rewrite (local)                                 │
        │  2. Hybrid search: Tier 1 (public) + Tier 2 (matter-filtered)
        │  3. Authorization filter (2nd check, default deny)        │
        │  4. Rerank (authorized only)                              │
        │  5. Context revalidation (re-read policy_version)         │
        └─────────────────────────────┬─────────────────────────────┘
                                      │ authorized chunks only
                         ┌────────────▼──────────────┐
                         │ Generation (local LLM)    │
                         │ evidence-only prompt      │
                         └────────────┬──────────────┘
                                      │
                         ┌────────────▼──────────────┐
                         │ Citation Validator /      │
                         │ Abstention                │
                         └────────────┬──────────────┘
                                      ▼
                                   Answer
```

## 3. Components
| Component | Responsibility | Notes |
|---|---|---|
| UI | Query box, results, citations, matter selector, admin pages | Next.js React frontend |
| API | Routes, authentication, request IDs, rate limits | FastAPI, stateless |
| Auth/Policy | Users, matters, memberships, `policy_version` | Tiny and unit-tested separately |
| Ingestion (Tier 2) | Extract, OCR, chunk, tag metadata, embed | Per-matter, user-triggered |
| Ingestion (Tier 1) | Daily fetch, dedupe, parse, chunk, embed, update citation graph | Scheduler, quarantine on parse failure |
| Vector index | Dense search with metadata payload filter | Qdrant/LanceDB/Chroma behind an interface |
| Lexical index | BM25/FTS for section numbers, case names | SQLite FTS5 or rank_bm25 |
| Reranker | Reorder top 20-30 authorized candidates | Optional toggle |
| Context builder | Final authz check, policy version re-read, prompt assembly | Security-critical |
| LLM runtime | Local quantized 3-4B model | Ollama or llama.cpp |
| Citation validator | Check each citation exists in the authorized evidence set | Security-critical |
| Safe logger | IDs, decisions, timestamps, error categories only | No raw text |

## 4. Two-Tier Data Layout
| | Tier 1 Public | Tier 2 Private |
|---|---|---|
| Content | Statutes, regulations, judgments | Matter files, notes |
| Index | Shared index | Separate index/collection per matter or per firm |
| Readers | All signed-in users | Matter members only |
| Writers | Ingestion pipeline only | Authorized uploaders |
| Promotion between tiers | Not allowed without explicit consent and redaction | |

Invariant: `R(u,q) ⊆ Public ∪ A(u)`.

## 5. Data Model
**Chunk metadata**
`chunk_id, document_id, tier, matter_id (Tier 2), court, date, case_no, citation, page, paragraph, section, jurisdiction, doc_type, access_policy, status (active/quarantined), good_law_flag`

**Auth tables**
`users(user_id, display_name)`, `matters(matter_id, owner_id)`, `memberships(user_id, matter_id, role)`, `policy_state(version)`

**Citation graph (v1)**
`edges(citing_case, cited_case, relation: follows | distinguishes | overrules | cites)`

## 6. Key Flows
### 6.1 Query
1. API authenticates user, gets permission snapshot and `policy_version = N`.
2. Retriever searches Tier 1 and authorized Tier 2 with metadata filter in the query.
3. App-side filter drops any chunk not in `Public ∪ A(u)`.
4. Rerank, then context builder re-reads `policy_version`. If not N, restart or abort.
5. LLM generates from question + authorized evidence only.
6. Citation validator rejects citations outside the evidence set; weak evidence triggers abstention.
7. Log request ID, policy decisions, document IDs. No raw text.

### 6.2 Daily Tier 1 update
Scheduler → fetch → dedupe (hash + citation) → parse → chunk by paragraph → embed incrementally → add to index → update citation graph → snapshot index version.

### 6.3 Permission revocation
Membership removed → `policy_version` incremented → in-flight requests restart or abort → caches keyed by `(user, policy_version)` become invalid.

## 7. Performance and Scalability
- Filter inside the vector query so only authorized slices are searched
- Small embedding model, HNSW index, batched ingestion
- Rerank only top 20-30; 4-6 chunks in context
- Stream LLM output
- Cache query embeddings keyed by user and `policy_version`; never share across users
- Vector store behind an interface so it can be swapped
- Stateless API workers; index snapshots with rollback

## 8. Security Architecture
| Threat | Control |
|---|---|
| Cross-matter retrieval | In-query filter + app-side check + context revalidation |
| Stale permissions (TOCTOU) | Re-read `policy_version` before prompt build |
| Prompt injection in documents | Unauthorized content never enters context; retrieved text labelled untrusted |
| Fabricated citations | Citation validator against authorized evidence |
| Log leakage | No raw prompts, passages or answers in logs; restricted log access |
| Bad metadata | Quarantine, default deny |
| External leakage | No external LLM, embedding or telemetry calls |

Out of scope: compromised OS, malicious admin, stolen credentials, side-channel inference, model inversion.

## 9. Repo Layout
```
my-project/
├── app/ (api, auth, ingest, retrieval, security, generation, logging)
├── eval/ (synthetic data, query sets, metrics, ablations)
├── tests/
├── configs/
└── docs: PLAN, PRD, ARCHITECTURE, DESIGN, RULES, MEMORY, TRACKER
```

## 10. Architecture Decisions Log
Record each decision in MEMORY.md (what, why, date).
