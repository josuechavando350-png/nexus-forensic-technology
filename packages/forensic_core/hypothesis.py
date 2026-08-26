from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


def _probability(value: float, name: str) -> float:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be a finite probability between 0 and 1")
    return value


def bayesian_update(*, prior: float, likelihood_if_true: float, likelihood_if_false: float) -> float:
    prior = _probability(prior, "prior")
    likelihood_if_true = _probability(likelihood_if_true, "likelihood_if_true")
    likelihood_if_false = _probability(likelihood_if_false, "likelihood_if_false")
    numerator = likelihood_if_true * prior
    denominator = numerator + likelihood_if_false * (1.0 - prior)
    if denominator == 0.0:
        raise ValueError("evidence has zero probability under both hypotheses")
    return numerator / denominator


@dataclass(frozen=True, slots=True)
class SourceAssessment:
    reliability: float
    information_credibility: float

    def __post_init__(self) -> None:
        _probability(self.reliability, "reliability")
        _probability(self.information_credibility, "information_credibility")

    @property
    def weight(self) -> float:
        return self.reliability * self.information_credibility


def weighted_likelihood(*, raw_likelihood: float, assessment: SourceAssessment) -> float:
    raw_likelihood = _probability(raw_likelihood, "raw_likelihood")
    return 0.5 + (raw_likelihood - 0.5) * assessment.weight


def normalize_competing_hypotheses(weights: dict[str, float]) -> dict[str, float]:
    if not weights:
        raise ValueError("weights must not be empty")
    for name, weight in weights.items():
        if not name.strip():
            raise ValueError("hypothesis names must not be blank")
        if not isfinite(weight) or weight < 0:
            raise ValueError("weights must be finite and non-negative")
    total = sum(weights.values())
    if total == 0:
        raise ValueError("at least one weight must be greater than zero")
    return {name: weight / total for name, weight in sorted(weights.items())}
