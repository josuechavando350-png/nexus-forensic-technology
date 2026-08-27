from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Protocol


class Anchor(Protocol):
    def read(self) -> str | None: ...

    def write(self, digest_hex: str) -> None: ...


@dataclass(slots=True)
class SoftwareAnchor:
    """Deterministic test/local anchor. It is not a hardware security boundary."""

    value: str | None = None

    def read(self) -> str | None:
        return self.value

    def write(self, digest_hex: str) -> None:
        _validate_digest(digest_hex)
        self.value = digest_hex


@dataclass(frozen=True, slots=True)
class TPM2NVAnchor:
    nv_index: str
    hierarchy: str = "o"
    read_executable: str = "tpm2_nvread"
    write_executable: str = "tpm2_nvwrite"

    def read(self) -> str | None:
        try:
            completed = subprocess.run(
                [self.read_executable, "-C", self.hierarchy, "-s", "32", self.nv_index],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10.0,
                shell=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RuntimeError("TPM2 NV read failed to execute") from exc
        if completed.returncode != 0:
            detail = completed.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(detail or "TPM2 NV read failed")
        if not completed.stdout:
            return None
        if len(completed.stdout) != 32:
            raise RuntimeError("TPM2 NV anchor has unexpected length")
        return completed.stdout.hex()

    def write(self, digest_hex: str) -> None:
        _validate_digest(digest_hex)
        digest = bytes.fromhex(digest_hex)
        try:
            completed = subprocess.run(
                [self.write_executable, "-C", self.hierarchy, "-i", "-", self.nv_index],
                input=digest,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=10.0,
                shell=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RuntimeError("TPM2 NV write failed to execute") from exc
        if completed.returncode != 0:
            detail = completed.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(detail or "TPM2 NV write failed")


def _validate_digest(digest_hex: str) -> None:
    if len(digest_hex) != 64:
        raise ValueError("digest must be a 64-character SHA-256 hex string")
    try:
        bytes.fromhex(digest_hex)
    except ValueError as exc:
        raise ValueError("digest must be hexadecimal") from exc


def _canonical_hash(record: dict[str, object]) -> str:
    encoded = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _require_index(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RuntimeError("audit record index must be an integer")
    if value < 0:
        raise RuntimeError("audit record index must not be negative")
    return value


class BitacoraEndurecidaHardware:
    """Append-only hash chain whose latest digest is anchored externally."""

    def __init__(self, path: str | Path, anchor: Anchor) -> None:
        self._path = Path(path)
        self._anchor = anchor
        self._lock = Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._initialize_genesis()
        self.verify_chain()

    def _initialize_genesis(self) -> None:
        genesis_base: dict[str, object] = {
            "index": 0,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "agente": "SYSTEM",
            "accion": "GENESIS",
            "hash_previo": "0" * 64,
        }
        genesis = dict(genesis_base)
        genesis["hash_actual"] = _canonical_hash(genesis_base)
        self._atomic_rewrite([genesis])
        self._anchor.write(str(genesis["hash_actual"]))

    def _load_records(self) -> list[dict[str, object]]:
        try:
            lines = self._path.read_text(encoding="utf-8").splitlines()
            decoded = [json.loads(line) for line in lines if line.strip()]
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError("audit log cannot be parsed") from exc
        if not decoded or not all(isinstance(record, dict) for record in decoded):
            raise RuntimeError("audit log is empty or malformed")
        return [dict(record) for record in decoded]

    def _atomic_rewrite(self, records: list[dict[str, object]]) -> None:
        payload = "".join(
            json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
            for record in records
        )
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self._path.parent,
                prefix=f".{self._path.name}.",
                delete=False,
            ) as handle:
                temporary = Path(handle.name)
                os.chmod(temporary, 0o600)
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self._path)
        except OSError as exc:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
            raise RuntimeError("audit log atomic write failed") from exc

    def verify_chain(self) -> str:
        records = self._load_records()
        previous = "0" * 64
        for expected_index, record in enumerate(records):
            try:
                actual_hash = str(record["hash_actual"])
                record_index = _require_index(record["index"])
                base: dict[str, object] = {
                    "index": record_index,
                    "timestamp_utc": str(record["timestamp_utc"]),
                    "agente": str(record["agente"]),
                    "accion": str(record["accion"]),
                    "hash_previo": str(record["hash_previo"]),
                }
            except (KeyError, TypeError, ValueError) as exc:
                raise RuntimeError("audit record schema is invalid") from exc
            _validate_digest(actual_hash)
            if record_index != expected_index:
                raise RuntimeError("audit log index discontinuity detected")
            if base["hash_previo"] != previous:
                raise RuntimeError("audit log chain discontinuity detected")
            if _canonical_hash(base) != actual_hash:
                raise RuntimeError("audit log tampering detected")
            previous = actual_hash

        anchored = self._anchor.read()
        if anchored is not None:
            _validate_digest(anchored)
            if anchored != previous:
                raise RuntimeError("audit log does not match external anchor")
        return previous

    def inyectar_log_militar(self, id_agente: str, operacion: str) -> str:
        agente = id_agente.strip()
        accion = operacion.strip()
        if not agente:
            raise ValueError("id_agente must not be blank")
        if not accion:
            raise ValueError("operacion must not be blank")

        with self._lock:
            current_hash = self.verify_chain()
            records = self._load_records()
            base: dict[str, object] = {
                "index": len(records),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "agente": agente,
                "accion": accion,
                "hash_previo": current_hash,
            }
            record = dict(base)
            record["hash_actual"] = _canonical_hash(base)
            records.append(record)
            self._atomic_rewrite(records)
            digest = str(record["hash_actual"])
            try:
                self._anchor.write(digest)
            except Exception:
                records.pop()
                self._atomic_rewrite(records)
                raise
            return digest
