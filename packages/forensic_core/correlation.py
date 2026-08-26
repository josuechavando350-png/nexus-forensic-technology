from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class CaseIndicator:
    case_id: str
    indicator: str

    def __post_init__(self) -> None:
        if not self.case_id.strip() or not self.indicator.strip():
            raise ValueError("case_id and indicator must not be blank")


def shared_indicators(records: Iterable[CaseIndicator]) -> dict[str, tuple[str, ...]]:
    index: dict[str, set[str]] = defaultdict(set)
    for record in records:
        index[record.indicator].add(record.case_id)
    return {indicator: tuple(sorted(case_ids)) for indicator, case_ids in sorted(index.items()) if len(case_ids) > 1}


def linked_case_pairs(records: Iterable[CaseIndicator]) -> dict[tuple[str, str], tuple[str, ...]]:
    shared = shared_indicators(records)
    pairs: dict[tuple[str, str], list[str]] = defaultdict(list)
    for indicator, case_ids in shared.items():
        for left_index in range(len(case_ids)):
            for right_index in range(left_index + 1, len(case_ids)):
                pairs[(case_ids[left_index], case_ids[right_index])].append(indicator)
    return {pair: tuple(sorted(values)) for pair, values in sorted(pairs.items())}
