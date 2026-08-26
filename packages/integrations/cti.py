from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(slots=True)
class OpenCTIAdapter:
    http_client: Any
    endpoint: str
    token: str

    def graphql(self, *, query: str, variables: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
        if not query.strip():
            raise ValueError("query must not be blank")
        response = self.http_client.post(
            self.endpoint,
            json={"query": query, "variables": dict(variables or {})},
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
            timeout=30.0,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("errors"):
            raise RuntimeError(f"OpenCTI GraphQL error: {payload['errors']}")
        return payload.get("data", {})


@dataclass(slots=True)
class MISPAdapter:
    pymisp: Any

    def search_attributes(self, *, value: str, attribute_type: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        if not value.strip():
            raise ValueError("value must not be blank")
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        result = self.pymisp.search(controller="attributes", value=value, type_attribute=attribute_type, limit=limit, pythonify=False)
        if isinstance(result, dict):
            return list(result.get("Attribute", []))
        return list(result or [])
