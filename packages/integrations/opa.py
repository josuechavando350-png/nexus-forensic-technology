from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(slots=True)
class OPAAdapter:
    http_client: Any
    base_url: str

    def evaluate(self, *, policy_path: str, input_document: Mapping[str, Any]) -> Any:
        policy_path = policy_path.strip("/")
        if not policy_path or ".." in policy_path.split("/"):
            raise ValueError("invalid policy_path")
        response = self.http_client.post(
            f"{self.base_url.rstrip('/')}/v1/data/{policy_path}",
            json={"input": dict(input_document)},
            timeout=10.0,
        )
        response.raise_for_status()
        payload = response.json()
        if "result" not in payload:
            raise RuntimeError("OPA response did not contain result")
        return payload["result"]
