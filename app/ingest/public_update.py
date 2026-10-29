import argparse
import sqlite3
from pathlib import Path

from app.ingest.public import PublicCorpusPipeline, PublicDocument, PublicSource
from app.retrieval.embeddings import LocalHashEmbedder
from app.retrieval.store import LocalIndex


def run_once(
    database_path: Path,
    source_id: str,
    source_title: str,
    license_name: str,
    source_url: str,
    document_path: Path,
) -> str:
    connection = sqlite3.connect(database_path)
    index = LocalIndex(connection, 384)
    pipeline = PublicCorpusPipeline(connection, index, LocalHashEmbedder(384))
    return pipeline.ingest(
        PublicSource(source_id, source_title, license_name),
        PublicDocument(
            document_id=f"{source_id}-{document_path.stem}",
            source_id=source_id,
            filename=document_path.name,
            media_type="application/pdf",
            source_url=source_url,
        ),
        document_path,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest one licensed public legal document.")
    parser.add_argument("document", type=Path)
    parser.add_argument("--database", type=Path, default=Path("data/legal_rag.sqlite3"))
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--source-title", required=True)
    parser.add_argument("--license", required=True, dest="license_name")
    parser.add_argument("--source-url", required=True)
    args = parser.parse_args()
    print(
        run_once(
            args.database,
            args.source_id,
            args.source_title,
            args.license_name,
            args.source_url,
            args.document,
        )
    )


if __name__ == "__main__":
    main()
