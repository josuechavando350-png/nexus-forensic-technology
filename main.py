from __future__ import annotations

import hashlib
import hmac
import re
from typing import Annotated, Any
from uuid import uuid4

from celery.exceptions import CeleryError
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from auditoria import AuditoriaInmutable
from auth import generar_token_jwt, hash_password, verificar_password, verificar_ruta_protegida
from config import settings
from tasks import procesar_inteligencia_pesada


MAX_UPLOAD_BYTES = 50 * 1024 * 1024
_PHONE_RE = re.compile(r"^[+0-9 ()-]{7,25}$")
_BOOTSTRAP_PASSWORD_HASH = hash_password(settings.NEO4J_PASSWORD)
auditoria = AuditoriaInmutable(settings.LOG_FILE_PATH)

app = FastAPI(
    title="NEXUS Investigation OS - Core API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
)


class LoginRequest(BaseModel):
    usuario: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=512)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int = 28_800


class InvestigationAccepted(BaseModel):
    status: str
    caso_id: str
    tarea_id: str
    hash_evidencia_sha256: str
    audit_hash: str


def _clabe_valida(clabe: str) -> bool:
    if len(clabe) != 18 or not clabe.isdigit():
        return False
    weights = (3, 7, 1)
    total = sum((int(digit) * weights[index % 3]) % 10 for index, digit in enumerate(clabe[:17]))
    expected = (10 - (total % 10)) % 10
    return expected == int(clabe[17])


async def _hash_upload_sha256(upload: UploadFile) -> tuple[str, int]:
    digest = hashlib.sha256()
    total = 0
    try:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_UPLOAD_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="El archivo excede el límite de 50 MiB",
                )
            digest.update(chunk)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fue posible leer la evidencia enviada",
        ) from exc
    finally:
        try:
            await upload.seek(0)
        except Exception:
            pass

    if total == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La evidencia enviada está vacía",
        )
    return digest.hexdigest(), total


@app.get("/health", include_in_schema=False)
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/auth/login", response_model=TokenResponse)
def login(credentials: LoginRequest) -> TokenResponse:
    try:
        user_matches = hmac.compare_digest(credentials.usuario.strip(), settings.NEO4J_USER)
        password_matches = verificar_password(credentials.password, _BOOTSTRAP_PASSWORD_HASH)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No fue posible validar las credenciales",
        ) from exc

    if not user_matches or not password_matches:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token = generar_token_jwt(credentials.usuario.strip())
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No fue posible emitir el token de acceso",
        ) from exc
    return TokenResponse(access_token=token)


@app.post(
    "/api/v1/investigar",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=InvestigationAccepted,
)
async def investigar(
    file: Annotated[UploadFile, File(...)],
    telefono: Annotated[str, Form(...)],
    cuenta_bancaria: Annotated[str, Form(...)],
    principal: Annotated[dict[str, Any], Depends(verificar_ruta_protegida)],
) -> InvestigationAccepted:
    phone = telefono.strip()
    clabe = cuenta_bancaria.strip()
    if not _PHONE_RE.fullmatch(phone):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El número telefónico tiene un formato inválido",
        )
    if not _clabe_valida(clabe):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La CLABE debe ser válida y contener 18 dígitos",
        )

    evidence_hash, size_bytes = await _hash_upload_sha256(file)
    case_id = f"NXS-{uuid4().hex.upper()}"
    content_type = file.content_type or "application/octet-stream"

    try:
        audit_hash = auditoria.registrar_evento(
            case_id,
            (
                "INGESTA_EVIDENCIA "
                f"sha256={evidence_hash} bytes={size_bytes} content_type={content_type} "
                f"analista={principal['sub']}"
            ),
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No fue posible registrar la cadena de auditoría",
        ) from exc

    try:
        async_result = procesar_inteligencia_pesada.delay(evidence_hash, phone, clabe)
    except (CeleryError, OSError, ConnectionError) as exc:
        try:
            auditoria.registrar_evento(case_id, "FALLO_ENCOLADO_ANALITICA")
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El sistema de procesamiento asíncrono no está disponible",
        ) from exc

    return InvestigationAccepted(
        status="ACEPTADO",
        caso_id=case_id,
        tarea_id=str(async_result.id),
        hash_evidencia_sha256=evidence_hash,
        audit_hash=audit_hash,
    )
