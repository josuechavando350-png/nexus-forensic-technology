from __future__ import annotations

import csv
import shutil
import subprocess
from dataclasses import dataclass

_QUERY_FIELDS = (
    "name",
    "uuid",
    "driver_version",
    "memory.total",
    "memory.used",
    "temperature.gpu",
    "power.draw",
)


class NvidiaSmiError(RuntimeError):
    """Raised when read-only NVIDIA telemetry cannot be collected or parsed."""


@dataclass(frozen=True, slots=True)
class NvidiaGpuTelemetry:
    name: str
    uuid: str
    driver_version: str
    memory_total_mib: int
    memory_used_mib: int
    temperature_c: int
    power_draw_w: float

    @property
    def is_rtx_4090(self) -> bool:
        normalized = " ".join(self.name.upper().split())
        return "RTX 4090" in normalized


def nvidia_smi_query_argv(executable: str = "nvidia-smi") -> tuple[str, ...]:
    return (
        executable,
        f"--query-gpu={','.join(_QUERY_FIELDS)}",
        "--format=csv,noheader,nounits",
    )


def _parse_int(value: str, field: str, row_number: int) -> int:
    try:
        return int(value.strip())
    except ValueError as exc:
        raise NvidiaSmiError(f"row {row_number}: invalid {field}") from exc


def _parse_float(value: str, field: str, row_number: int) -> float:
    try:
        return float(value.strip())
    except ValueError as exc:
        raise NvidiaSmiError(f"row {row_number}: invalid {field}") from exc


def parse_nvidia_smi_csv(text: str) -> tuple[NvidiaGpuTelemetry, ...]:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    records: list[NvidiaGpuTelemetry] = []
    for row_number, row in enumerate(csv.reader(text.splitlines()), start=1):
        if not row or all(not item.strip() for item in row):
            continue
        if len(row) != len(_QUERY_FIELDS):
            raise NvidiaSmiError(
                f"row {row_number}: expected {len(_QUERY_FIELDS)} fields, got {len(row)}"
            )
        records.append(
            NvidiaGpuTelemetry(
                name=row[0].strip(),
                uuid=row[1].strip(),
                driver_version=row[2].strip(),
                memory_total_mib=_parse_int(row[3], "memory.total", row_number),
                memory_used_mib=_parse_int(row[4], "memory.used", row_number),
                temperature_c=_parse_int(row[5], "temperature.gpu", row_number),
                power_draw_w=_parse_float(row[6], "power.draw", row_number),
            )
        )
    return tuple(records)


def collect_nvidia_gpu_telemetry(
    executable: str = "nvidia-smi", *, timeout_seconds: float = 10.0
) -> tuple[NvidiaGpuTelemetry, ...]:
    """Collect read-only GPU inventory/telemetry through NVIDIA's nvidia-smi."""

    resolved = shutil.which(executable) if "/" not in executable else executable
    if not resolved:
        raise FileNotFoundError(executable)
    try:
        completed = subprocess.run(
            nvidia_smi_query_argv(resolved),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise NvidiaSmiError("nvidia-smi telemetry query timed out") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or "nvidia-smi returned a non-zero status"
        raise NvidiaSmiError(detail)
    return parse_nvidia_smi_csv(completed.stdout)
