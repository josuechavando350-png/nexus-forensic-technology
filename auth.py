from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from passlib.exc import UnknownHashError

from config import settings


ALGORITHM = "HS256"
TOKEN_TTL = timedelta(hours=8)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_bearer = HTTPBearer(auto_error=True)


def hash_password(password: str) -> str:
    if not isinstance(password, str) or len(password) < 12:
        raise ValueError("password must contain at least 12 characters")
    try:
        return str(pwd_context.hash(password))
    except (ValueError, TypeError) as exc:
        raise ValueError("password could not be hashed") from exc


def verificar_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    try:
        return bool(pwd_context.verify(plain_password, hashed_password))
    except (UnknownHashError, ValueError, TypeError):
        return False


def generar_token_jwt(usuario_id: str) -> str:
    subject = usuario_id.strip()
    if not subject:
        raise ValueError("usuario_id must not be blank")

    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + TOKEN_TTL,
        "rol": "analista_tactico",
    }
    try:
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)
    except (jwt.PyJWTError, TypeError, ValueError) as exc:
        raise RuntimeError("JWT token could not be generated") from exc
    return str(token)


def verificar_ruta_protegida(
    credentials: HTTPAuthorizationCredentials = Security(security_bearer),
) -> dict[str, Any]:
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["sub", "iat", "exp", "rol"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token de acceso ha expirado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación inválido o alterado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if payload.get("rol") != "analista_tactico" or not str(payload.get("sub", "")).strip():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El token no contiene privilegios válidos",
        )
    return dict(payload)
