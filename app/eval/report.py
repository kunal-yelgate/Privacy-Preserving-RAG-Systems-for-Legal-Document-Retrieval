import json
import tracemalloc
from dataclasses import asdict, dataclass
from time import perf_counter

from app.eval.harness import run_harness
from app.eval.metrics import DisclosureSummary, summarize
from app.eval.synthetic import SyntheticCase, SyntheticCorpus, build_cases, build_corpus


@dataclass(frozen=True)
class ConfigurationReport:
    name: str
    retrieval: str
    filtered: bool
    summary: DisclosureSummary
    elapsed_ms: float


@dataclass(frozen=True)
class ResourceReport:
    peak_memory_bytes: int
    index_size_bytes: int


@dataclass(frozen=True)
class EvaluationReport:
    total_cases: int
    configurations: tuple[ConfigurationReport, ...]
    ablations: tuple[ConfigurationReport, ...] = ()
    resources: ResourceReport | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "total_cases": self.total_cases,
            "configurations": [
                {
                    **asdict(configuration),
                    "summary": asdict(configuration.summary),
                }
                for configuration in self.configurations
            ],
            "ablations": [
                {
                    **asdict(configuration),
                    "summary": asdict(configuration.summary),
                }
                for configuration in self.ablations
            ],
            "resources": asdict(self.resources) if self.resources else None,
        }

    def as_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2, sort_keys=True)


def run_evaluation(
    corpus: SyntheticCorpus | None = None,
    cases: list[SyntheticCase] | None = None,
    top_k: int = 3,
    alpha: float = 0.7,
) -> EvaluationReport:
    """Run all comparative configurations on synthetic data only.

    The unrestricted configurations intentionally bypass authorization and must never
    receive real documents. ``build_corpus`` is the default isolated fixture.
    """
    evaluation_corpus = corpus or build_corpus()
    evaluation_cases = cases or build_cases()
    configurations = (
        ("baseline-a-lexical-unrestricted", "lexical", False),
        ("baseline-b-dense-unrestricted", "dense", False),
        ("proposed-filtered-hybrid", "hybrid", True),
    )
    reports = _run_configurations(evaluation_corpus, evaluation_cases, configurations, top_k, alpha)
    ablation_definitions = (
        ("ablation-unfiltered-hybrid", "hybrid", False),
        ("ablation-filtered-lexical", "lexical", True),
        ("ablation-filtered-dense", "dense", True),
    )
    ablations = _run_configurations(
        evaluation_corpus, evaluation_cases, ablation_definitions, top_k, alpha
    )
    return EvaluationReport(
        len(evaluation_cases),
        tuple(reports),
        tuple(ablations),
        _measure_resources(evaluation_corpus),
    )


def _run_configurations(
    corpus: SyntheticCorpus,
    cases: list[SyntheticCase],
    configurations: tuple[tuple[str, str, bool], ...],
    top_k: int,
    alpha: float,
) -> list[ConfigurationReport]:
    reports: list[ConfigurationReport] = []
    for name, retrieval, filtered in configurations:
        started = perf_counter()
        result = run_harness(
            corpus,
            cases,
            alpha=alpha,
            top_k=top_k,
            retrieval=retrieval,
            enforce_scope=filtered,
        )
        reports.append(
            ConfigurationReport(
                name=name,
                retrieval=retrieval,
                filtered=filtered,
                summary=summarize(result),
                elapsed_ms=(perf_counter() - started) * 1000,
            )
        )
    return reports


def _measure_resources(corpus: SyntheticCorpus) -> ResourceReport:
    connection = corpus.index.connection
    page_count, page_size = (
        connection.execute("PRAGMA page_count").fetchone()[0],
        connection.execute("PRAGMA page_size").fetchone()[0],
    )
    tracemalloc.start()
    corpus.index.all_chunks()
    _, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return ResourceReport(
        peak_memory_bytes=peak_memory,
        index_size_bytes=page_count * page_size,
    )


def main() -> None:
    print(run_evaluation().as_json())


if __name__ == "__main__":
    main()
