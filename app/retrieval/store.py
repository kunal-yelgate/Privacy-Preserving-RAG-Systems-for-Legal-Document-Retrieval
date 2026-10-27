import json
import re
import sqlite3
from dataclasses import asdict

import numpy as np

from app.security.filter import Chunk


class LocalIndex:
    def __init__(self, connection: sqlite3.Connection, dimensions: int) -> None:
        self.connection = connection
        self.dimensions = dimensions
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY, document_id TEXT NOT NULL, text TEXT NOT NULL,
                tier TEXT NOT NULL, matter_id TEXT, court TEXT, date TEXT,
                paragraph INTEGER, status TEXT NOT NULL, embedding TEXT NOT NULL
            )
            """
        )
        self.connection.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts
            USING fts5(chunk_id UNINDEXED, text)
            """
        )
        self.connection.execute(
            """
            INSERT OR IGNORE INTO chunks_fts(chunk_id, text)
            SELECT chunk_id, text FROM chunks
            """
        )
        self.connection.commit()

    def add(self, chunk: Chunk, embedding: np.ndarray) -> None:
        if embedding.shape != (self.dimensions,):
            raise ValueError("embedding has incorrect dimensions")
        self.connection.execute(
            """
            INSERT OR REPLACE INTO chunks
            (chunk_id, document_id, text, tier, matter_id, court, date, paragraph, status, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (*asdict(chunk).values(), json.dumps(embedding.astype(float).tolist())),
        )
        self.connection.execute("DELETE FROM chunks_fts WHERE chunk_id = ?", (chunk.chunk_id,))
        self.connection.execute(
            "INSERT INTO chunks_fts(chunk_id, text) VALUES (?, ?)", (chunk.chunk_id, chunk.text)
        )
        self.connection.commit()

    def all_chunks(self) -> list[Chunk]:
        rows = self.connection.execute(
            """
            SELECT chunk_id, document_id, text, tier, matter_id, court, date,
                   paragraph, status
            FROM chunks
            WHERE status = 'active'
            """
        ).fetchall()
        return [Chunk(*row) for row in rows]

    def search(
        self,
        query_embedding: np.ndarray,
        matter_ids: frozenset[str],
        top_k: int,
        include_public: bool = True,
    ) -> list[Chunk]:
        if query_embedding.shape != (self.dimensions,):
            raise ValueError("query embedding has incorrect dimensions")
        predicates: list[str] = []
        parameters: list[str] = []
        if include_public:
            predicates.append("tier = 'public'")
        if matter_ids:
            predicates.append(f"matter_id IN ({','.join('?' for _ in matter_ids)})")
            parameters.extend(matter_ids)
        if not predicates:
            return []
        rows = self.connection.execute(
            f"""
            SELECT chunk_id, document_id, text, tier, matter_id, court, date, paragraph, status, embedding
            FROM chunks WHERE status = 'active' AND ({' OR '.join(predicates)})
            """,
            tuple(parameters),
        ).fetchall()
        scored: list[tuple[float, Chunk]] = []
        query_norm = np.linalg.norm(query_embedding)
        for row in rows:
            vector = np.asarray(json.loads(row[9]), dtype=float)
            denominator = query_norm * np.linalg.norm(vector)
            score = float(np.dot(query_embedding, vector) / denominator) if denominator else 0.0
            scored.append((score, Chunk(*row[:9])))
        return [
            chunk for _, chunk in sorted(scored, key=lambda item: item[0], reverse=True)[:top_k]
        ]

    def search_lexical(
        self,
        query: str,
        matter_ids: frozenset[str],
        top_k: int,
        include_public: bool = True,
    ) -> list[tuple[Chunk, float]]:
        match_query = _fts_match_query(query)
        if not match_query:
            return []
        predicates, parameters = _scope_predicates(matter_ids, include_public)
        if not predicates:
            return []
        rows = self.connection.execute(
            f"""
            SELECT c.chunk_id, c.document_id, c.text, c.tier, c.matter_id,
                   c.court, c.date, c.paragraph, c.status, bm25(chunks_fts) AS rank
            FROM chunks_fts
            JOIN chunks AS c ON c.chunk_id = chunks_fts.chunk_id
            WHERE chunks_fts MATCH ? AND c.status = 'active'
              AND ({' OR '.join(predicates)})
            ORDER BY rank
            LIMIT ?
            """,
            (match_query, *parameters, top_k),
        ).fetchall()
        raw_scores = [-float(row[9]) for row in rows]
        maximum = max(raw_scores, default=0.0)
        return [
            (Chunk(*row[:9]), score / maximum if maximum > 0 else 0.0)
            for row, score in zip(rows, raw_scores, strict=True)
        ]

    def search_hybrid(
        self,
        query: str,
        query_embedding: np.ndarray,
        matter_ids: frozenset[str],
        top_k: int,
        alpha: float = 0.7,
        include_public: bool = True,
    ) -> list[Chunk]:
        if not 0.0 <= alpha <= 1.0:
            raise ValueError("alpha must be between 0 and 1")
        dense_chunks = self.search(
            query_embedding, matter_ids, top_k, include_public=include_public
        )
        lexical = self.search_lexical(query, matter_ids, top_k, include_public=include_public)
        dense_scores = _dense_scores(
            dense_chunks, query_embedding, self.connection, self.dimensions
        )
        lexical_scores = {chunk.chunk_id: score for chunk, score in lexical}
        candidates = {chunk.chunk_id: chunk for chunk in dense_chunks}
        candidates.update({chunk.chunk_id: chunk for chunk, _ in lexical})
        ranked = sorted(
            candidates.values(),
            key=lambda chunk: alpha * dense_scores.get(chunk.chunk_id, 0.0)
            + (1.0 - alpha) * lexical_scores.get(chunk.chunk_id, 0.0),
            reverse=True,
        )
        return ranked[:top_k]


def _scope_predicates(
    matter_ids: frozenset[str], include_public: bool
) -> tuple[list[str], list[str]]:
    predicates: list[str] = []
    parameters: list[str] = []
    if include_public:
        predicates.append("c.tier = 'public'")
    if matter_ids:
        predicates.append(f"c.matter_id IN ({','.join('?' for _ in matter_ids)})")
        parameters.extend(matter_ids)
    return predicates, parameters


def _fts_match_query(query: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9_]+", query.lower())
    return " OR ".join(f'"{token.replace(chr(34), chr(34) * 2)}"' for token in tokens)


def _dense_scores(
    chunks: list[Chunk],
    query_embedding: np.ndarray,
    connection: sqlite3.Connection,
    dimensions: int,
) -> dict[str, float]:
    if not chunks:
        return {}
    placeholders = ",".join("?" for _ in chunks)
    rows = connection.execute(
        f"SELECT chunk_id, embedding FROM chunks WHERE chunk_id IN ({placeholders})",
        tuple(chunk.chunk_id for chunk in chunks),
    ).fetchall()
    query_norm = np.linalg.norm(query_embedding)
    scores: dict[str, float] = {}
    for chunk_id, encoded in rows:
        vector = np.asarray(json.loads(encoded), dtype=float)
        if vector.shape != (dimensions,):
            continue
        denominator = query_norm * np.linalg.norm(vector)
        cosine = float(np.dot(query_embedding, vector) / denominator) if denominator else 0.0
        scores[chunk_id] = (cosine + 1.0) / 2.0
    return scores
