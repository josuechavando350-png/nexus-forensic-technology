from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
from typing import Final, TypedDict

NIVEL_SEGURIDAD: Final[str] = "TOP_SECRET_E2E"
MAX_PAYLOAD_BYTES: Final[int] = 1024 * 1024
MAX_CPU_SECONDS: Final[int] = 2
MAX_ADDRESS_SPACE_BYTES: Final[int] = 64 * 1024 * 1024
SUBPROCESS_TIMEOUT_SECONDS: Final[float] = 5.0


class IsolatedExecutionResult(TypedDict):
    status: str
    bytes_procesados: int
    sha256: str
    integridad_entorno: bool


def _ensure_non_root() -> None:
    getuid = getattr(os, "getuid", None)
    if getuid is not None and int(getuid()) == 0:
        raise PermissionError(
            "Fallo de seguridad: el motor no puede ejecutar cargas no confiables como root."
        )


def _limit_child_resources() -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (MAX_CPU_SECONDS, MAX_CPU_SECONDS))
    resource.setrlimit(
        resource.RLIMIT_AS,
        (MAX_ADDRESS_SPACE_BYTES, MAX_ADDRESS_SPACE_BYTES),
    )
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NOFILE, (16, 16))


def _validate_payload(payload_bytes: bytes) -> bytes:
    if not isinstance(payload_bytes, bytes):
        raise TypeError("payload_bytes debe ser bytes")
    if len(payload_bytes) > MAX_PAYLOAD_BYTES:
        raise ValueError("Payload excede el límite estricto de 1 MiB.")
    return payload_bytes


def ejecutar_modulo_aislado(payload_bytes: bytes) -> IsolatedExecutionResult:
    """Procesa una carga en un proceso hijo con privilegio mínimo y límites de recursos.

    Este aislamiento es de proceso a nivel de sistema operativo; no sustituye un sandbox
    de kernel, una VM o un contenedor endurecido cuando se ejecuta código no confiable.
    """

    _ensure_non_root()
    payload = _validate_payload(payload_bytes)

    worker = (
        "import hashlib,json,sys;"
        "data=sys.stdin.buffer.read();"
        "out={'bytes_procesados':len(data),'sha256':hashlib.sha256(data).hexdigest()};"
        "sys.stdout.write(json.dumps(out,sort_keys=True,separators=(',',':')))"
    )

    with tempfile.TemporaryDirectory(prefix="nexus-isolated-") as directory:
        cwd = Path(directory)
        env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONIOENCODING": "utf-8",
            "PYTHONNOUSERSITE": "1",
        }
        preexec = _limit_child_resources if os.name == "posix" else None

        try:
            completed = subprocess.run(
                [sys.executable, "-I", "-S", "-c", worker],
                input=payload,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                env=env,
                check=False,
                timeout=SUBPROCESS_TIMEOUT_SECONDS,
                preexec_fn=preexec,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError("El proceso aislado excedió el tiempo permitido.") from exc
        except OSError as exc:
            raise RuntimeError("No fue posible iniciar el proceso aislado.") from exc

    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(detail or "El proceso aislado terminó con error.")

    try:
        decoded = json.loads(completed.stdout.decode("utf-8"))
        bytes_processed = int(decoded["bytes_procesados"])
        digest = str(decoded["sha256"])
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("El proceso aislado devolvió una respuesta inválida.") from exc

    expected = hashlib.sha256(payload).hexdigest()
    if bytes_processed != len(payload) or digest != expected:
        raise RuntimeError("Falló la verificación de integridad del resultado aislado.")

    return {
        "status": "PROCESS_ISOLATED",
        "bytes_procesados": bytes_processed,
        "sha256": digest,
        "integridad_entorno": True,
    }
