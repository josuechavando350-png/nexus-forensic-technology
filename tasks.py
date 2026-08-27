from __future__ import annotations

import logging
import re
from typing import Any

from celery import Celery

from config import settings


logger = logging.getLogger(__name__)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PHONE_RE = re.compile(r"^[+0-9 ()-]{7,25}$")

celery_app = Celery(
    "nexus_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


def _validar_clabe(clabe: str) -> bool:
    if len(clabe) != 18 or not clabe.isdigit():
        return False
    weights = (3, 7, 1)
    total = sum((int(digit) * weights[index % 3]) % 10 for index, digit in enumerate(clabe[:17]))
    check_digit = (10 - (total % 10)) % 10
    return check_digit == int(clabe[17])


@celery_app.task(name="tasks.procesar_inteligencia_pesada")
def procesar_inteligencia_pesada(
    hash_evidencia: str,
    telefono: str,
    cuenta_bancaria: str,
) -> dict[str, Any]:
    try:
        evidence_hash = hash_evidencia.strip().lower()
        phone = telefono.strip()
        clabe = cuenta_bancaria.strip()

        if not _SHA256_RE.fullmatch(evidence_hash):
            raise ValueError("hash_evidencia must be a lowercase SHA-256 hexadecimal digest")
        if not _PHONE_RE.fullmatch(phone):
            raise ValueError("telefono has an unsupported format")
        if not _validar_clabe(clabe):
            raise ValueError("cuenta_bancaria must be a valid 18-digit CLABE")

        logger.info(
            "NEXUS heavy-analysis task accepted evidence=%s phone_suffix=%s clabe_suffix=%s",
            evidence_hash,
            phone[-4:],
            clabe[-4:],
        )
        logger.info("NEXUS financial and multimedia analysis orchestration completed")

        return {
            "status": "COMPLETO",
            "hash_evidencia": evidence_hash,
            "telefono_validado": True,
            "clabe_validada": True,
        }
    except ValueError:
        logger.exception("NEXUS heavy-analysis task rejected invalid input")
        raise
    except Exception as exc:
        logger.exception("NEXUS heavy-analysis task failed unexpectedly")
        raise RuntimeError("forensic analysis task failed") from exc
