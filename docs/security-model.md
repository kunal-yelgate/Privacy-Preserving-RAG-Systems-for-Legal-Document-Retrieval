# Security Model & Privacy Boundaries

## 1. Principles of Offline & Local Privacy
The system enforces strict local privacy through defensive architecture:
1. **Zero External Cloud Egress**: All vector embeddings, document parsing, SQLite transactions, and generative inference execute strictly on the local machine (`127.0.0.1`).
2. **Deny-by-Default Access Control**: Access to documents, chunks, keyword indices, and conversation histories requires explicit matter membership.
3. **Pre-Retrieval Boundary Enforcement**: Matter boundary filters are enforced on the server prior to vector similarity queries and BM25 candidate scoring. Unfiltered candidates are never exposed to the client or to the LLM.
4. **Untrusted Evidence Boundary**: All document text is treated as raw data. The generation prompt instructs the LLM never to follow or execute commands found within documents.
5. **No Canary / Secret Leakage**: Multi-tenant canary strings embedded in synthetic test documents verify that Matter A's secrets never appear in Matter B's retrieval or answers.
6. **Redaction in Structured Logs**: The application logger automatically redacts authorization bearer tokens, passwords, and canary expressions matching `CANARY-[A-Z0-9\-]+`.

## 2. Authorization Hierarchy
- **Administrator**:
  - Full system visibility across all matters.
  - Can view immutable security audit logs and run adversarial benchmarks.
  - Can create and archive matters.
- **Researcher**:
  - Limited strictly to assigned matters.
  - Can ingest documents, execute hybrid searches, and engage in grounded research chat within authorized matters only.
  - Forbidden from enumerating or viewing metadata of unauthorized matters.
- **Viewer**:
  - Read-only access to search and answers within assigned matters. Cannot upload or delete documents.

## 3. Data Lifecycle & Deletion Guarantee
- **Original Document**: Stored in `data/originals/` under internal random ID.
- **Extracted Vectors**: ChromaDB collection `legal_rag_chunks` indexed with `matter_id`.
- **Structured Metadata**: SQLite table `documents` and `matter_memberships`.
- **Deletion Workflow**: Deleting a document removes its original file, deletes all associated vector chunks from ChromaDB, purges its tokens from the matter BM25 index, and deletes the SQLite record.
