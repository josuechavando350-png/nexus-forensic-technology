from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import log
import re
from typing import Mapping


_TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)


def tokenize(text: str) -> tuple[str, ...]:
    return tuple(token.casefold() for token in _TOKEN_RE.findall(text))


@dataclass(frozen=True, slots=True)
class SearchHit:
    document_id: str
    score: float


class BM25Index:
    def __init__(self, documents: Mapping[str, str], *, k1: float = 1.5, b: float = 0.75) -> None:
        if not documents:
            raise ValueError("documents must not be empty")
        if k1 <= 0 or not 0 <= b <= 1:
            raise ValueError("invalid BM25 parameters")
        self._k1 = k1
        self._b = b
        self._tokens = {doc_id: tokenize(text) for doc_id, text in documents.items()}
        if any(not doc_id.strip() for doc_id in self._tokens):
            raise ValueError("document identifiers must not be blank")
        self._average_length = sum(map(len, self._tokens.values())) / len(self._tokens)
        self._document_frequency: Counter[str] = Counter()
        for tokens in self._tokens.values():
            self._document_frequency.update(set(tokens))

    def search(self, query: str, *, limit: int = 10) -> tuple[SearchHit, ...]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        query_tokens = tokenize(query)
        total_docs = len(self._tokens)
        scores: list[SearchHit] = []
        for doc_id, tokens in self._tokens.items():
            frequencies = Counter(tokens)
            score = 0.0
            for term in query_tokens:
                frequency = frequencies[term]
                if frequency == 0:
                    continue
                doc_frequency = self._document_frequency[term]
                idf = log(1 + (total_docs - doc_frequency + 0.5) / (doc_frequency + 0.5))
                norm = frequency + self._k1 * (1 - self._b + self._b * len(tokens) / (self._average_length or 1))
                score += idf * (frequency * (self._k1 + 1)) / norm
            if score > 0:
                scores.append(SearchHit(doc_id, score))
        scores.sort(key=lambda hit: (-hit.score, hit.document_id))
        return tuple(scores[:limit])
