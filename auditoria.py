from __future__ import annotations

from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
from threading import RLock
from typing import Any, TextIO

from config import settings


class AuditoriaInmutable:
    _ZERO_HASH = "0" * 64

    def __init__(self, ruta_log: str = settings.LOG_FILE_PATH) -> None:
        ruta = Path(ruta_log).expanduser()
        if not ruta.name:
            raise ValueError("ruta_log must point to a file")
        self.ruta_log = ruta
        self._thread_lock = RLock()
        try:
            self.ruta_log.parent.mkdir(parents=True, exist_ok=True)
            self._inicializar_si_es_necesario()
        except OSError as exc:
            raise RuntimeError(f"cannot initialize audit log at {self.ruta_log}") from exc

    @staticmethod
    def _timestamp_utc() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")

    def _calcular_hash(self, registro: dict[str, Any]) -> str:
        required = ("index", "timestamp_utc", "caso_id", "accion", "hash_anterior")
        missing = [key for key in required if key not in registro]
        if missing:
            raise ValueError(f"audit record is missing required fields: {', '.join(missing)}")
        canonical = {
            "index": registro["index"],
            "timestamp_utc": registro["timestamp_utc"],
            "caso_id": registro["caso_id"],
            "accion": registro["accion"],
            "hash_anterior": registro["hash_anterior"],
        }
        payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _serializar(registro: dict[str, Any]) -> str:
        return json.dumps(registro, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def _crear_genesis(self) -> dict[str, Any]:
        genesis: dict[str, Any] = {
            "index": 0,
            "timestamp_utc": self._timestamp_utc(),
            "caso_id": "SYSTEM_GENESIS",
            "accion": "INICIALIZACION_DEL_MOTOR_NEXUS",
            "hash_anterior": self._ZERO_HASH,
        }
        genesis["hash_actual"] = self._calcular_hash(genesis)
        return genesis

    def _inicializar_si_es_necesario(self) -> None:
        try:
            descriptor = os.open(
                self.ruta_log,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
        except FileExistsError:
            if self.ruta_log.stat().st_size == 0:
                with self.ruta_log.open("r+", encoding="utf-8") as handle:
                    self._bloquear(handle)
                    try:
                        if self.ruta_log.stat().st_size == 0:
                            self._escribir_y_sincronizar(handle, self._crear_genesis())
                    finally:
                        self._desbloquear(handle)
            return

        try:
            genesis_line = (self._serializar(self._crear_genesis()) + "\n").encode("utf-8")
            os.write(descriptor, genesis_line)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    @staticmethod
    def _bloquear(handle: TextIO) -> None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)

    @staticmethod
    def _desbloquear(handle: TextIO) -> None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _ultimo_registro(self, handle: TextIO) -> dict[str, Any]:
        handle.seek(0)
        last_nonblank = ""
        for line in handle:
            if line.strip():
                last_nonblank = line
        if not last_nonblank:
            raise RuntimeError("audit log contains no records")
        try:
            record = json.loads(last_nonblank)
        except json.JSONDecodeError as exc:
            raise RuntimeError("last audit record contains invalid JSON") from exc
        if not isinstance(record, dict):
            raise RuntimeError("last audit record is not a JSON object")
        expected = self._calcular_hash(record)
        if record.get("hash_actual") != expected:
            raise RuntimeError("audit chain integrity check failed on last record")
        return record

    def _escribir_y_sincronizar(self, handle: TextIO, registro: dict[str, Any]) -> None:
        handle.seek(0, os.SEEK_END)
        handle.write(self._serializar(registro) + "\n")
        handle.flush()
        os.fsync(handle.fileno())

    def registrar_evento(self, caso_id: str, accion_ejecutada: str) -> str:
        caso = caso_id.strip()
        accion = accion_ejecutada.strip()
        if not caso:
            raise ValueError("caso_id must not be blank")
        if not accion:
            raise ValueError("accion_ejecutada must not be blank")

        with self._thread_lock:
            try:
                with self.ruta_log.open("r+", encoding="utf-8") as handle:
                    self._bloquear(handle)
                    try:
                        previous = self._ultimo_registro(handle)
                        nuevo: dict[str, Any] = {
                            "index": int(previous["index"]) + 1,
                            "timestamp_utc": self._timestamp_utc(),
                            "caso_id": caso,
                            "accion": accion,
                            "hash_anterior": str(previous["hash_actual"]),
                        }
                        nuevo["hash_actual"] = self._calcular_hash(nuevo)
                        self._escribir_y_sincronizar(handle, nuevo)
                        return str(nuevo["hash_actual"])
                    finally:
                        self._desbloquear(handle)
            except OSError as exc:
                raise RuntimeError("audit event could not be persisted") from exc

    def verificar_integridad(self) -> bool:
        with self._thread_lock:
            try:
                with self.ruta_log.open("r", encoding="utf-8") as handle:
                    previous_hash = self._ZERO_HASH
                    expected_index = 0
                    seen = False
                    for raw_line in handle:
                        if not raw_line.strip():
                            continue
                        seen = True
                        record = json.loads(raw_line)
                        if not isinstance(record, dict):
                            return False
                        if record.get("index") != expected_index:
                            return False
                        if record.get("hash_anterior") != previous_hash:
                            return False
                        current_hash = self._calcular_hash(record)
                        if record.get("hash_actual") != current_hash:
                            return False
                        previous_hash = current_hash
                        expected_index += 1
                    return seen
            except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
                return False
