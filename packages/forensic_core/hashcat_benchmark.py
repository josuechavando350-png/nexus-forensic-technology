from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


class HashcatBenchmarkError(RuntimeError):
    """Raised when a synthetic Hashcat benchmark cannot be collected or parsed."""


@dataclass(frozen=True, slots=True)
class HashcatBenchmarkRecord:
    device_id: int
    metadata_fields: tuple[str, ...]
    execution_runtime_ms: float
    hashes_per_second: int


def hashcat_benchmark_argv(
    hash_mode: int, executable: str = "hashcat"
) -> tuple[str, ...]:
    if isinstance(hash_mode, bool) or not isinstance(hash_mode, int):
        raise TypeError("hash_mode must be an integer")
    if hash_mode < 0 or hash_mode > 99_999:
        raise ValueError("hash_mode must be between 0 and 99999")
    return (
        executable,
        "--benchmark",
        "--hash-type",
        str(hash_mode),
        "--machine-readable",
        "--quiet",
    )


def parse_hashcat_benchmark(text: str) -> tuple[HashcatBenchmarkRecord, ...]:
    """Parse Hashcat machine-readable benchmark output only.

    This parser intentionally accepts synthetic benchmark output, not cracking
    status, recovered passwords, potfiles, wordlists, masks, or hash targets.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    records: list[HashcatBenchmarkRecord] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("Started:") or line.startswith("Stopped:"):
            continue
        fields = [item.strip() for item in line.split(":")]
        if len(fields) < 3:
            raise HashcatBenchmarkError(f"line {line_number}: malformed benchmark row")
        try:
            device_id = int(fields[0])
            runtime_ms = float(fields[-2])
            hashes_per_second = int(fields[-1])
        except ValueError as exc:
            raise HashcatBenchmarkError(
                f"line {line_number}: invalid numeric benchmark field"
            ) from exc
        if device_id < 0 or runtime_ms < 0 or hashes_per_second < 0:
            raise HashcatBenchmarkError(f"line {line_number}: negative benchmark value")
        records.append(
            HashcatBenchmarkRecord(
                device_id=device_id,
                metadata_fields=tuple(fields[1:-2]),
                execution_runtime_ms=runtime_ms,
                hashes_per_second=hashes_per_second,
            )
        )
    return tuple(records)


def collect_hashcat_benchmark(
    hash_mode: int,
    executable: str = "hashcat",
    *,
    timeout_seconds: float = 120.0,
) -> tuple[HashcatBenchmarkRecord, ...]:
    """Run Hashcat's synthetic benchmark mode without accepting a hash target."""

    resolved = shutil.which(executable) if "/" not in executable else executable
    if not resolved:
        raise FileNotFoundError(executable)
    try:
        completed = subprocess.run(
            hashcat_benchmark_argv(hash_mode, resolved),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise HashcatBenchmarkError("Hashcat benchmark timed out") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or "Hashcat benchmark failed"
        raise HashcatBenchmarkError(detail)
    records = parse_hashcat_benchmark(completed.stdout)
    if not records:
        raise HashcatBenchmarkError("Hashcat returned no benchmark records")
    return records
