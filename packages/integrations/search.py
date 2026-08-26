from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(slots=True)
class OpenSearchAdapter:
    client: Any
    index: str

    def __post_init__(self) -> None:
        if not self.index.strip():
            raise ValueError("index must not be blank")

    def index_document(self, *, document_id: str, document: Mapping[str, Any]) -> Mapping[str, Any]:
        if not document_id.strip():
            raise ValueError("document_id must not be blank")
        if not isinstance(document, Mapping):
            raise TypeError("document must be a mapping")
        return self.client.index(index=self.index, id=document_id, body=dict(document), refresh=False)

    def search_text(self, *, query: str, fields: tuple[str, ...], size: int = 20) -> list[dict[str, Any]]:
        if not query.strip() or not fields:
            raise ValueError("query and fields must not be empty")
        if not 1 <= size <= 1000:
            raise ValueError("size must be between 1 and 1000")
        body = {
            "query": {"multi_match": {"query": query, "fields": list(fields)}},
            "size": size,
            "sort": [{"_score": "desc"}, {"_id": "asc"}],
        }
        response = self.client.search(index=self.index, body=body)
        return [{"id": hit.get("_id"), "score": hit.get("_score"), "source": hit.get("_source", {})} for hit in response.get("hits", {}).get("hits", [])]
