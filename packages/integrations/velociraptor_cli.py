from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from packages.integrations.forensics_cli import run_read_only_command


_SAFE_QUERIES: dict[str, str] = {
    "host_info": "SELECT OS, Architecture, Hostname, Fqdn FROM info()",
    "processes": "SELECT Pid, Ppid, Name, Exe, CommandLine FROM pslist()",
}


def velociraptor_version(*, executable: str | Path = "velociraptor") -> str:
    """Return version information from the real Velociraptor binary."""
    result = run_read_only_command(str(executable), ["version"], timeout=30.0)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Velociraptor version command failed")
    version = result.stdout.strip()
    if not version:
        raise RuntimeError("Velociraptor returned an empty version response")
    return version


def velociraptor_query(
    query_name: str,
    *,
    executable: str | Path = "velociraptor",
    timeout: float = 120.0,
) -> list[dict[str, Any]]:
    """Run one audited read-only VQL query selected from a fixed allowlist.

    The caller cannot inject arbitrary VQL. Keeping the query set explicit makes the
    forensic adapter deterministic and prevents this integration from becoming a
    general command-execution surface.
    """
    try:
        query = _SAFE_QUERIES[query_name]
    except KeyError as exc:
        allowed = ", ".join(sorted(_SAFE_QUERIES))
        raise ValueError(f"unsupported Velociraptor query: {query_name}; allowed: {allowed}") from exc

    result = run_read_only_command(
        str(executable),
        ["query", "--format=jsonl", query],
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Velociraptor query failed")

    rows: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(result.stdout.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Velociraptor produced invalid JSONL at line {line_number}"
            ) from exc
        if not isinstance(payload, dict):
            raise RuntimeError(
                f"Velociraptor JSONL row {line_number} is not an object"
            )
        rows.append(payload)

    if not rows:
        raise RuntimeError("Velociraptor query returned no rows")
    return rows
