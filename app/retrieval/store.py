import json
import re
import sqlite3
from dataclasses import asdict

import numpy as np

from app.security.filter import Chunk

_PUBLIC_QUERY_STOP_WORDS = {
    "a", "about", "after", "all", "also", "an", "and", "any", "are", "as", "at",
    "be", "because", "been", "before", "being", "by", "can", "case", "claim", "claims",
    "company", "court", "determine", "did", "do", "does", "for", "from", "had", "has", "have", "how",
    "if", "in", "into", "is", "it", "law", "legal", "matter", "may", "must", "of", "on",
    "or", "party", "plaintiff", "defendant", "question", "record", "should", "that", "the",
    "land", "order", "ordered", "prove", "proved", "proof", "their", "them", "then", "there",
    "these", "this", "those", "to", "under", "unlawful", "unlawfully", "was", "what",
    "when", "where", "whether", "which", "who", "will", "with", "would",
}


def _topic_terms(text: str) -> set[str]:
    terms: set[str] = set()
    for token in re.findall(r"[a-z0-9]+", text.casefold()):
        if token in _PUBLIC_QUERY_STOP_WORDS or len(token) < 3:
            continue
        if token.startswith("environment"):
            token = "environment"
        elif token.startswith(("deforest", "forest")):
            token = "forest"
        elif token.startswith(("clear", "clearing")):
            token = "clear"
        elif token.startswith("remed"):
            token = "remed"
        elif token.endswith("ies") and len(token) > 4:
            token = f"{token[:-3]}y"
        elif token.endswith("s") and len(token) > 4:
            token = token[:-1]
        terms.add(token)
    return terms


def _public_passage_matches_topic(query: str, text: str) -> bool:
    """Reject public passages that only share generic legal words with a query."""
    return len(_topic_terms(query) & _topic_terms(text)) >= 2


def _expand_public_query(query: str) -> str:
    """Add evidence vocabulary for forest-clearing and environmental-harm questions."""
    terms = _topic_terms(query)
    additions: list[str] = []
    if terms & {"forest", "tree", "clear", "deforestation"}:
        additions.append(
            "forest clearing permits approvals satellite imagery photographs land records "
            "official boundaries surveys company contractor equipment witness inspection"
        )
    if terms & {"environment", "damage", "harm", "wildlife", "erosion", "stream"}:
        additions.append(
            "environmental ecological assessment baseline habitat wildlife soil erosion "
            "stream flow water quality causation restoration remediation compensation monitoring"
        )
    return " ".join([query, *additions])


def _is_question_only_passage(text: str) -> bool:
    """Avoid treating embedded questions or issue headings as evidence."""
    normalized = text.strip().casefold()
    return normalized.endswith("?") or normalized.startswith(
        ("whether ", "what restoration ", "what remedy ", "what remedies ")
    )


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
        # FTS5 does not enforce a unique chunk_id. Rebuild this derived index
        # from the authoritative chunk table so reopening the DB cannot append
        # duplicate search rows and crowd relevant evidence out of top-k.
        self.connection.execute("DELETE FROM chunks_fts")
        self.connection.execute(
            """
            INSERT INTO chunks_fts(chunk_id, text)
            SELECT chunk_id, text FROM chunks WHERE status = 'active'
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
        # The local hash embedder is a deterministic offline baseline, not a
        # semantic model. Use it for private case passages, but require lexical
        # evidence before adding public legal material; otherwise unrelated
        # public authorities can crowd out the case's actual law.
        dense_private = self.search(
            query_embedding, matter_ids, top_k, include_public=False
        )
        dense_private = [
            chunk for chunk in dense_private if not _is_question_only_passage(chunk.text)
        ]
        lexical_private = self.search_lexical(
            query, matter_ids, top_k, include_public=False
        )
        lexical_private = [
            (chunk, score)
            for chunk, score in lexical_private
            if not _is_question_only_passage(chunk.text)
        ]
        public_query = _expand_public_query(query)
        lexical_public = (
            self.search_lexical(public_query, frozenset(), top_k * 2, include_public=True)
            if include_public
            else []
        )
        lexical_public = [
            (chunk, score)
            for chunk, score in lexical_public
            if _public_passage_matches_topic(public_query, chunk.text)
        ]
        lexical = [*lexical_private, *lexical_public]
        candidates = {chunk.chunk_id: chunk for chunk in dense_private}
        candidates.update({chunk.chunk_id: chunk for chunk, _ in lexical})
        dense_scores = _dense_scores(
            list(candidates.values()), query_embedding, self.connection, self.dimensions
        )
        lexical_scores = {chunk.chunk_id: score for chunk, score in lexical}
        ranked = sorted(
            candidates.values(),
            key=lambda chunk: (
                0.1 * dense_scores.get(chunk.chunk_id, 0.0)
                + 0.9 * lexical_scores.get(chunk.chunk_id, 0.0)
                if chunk.tier == "public"
                else alpha * dense_scores.get(chunk.chunk_id, 0.0)
                + (1.0 - alpha) * lexical_scores.get(chunk.chunk_id, 0.0)
            ),
            reverse=True,
        )
        private_ranked = [chunk for chunk in ranked if chunk.tier == "private"]
        public_ranked = [chunk for chunk in ranked if chunk.tier == "public"]
        if private_ranked and public_ranked:
            # Keep public authorities from crowding out the user's case record.
            public_limit = top_k // 2
            selected = [
                *private_ranked[: top_k - public_limit],
                *public_ranked[:public_limit],
            ]
            return selected[:top_k]
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
