from __future__ import annotations

from dataclasses import dataclass
from math import fsum, sqrt
from typing import Iterable


@dataclass(frozen=True, slots=True)
class ZScoreResult:
    value: float
    z_score: float


def z_scores(values: Iterable[float]) -> tuple[ZScoreResult, ...]:
    data = tuple(float(value) for value in values)
    if not data:
        raise ValueError("values must not be empty")
    mean = fsum(data) / len(data)
    variance = fsum((value - mean) ** 2 for value in data) / len(data)
    standard_deviation = sqrt(variance)
    if standard_deviation == 0:
        return tuple(ZScoreResult(value, 0.0) for value in data)
    return tuple(ZScoreResult(value, (value - mean) / standard_deviation) for value in data)


def anomalies_by_zscore(values: Iterable[float], *, threshold: float = 3.0) -> tuple[ZScoreResult, ...]:
    if threshold <= 0:
        raise ValueError("threshold must be positive")
    return tuple(result for result in z_scores(values) if abs(result.z_score) >= threshold)
