# Windows 10/11 Setup Guide: Privacy-Preserving Offline Legal RAG

This guide provides step-by-step instructions for running the complete legal RAG platform locally on Windows without cloud services.

## Prerequisites
- **Operating System**: Windows 10 or Windows 11 (64-bit)
- **RAM**: Minimum 8 GB RAM
- **Python**: 3.11, 3.12, or 3.13 (with `python` available on PATH)
- **Node.js**: v18+ or v20+ with `npm`
- **Ollama for Windows**: Download and install from [ollama.com](https://ollama.com)

---

## 1. Preparing Local Inference Models in Ollama
Before entering offline operation, pull the small quantized models into your local machine:

```powershell
# In PowerShell:
ollama pull nomic-embed-text
ollama pull qwen2.5:1.5b
```

Verify that models are present locally:
```powershell
ollama list
```

Ensure the Ollama local daemon is running:
```powershell
# By default Ollama runs in background on Windows at http://127.0.0.1:11434
Invoke-RestMethod -Uri http://127.0.0.1:11434/api/tags
```

---

## 2. Setting Up Backend (Python / FastAPI)

1. Open PowerShell and navigate to the project directory:
   ```powershell
   cd c:\Users\yelga\Desktop\legal-rag
   ```

2. Create and activate a Python virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. Install backend dependencies:
   ```powershell
   pip install -r backend\requirements.txt
   ```

4. Generate synthetic test documents:
   ```powershell
   python scripts\generate_synthetic_docs.py
   ```

5. Run test suite to verify installation and privacy boundaries:
   ```powershell
   pytest backend\tests -v
   ```

6. Start FastAPI backend server:
   ```powershell
   python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

Backend will be available at:
- API Base: `http://127.0.0.1:8000/api/v1`
- OpenAPI Docs: `http://127.0.0.1:8000/docs`
- Health Probe: `http://127.0.0.1:8000/api/v1/health/ready`

---

## 3. Setting Up Frontend (Next.js / TypeScript)

1. Open a second PowerShell terminal in the `frontend` folder:
   ```powershell
   cd c:\Users\yelga\Desktop\legal-rag\frontend
   ```

2. Install dependencies:
   ```powershell
   npm install
   ```

3. Start development server:
   ```powershell
   npm run dev
   ```

Frontend will be accessible at:
- Web Application: `http://localhost:3000`

---

## 4. Default Demonstration Credentials
For local development and testing, default accounts are pre-seeded:
- **Administrator**:
  - Username: `admin`
  - Password: `AdminSecureOffline2026!`
- **Researcher 1**:
  - Username: `researcher1`
  - Password: `ResearcherPass2026!`
- **Researcher 2**:
  - Username: `researcher2`
  - Password: `ResearcherPass2026!`

---

## 5. Strict Offline Verification (Windows Firewall)
To verify that the system runs without internet access:
1. Disconnect Wi-Fi or disable network adapter:
   ```powershell
   Disable-NetAdapter -Name "Wi-Fi" -Confirm:$false
   ```
2. Navigate to `http://localhost:3000/research` and submit a query on `matter-101`.
3. Check the Security Center (`http://localhost:3000/security`) to verify 100% offline local generation.
