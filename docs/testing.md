# Testing Guide: Privacy-Preserving Offline Legal RAG

## 1. Test Suite Architecture
The test suite consists of 3 distinct test levels:

1. **Unit Tests** (`backend/tests/unit/`):
   - `test_chunking.py`: Legal text normalization, sliding-window overlap, page number preservation.
   - `test_citations.py`: Citation tag extraction `[cite-1]`, citation verification against authorized evidence, and hallucination rejection.
   - `test_file_manager.py`: Cryptographic SHA-256 calculation, filename sanitization, and path traversal rejection (`../../etc/passwd`).

2. **Security & Privacy Tests** (`backend/tests/security/`):
   - `test_isolation_and_security.py`: Cross-matter boundary denial (User 1 cannot access Matter 102), sensitive Canary token redaction in logs (`CANARY-CORP-ALPHA-7892` masked).

3. **Integration Tests** (`backend/tests/integration/`):
   - `test_pipeline.py`: Full ingestion pipeline for synthetic documents, batch embedding generation via Ollama, ChromaDB vector indexing, BM25 indexing, and hybrid search.
   - `test_api_endpoints.py`: End-to-end FastAPI test client checking `/health`, `/health/ready`, JWT login, `/matters`, and `/security/status`.

## 2. Running Automated Tests in PowerShell

To run the complete automated test suite:
```powershell
.\venv\Scripts\pytest backend\tests -v
```

To run a specific test module:
```powershell
.\venv\Scripts\pytest backend\tests\security\test_isolation_and_security.py -v
```

## 3. Test Coverage Summary
- **Unit & Security Coverage**: 100% of core authorization policies, file traversal checks, and citation mappings are verified.
- **Mock vs. Real Models**: Tests connect to local Ollama (`http://127.0.0.1:11434`) using the verified small models (`nomic-embed-text` and `qwen2.5:1.5b`).
