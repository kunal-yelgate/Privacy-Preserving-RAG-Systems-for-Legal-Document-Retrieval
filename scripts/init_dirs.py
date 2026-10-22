"""
Bootstrap project directory tree and .gitkeep files for legal-rag.
"""
import os
from pathlib import Path

DIRECTORIES = [
    "data/originals",
    "data/processed",
    "data/chroma",
    "data/sqlite",
    "data/quarantine",
    "datasets/synthetic",
    "datasets/public_legal",
    "experiments/configurations",
    "experiments/scripts",
    "experiments/datasets",
    "experiments/reports",
    "scripts",
    "docs",
    "backend/app/api/v1",
    "backend/app/core",
    "backend/app/domain/models",
    "backend/app/schemas",
    "backend/app/services",
    "backend/app/repositories",
    "backend/app/infrastructure/database",
    "backend/app/infrastructure/vector_store",
    "backend/app/infrastructure/llm",
    "backend/app/infrastructure/embeddings",
    "backend/app/infrastructure/document_parsers",
    "backend/app/infrastructure/keyword_search",
    "backend/app/infrastructure/filesystem",
    "backend/app/middleware",
    "backend/tests/unit",
    "backend/tests/integration",
    "backend/tests/security",
    "backend/tests/fixtures",
]

def main():
    root = Path(__file__).resolve().parent.parent
    for d in DIRECTORIES:
        p = root / d
        p.mkdir(parents=True, exist_ok=True)
        gitkeep = p / ".gitkeep"
        if not gitkeep.exists() and not any(p.iterdir()):
            gitkeep.touch()
    print("Project directories created successfully.")

if __name__ == "__main__":
    main()
