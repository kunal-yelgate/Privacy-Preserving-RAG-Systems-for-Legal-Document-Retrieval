# Architecture Specification: Privacy-Preserving Offline Legal RAG

## 1. System Overview
The Veritas Legal RAG system is an offline-capable, matter-isolated legal research platform designed to operate on local consumer workstations (Windows 10/11 with 8 GB RAM) without external AI cloud dependencies, cloud vector stores, or mandatory telemetry.

```
+-------------------------------------------------------------------------+
|                        Next.js Frontend (React/TS)                      |
| Dashboard | Research Workspace | Document Ingestion | Security Center   |
+------------------------------------+------------------------------------+
                                     | Loopback HTTP (127.0.0.1:8000)
                                     v
+-------------------------------------------------------------------------+
|                         FastAPI Application Core                        |
|   API Router -> Validation -> Matter Authorization -> Domain Services   |
+--------+-------------------+--------------------+-----------------------+
         |                   |                    |
         v                   v                    v
+-----------------+ +-------------------+ +-------------------------------+
| Storage Layer   | | Ingestion & Search| | Local Inference Subsystem     |
| SQLite (WAL)    | | PyMuPDF Parser    | | Ollama Local Service          |
| Original Files  | | Chunking Service  | | - nomic-embed-text (Embed)    |
| ChromaDB Vector | | BM25 Okapi Index  | | - qwen2.5:1.5b (Evidence Gen) |
| Quarantine Root | | Reciprocal Fusion | | Loopback Enforced (127.0.0.1) |
+-----------------+ +-------------------+ +-------------------------------+
```

## 2. Ingestion Pipeline
1. **Validation**: Enforces allowed extensions (`.pdf`, `.txt`), file size bounds (default 25 MB max), and generates a cryptographic SHA-256 content hash.
2. **Safe Storage**: Stores original files in `data/originals/` using safe generated document IDs, neutralizing directory traversal attempts.
3. **Extraction**:
   - PDF: Uses `PyMuPDF` (`pymupdf`) to parse page-by-page text, preserving 1-indexed page references and detecting corrupted or encrypted documents.
   - TXT: Detects page markers or preserves page blocks.
4. **Chunking**: Uses `ChunkingService` with legal text normalization, sliding-window overlap, and metadata retention (`document_id`, `matter_id`, `page_number`, `chunk_index`, `classification`).
5. **Local Vectorization**: Generates 768-dimensional embeddings via local Ollama `nomic-embed-text` in small batches (batch size = 8) to avoid memory spikes.
6. **Indexing**:
   - Vector persistence in ChromaDB (`data/chroma/`).
   - Keyword indexing in memory-efficient BM25 Okapi with matter partitioning.
   - Lifecycle metadata record in SQLite (`data/sqlite/legal_rag.db`).

## 3. Hybrid Retrieval & Reciprocal Rank Fusion (RRF)
To ensure both conceptual semantic retrieval and precision keyword matching for legal statute sections and parties, the retrieval pipeline combines:
- Local cosine similarity search via ChromaDB with matter metadata filter.
- Keyword frequency matching via BM25 Okapi with matter partitioning.
- Reciprocal Rank Fusion scoring:
  $$RRF\_score(d) = \sum_{m \in \{semantic, bm25\}} \frac{1}{60 + rank_m(d)}$$

## 4. Evidence-Grounded Generation & Prompt Isolation
- Retrieves candidate passages strictly within authorized matter boundaries.
- Formats evidence blocks with explicit citation tags `[cite-1]`, `[cite-2]`.
- Implements strict prompt boundary: Retrieved text is treated as untrusted data, explicitly instructing the model to disregard embedded commands, overrides, or Canary extraction attempts.
- Verifies citation references: Hallucinated citation tags not present in the context are rejected.
- Strict Abstention: If no evidence is found or evidence is insufficient, the system abstains rather than hallucinating legal advice.
