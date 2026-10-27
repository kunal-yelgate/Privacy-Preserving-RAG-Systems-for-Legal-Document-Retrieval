from dataclasses import dataclass
from math import sqrt

from app.eval.harness import HarnessResult


@dataclass(frozen=True)
class DisclosureSummary:
    configuration: str
    total_cases: int
    unauthorized_disclosures: int
    cross_matter_cases: int
    cross_matter_disclosures: int
    unauthorized_retrieval_rate: float
    cross_matter_disclosure_rate: float
    unauthorized_retrieval_rate_ci95: tuple[float, float] = (0.0, 0.0)
    cross_matter_disclosure_rate_ci95: tuple[float, float] = (0.0, 0.0)


def wilson_interval(successes: int, trials: int, z: float = 1.96) -> tuple[float, float]:
    if trials < 0 or successes < 0 or successes > trials:
        raise ValueError("successes must be between zero and trials")
    if trials == 0:
        return (0.0, 0.0)
    proportion = successes / trials
    denominator = 1 + z * z / trials
    centre = (proportion + z * z / (2 * trials)) / denominator
    margin = (
        z
        * sqrt(proportion * (1 - proportion) / trials + z * z / (4 * trials * trials))
        / denominator
    )
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def summarize(result: HarnessResult) -> DisclosureSummary:
    cross_matter = [case for case in result.cases if case.category != "authorized"]
    unauthorized = sum(case.disclosed_forbidden_matter for case in result.cases)
    cross_disclosures = sum(case.disclosed_forbidden_matter for case in cross_matter)
    return DisclosureSummary(
        configuration=result.configuration,
        total_cases=len(result.cases),
        unauthorized_disclosures=unauthorized,
        cross_matter_cases=len(cross_matter),
        cross_matter_disclosures=cross_disclosures,
        unauthorized_retrieval_rate=result.unauthorized_retrieval_rate,
        cross_matter_disclosure_rate=result.cross_matter_disclosure_rate,
        unauthorized_retrieval_rate_ci95=wilson_interval(unauthorized, len(result.cases)),
        cross_matter_disclosure_rate_ci95=wilson_interval(cross_disclosures, len(cross_matter)),
    )
