from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from timesketch_api_client import client as timesketch_client


@dataclass(frozen=True, slots=True)
class TimesketchSketchSummary:
    sketch_id: int
    name: str
    description: str


def _require_non_blank(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be blank")
    return normalized


def create_timesketch_client(
    host_uri: str,
    username: str,
    password: str,
    *,
    verify: bool = True,
) -> timesketch_client.TimesketchApi:
    """Create an authenticated client for a caller-supplied Timesketch instance."""
    host = _require_non_blank(host_uri, "host_uri")
    user = _require_non_blank(username, "username")
    secret = _require_non_blank(password, "password")
    if not host.startswith(("http://", "https://")):
        raise ValueError("host_uri must use http:// or https://")
    return timesketch_client.TimesketchApi(
        host_uri=host,
        username=user,
        password=secret,
        verify=verify,
    )


def list_sketch_summaries(api: timesketch_client.TimesketchApi) -> tuple[TimesketchSketchSummary, ...]:
    """Read sketches visible to the authenticated Timesketch identity."""
    summaries: list[TimesketchSketchSummary] = []
    try:
        sketches: Iterable[object] = api.list_sketches()
        for sketch in sketches:
            sketch_id = getattr(sketch, "id", None)
            name = getattr(sketch, "name", None)
            description = getattr(sketch, "description", "")
            if not isinstance(sketch_id, int):
                raise RuntimeError("Timesketch returned a sketch without an integer id")
            if not isinstance(name, str):
                raise RuntimeError("Timesketch returned a sketch without a string name")
            summaries.append(
                TimesketchSketchSummary(
                    sketch_id=sketch_id,
                    name=name,
                    description=str(description or ""),
                )
            )
    except (OSError, ValueError) as exc:
        raise RuntimeError("Timesketch API request failed") from exc
    return tuple(summaries)
