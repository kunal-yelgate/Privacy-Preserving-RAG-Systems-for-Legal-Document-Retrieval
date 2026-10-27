import json
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
class EvaluationReport:
    total_cases: int
    configurations: tuple[ConfigurationReport, ...]

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
    reports: list[ConfigurationReport] = []
    for name, retrieval, filtered in configurations:
        started = perf_counter()
        result = run_harness(
            evaluation_corpus,
            evaluation_cases,
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
    return EvaluationReport(len(evaluation_cases), tuple(reports))


def main() -> None:
    print(run_evaluation().as_json())


if __name__ == "__main__":
    main()
