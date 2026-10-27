from dataclasses import dataclass

from app.eval.synthetic import SyntheticCase, SyntheticCorpus


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    category: str
    retrieved_matter_ids: frozenset[str]
    disclosed_forbidden_matter: bool
    retrieved_anything: bool


@dataclass(frozen=True)
class HarnessResult:
    configuration: str
    cases: tuple[CaseResult, ...]

    @property
    def unauthorized_retrieval_rate(self) -> float:
        if not self.cases:
            return 0.0
        return sum(case.disclosed_forbidden_matter for case in self.cases) / len(self.cases)

    @property
    def cross_matter_disclosure_rate(self) -> float:
        cross_matter = [case for case in self.cases if case.category != "authorized"]
        if not cross_matter:
            return 0.0
        return sum(case.disclosed_forbidden_matter for case in cross_matter) / len(cross_matter)


def run_harness(
    corpus: SyntheticCorpus,
    cases: list[SyntheticCase],
    alpha: float,
    top_k: int = 3,
    retrieval: str = "hybrid",
    enforce_scope: bool = True,
) -> HarnessResult:
    if retrieval not in {"dense", "lexical", "hybrid"}:
        raise ValueError("retrieval must be dense, lexical, or hybrid")
    results: list[CaseResult] = []
    all_matters = frozenset(
        chunk.matter_id for chunk in corpus.index.all_chunks() if chunk.matter_id
    )
    for case in cases:
        snapshot = corpus.snapshots[case.user_id]
        matter_ids = snapshot.matter_ids if enforce_scope else all_matters
        if retrieval == "dense":
            chunks = corpus.index.search(
                corpus.embedder.embed(case.question),
                matter_ids,
                top_k,
                include_public=False,
            )
        elif retrieval == "lexical":
            chunks = [
                chunk
                for chunk, _ in corpus.index.search_lexical(
                    case.question, matter_ids, top_k, include_public=False
                )
            ]
        else:
            chunks = corpus.index.search_hybrid(
                case.question,
                corpus.embedder.embed(case.question),
                matter_ids,
                top_k,
                alpha=alpha,
                include_public=False,
            )
        matter_ids = frozenset(chunk.matter_id for chunk in chunks if chunk.matter_id)
        results.append(
            CaseResult(
                case.query_id,
                case.category,
                matter_ids,
                case.forbidden_matter_id in matter_ids if case.forbidden_matter_id else False,
                bool(chunks),
            )
        )
    return HarnessResult(
        f"{retrieval}, filtered={enforce_scope}, alpha={alpha:.1f}", tuple(results)
    )
