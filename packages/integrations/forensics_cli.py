from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Sequence


def _existing_path(path: str | Path) -> Path:
    result = Path(path)
    if not result.exists():
        raise ValueError(f"path does not exist: {result}")
    return result


@dataclass(frozen=True, slots=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


def run_read_only_command(executable: str, arguments: Sequence[str], *, timeout: float = 120.0) -> CommandResult:
    if not executable.strip():
        raise ValueError("executable must not be blank")
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    completed = subprocess.run([executable, *map(str, arguments)], check=False, capture_output=True, text=True, timeout=timeout, shell=False)
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def exiftool_metadata(path: str | Path, *, executable: str = "exiftool") -> dict[str, object]:
    target = _existing_path(path)
    result = run_read_only_command(executable, ["-json", "-G", "-n", str(target)])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ExifTool failed")
    payload = json.loads(result.stdout)
    if not isinstance(payload, list) or len(payload) != 1 or not isinstance(payload[0], dict):
        raise RuntimeError("unexpected ExifTool JSON output")
    return payload[0]


def ffprobe_metadata(path: str | Path, *, executable: str = "ffprobe") -> dict[str, object]:
    target = _existing_path(path)
    result = run_read_only_command(executable, ["-v", "error", "-show_format", "-show_streams", "-of", "json", str(target)])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffprobe failed")
    payload = json.loads(result.stdout)
    if not isinstance(payload, dict):
        raise RuntimeError("unexpected ffprobe JSON output")
    return payload


def sleuthkit_fls(image_path: str | Path, *, executable: str = "fls") -> str:
    target = _existing_path(image_path)
    result = run_read_only_command(executable, ["-r", "-p", str(target)])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "fls failed")
    return result.stdout
