from app.eval.harness import run_harness
from app.eval.metrics import summarize
from app.eval.report import run_evaluation
from app.eval.synthetic import build_cases, build_corpus


def test_synthetic_harness_has_required_query_categories() -> None:
    cases = build_cases()
    assert len(cases) == 50
    assert {case.category for case in cases} == {
        "authorized",
        "direct-cross-matter",
        "indirect-cross-matter",
        "prompt-injection",
        "unanswerable",
    }


def test_proposed_filter_has_zero_cross_matter_disclosure() -> None:
    result = run_harness(build_corpus(), build_cases(), alpha=0.7)
    assert result.unauthorized_retrieval_rate == 0.0
    assert result.cross_matter_disclosure_rate == 0.0


def test_three_hybrid_configurations_are_reproducible() -> None:
    corpus = build_corpus()
    cases = build_cases()
    first = [run_harness(corpus, cases, alpha=alpha) for alpha in (0.3, 0.7, 1.0)]
    second = [run_harness(corpus, cases, alpha=alpha) for alpha in (0.3, 0.7, 1.0)]
    assert [result.cases for result in first] == [result.cases for result in second]
    assert all(result.unauthorized_retrieval_rate == 0.0 for result in first)


def test_disclosure_summary_has_labelled_counts() -> None:
    summary = summarize(run_harness(build_corpus(), build_cases(), alpha=0.7))
    assert summary.total_cases == 50
    assert summary.cross_matter_cases == 40
    assert summary.unauthorized_disclosures == 0
    assert summary.cross_matter_disclosure_rate == 0.0
    assert summary.unauthorized_retrieval_rate_ci95[0] == 0.0
    assert summary.unauthorized_retrieval_rate_ci95[1] > 0.0
    assert summary.cross_matter_disclosure_rate_ci95[0] == 0.0
    assert summary.cross_matter_disclosure_rate_ci95[1] > 0.0


def test_comparative_evaluation_reports_baselines_and_proposed_system() -> None:
    report = run_evaluation()
    assert report.total_cases == 50
    assert [configuration.name for configuration in report.configurations] == [
        "baseline-a-lexical-unrestricted",
        "baseline-b-dense-unrestricted",
        "proposed-filtered-hybrid",
    ]
    assert report.configurations[-1].summary.cross_matter_disclosure_rate == 0.0
    assert report.configurations[0].summary.cross_matter_disclosure_rate > 0.0
    assert report.as_dict()["configurations"][0]["summary"]["total_cases"] == 50
