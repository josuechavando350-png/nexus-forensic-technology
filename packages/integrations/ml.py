from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence


@dataclass(frozen=True, slots=True)
class ModelResult:
    labels: tuple[int, ...]


def sklearn_dbscan(features: Sequence[Sequence[float]], *, eps: float = 0.5, min_samples: int = 5) -> ModelResult:
    if eps <= 0 or min_samples <= 0:
        raise ValueError("invalid DBSCAN parameters")
    try:
        from sklearn.cluster import DBSCAN
    except ImportError as exc:
        raise RuntimeError("scikit-learn is required") from exc
    labels = DBSCAN(eps=eps, min_samples=min_samples).fit_predict(features)
    return ModelResult(tuple(int(value) for value in labels))


def sklearn_isolation_forest(features: Sequence[Sequence[float]], *, contamination: float | str = "auto", random_state: int = 0) -> tuple[int, ...]:
    try:
        from sklearn.ensemble import IsolationForest
    except ImportError as exc:
        raise RuntimeError("scikit-learn is required") from exc
    model = IsolationForest(contamination=contamination, random_state=random_state)
    return tuple(int(value) for value in model.fit_predict(features))


def xgboost_classifier(*, random_state: int = 0, **kwargs: Any) -> Any:
    try:
        from xgboost import XGBClassifier
    except ImportError as exc:
        raise RuntimeError("xgboost is required") from exc
    return XGBClassifier(random_state=random_state, **kwargs)
