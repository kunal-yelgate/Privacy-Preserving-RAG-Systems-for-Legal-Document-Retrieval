# PRD — Legal Research RAG with Matter-Level Privacy

> Version 0.1 (DRAFT). Items marked **(ASSUMPTION)** need team confirmation. Companion files: PLAN.md, ARCHITECTURE.md, DESIGN.md, RULES.md, MEMORY.md, TRACKER.md.

## 1. Summary
An online legal research assistant for **Indian law**. A lawyer describes a case and gets verified key points, claims and supporting proof, each tied to a source passage. The platform's differentiator is **privacy**: a user's private case data never leaks to other users, organisations, logs, or external AI services.

## 2. Problem
- Lawyers spend a large share of time reading case material and finding proof for claims.
- Existing online legal RAG platforms are not built around confidentiality: case details and queries can leak via the operator, other tenants, logs, or external LLM/embedding providers.

## 3. Target Users
| User | Need |
|---|---|
| Practising lawyer (primary) **(ASSUMPTION)** | Fast, trustworthy case research with checkable citations |
| Case team member | Shared access to one matter only |
| Law student (secondary) | Study from past judgments |
| Firm admin | Manage users and matter access |

## 4. Goals and Non-Goals
**Goals**
1. Answer case queries with key issues, statutes, precedents, claims and evidence, each with a pinpoint citation.
2. Enforce `R(u,q) ⊆ Public ∪ A(u)`: a user only ever sees public law plus their own authorized matters.
3. Keep the public knowledge base current with daily ingestion of new judgments and amendments.
4. Run fully local (embeddings, index, LLM) in the first version.
5. Produce measurable results (URR, CMDR, Recall@k, latency) for the research paper.

**Non-Goals (v1)**
- Legal advice or guaranteed-correct conclusions
- Formal differential privacy, cryptographic PIR, or defence against a compromised host/admin
- Hindi/Marathi support **(ASSUMPTION, confirm)**
- Public use by non-lawyers without disclaimers

## 5. Functional Requirements
| ID | Requirement | Priority |
|---|---|---|
| FR-1 | Sign in; each user has a permission snapshot of authorized matters | Must |
| FR-2 | Upload PDF/DOCX into a private matter workspace (OCR for scans) | Must |
| FR-3 | Search public law (Tier 1) with hybrid retrieval and filters (court, year, statute) | Must |
| FR-4 | Case query returns: issues, statutes, precedents, claims-to-evidence mapping, counter-arguments | Must |
| FR-5 | Every claim carries a pinpoint citation (court, date, paragraph) and a verification status: supported / partially supported / not found | Must |
| FR-6 | Abstain when evidence is insufficient | Must |
| FR-7 | Daily ingestion of new judgments and notifications into Tier 1 | Must |
| FR-8 | Good-law flags: overruled, amended, repealed | Should |
| FR-9 | Matter membership management (add/revoke user) with immediate effect | Must |
| FR-10 | Provenance label on every result: public vs private matter X | Must |
| FR-11 | Export answer with citations (PDF/DOCX) | Could |
| FR-12 | Admin audit view of security events (IDs only, no raw text) | Should |

## 6. Non-Functional Requirements
| Area | Requirement (targets are ASSUMPTIONS, validate on real hardware) |
|---|---|
| Security | Default-deny; two authorization checks; policy version re-read before prompt build; no raw text in logs; no external AI calls |
| Speed | Retrieval + filter under 300 ms; first token of answer within a few seconds; full answer 5-20 s on a 3-4B quantized model |
| Accuracy | Hybrid retrieval, reranking on authorized candidates, citation validator, abstention |
| Scalability | Incremental indexing; separate Tier 1 and Tier 2 indexes; stateless API; tested at 1K, 10K, 100K chunks |
| Reliability | Index snapshots with rollback; ingest quarantine for failed parses |
| Reproducibility | Fixed config and recorded model, hardware and library versions for all experiments |

## 7. Success Metrics
- **URR** (unauthorized retrieval rate): target 0 on the synthetic adversarial set
- **CMDR** (cross-matter disclosure rate): target 0 or clearly lower than baselines
- Recall@k, Precision@k, MRR, nDCG@k on authorized questions
- Citation existence rate and citation support rate (reported separately)
- Median and p95 latency, peak RAM, index size

## 8. Scope by Release
| Release | Contents |
|---|---|
| MVP (research prototype) | Tier 2 private matters on synthetic data, matter-level authz, hybrid retrieval, local LLM, citation validation, adversarial test harness |
| v1 | Tier 1 public corpus (one court first), daily ingestion, good-law flags, Next.js React UI |
| v2 | Document-level roles, citation graph, more courts, Indian-language support, real auth (OAuth/JWT), encryption at rest |

## 9. Risks and Dependencies
- Data licensing and terms of use for court/gazette sources (check before bulk ingestion)
- 8 GB RAM constraint limits model size and speed
- Metadata errors can defeat protection (quarantine bad metadata)
- Legal liability: UI must state that output is research support, not advice

## 10. Open Questions
See PLAN.md section 14 (deployment model, first-version scope, first court, corpus size, team hours, deadline, languages).
