# Troubleshooting Guide: Common Issues and Resolutions

## 1. Ollama Connection Error (`Cannot connect to local Ollama`)
- **Symptom**: `503 Service Unavailable` or `Cannot connect to local Ollama at http://127.0.0.1:11434`.
- **Cause**: The local Ollama daemon is not running on your machine.
- **Resolution**:
  1. Open PowerShell and start Ollama:
     ```powershell
     ollama serve
     ```
  2. Test local connectivity:
     ```powershell
     Invoke-RestMethod -Uri http://127.0.0.1:11434/api/tags
     ```

## 2. Model Not Found (`Ollama embedding failed for model 'nomic-embed-text'`)
- **Symptom**: Ingestion or chat reports model is missing.
- **Cause**: Required models have not been pulled into local Ollama storage.
- **Resolution**:
  ```powershell
  ollama pull nomic-embed-text
  ollama pull qwen2.5:1.5b
  ```

## 3. High Memory Usage on 8 GB RAM Machine
- **Symptom**: Slow inference or Windows memory pressure warning.
- **Resolution**:
  1. Ensure only one Ollama model is active in memory at a time.
  2. Keep `EMBEDDING_BATCH_SIZE=8` (default in `.env`).
  3. Ensure `RETRIEVAL_TOP_K=4` or `5` to avoid feeding large context windows to the LLM.

## 4. Scanned PDF Contains No Digital Text
- **Symptom**: `DocumentExtractionError: PDF contains no selectable text.`
- **Cause**: The uploaded file is a scanned flat image without an embedded OCR text layer.
- **Resolution**: Provide digitally born PDFs or text documents, or enable optional local OCR if configured.

## 5. Port Conflict on 8000 or 3000
- **Symptom**: `Error: listen EADDRINUSE: address already in use 127.0.0.1:8000` or `3000`.
- **Resolution**:
  Check running processes and terminate old instances:
  ```powershell
  Get-Process | Where-Object { $_.ProcessName -match "python|node" }
  ```

## 6. Frontend `TypeError: Failed to fetch` (`client.ts @ fetch`)
- **Symptom**: Red runtime alert or banner stating `Failed to fetch` or `Unable to reach local backend at http://127.0.0.1:8000/api/v1`.
- **Cause**: The Next.js frontend is attempting to call the REST API while the FastAPI backend service has not yet been started or is restarting.
- **Resolution**:
  1. Open a PowerShell terminal at the repository root and start the backend:
     ```powershell
     cd c:\Users\yelga\Desktop\legal-rag
     .\venv\Scripts\Activate.ps1
     .\venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
     ```
  2. Verify backend readiness in your browser at [`http://127.0.0.1:8000/api/v1/health`](http://127.0.0.1:8000/api/v1/health).
  3. Click the **"Reconnect Backend"** or **"Retry"** button in the web UI.

## 7. `No module named uvicorn`
- **Symptom**: PowerShell outputs `python.exe: No module named uvicorn`.
- **Cause**: The terminal is using an unpopulated Python virtual environment (e.g., an empty `backend\venv` created inside the backend subdirectory) instead of the project root's `.\venv` where dependencies are installed.
- **Resolution**:
  Run from the project root using the project virtual environment:
  ```powershell
  cd c:\Users\yelga\Desktop\legal-rag
  .\venv\Scripts\Activate.ps1
  pip install -r backend\requirements.txt
  .\venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
  ```

