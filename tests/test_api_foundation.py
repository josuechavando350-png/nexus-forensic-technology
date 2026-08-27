from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")
os.environ.setdefault("NEO4J_USER", "neo4j")
os.environ.setdefault("NEO4J_PASSWORD", "N3xusSecurePass2026!")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "96f8c6d4e8b2a1c7d3e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7",
)
os.environ.setdefault("LOG_FILE_PATH", "/tmp/nexus_api_foundation_test_audit.log")

TEST_AUDIT = Path(os.environ["LOG_FILE_PATH"])
if TEST_AUDIT.exists():
    TEST_AUDIT.unlink()

import jwt
from fastapi.testclient import TestClient

from auditoria import AuditoriaInmutable
from auth import ALGORITHM, generar_token_jwt, hash_password, verificar_password
import main
from tasks import _validar_clabe, procesar_inteligencia_pesada


class AuthenticationTests(unittest.TestCase):
    def test_password_hash_and_verify(self) -> None:
        hashed = hash_password("CorrectHorseBatteryStaple2026!")
        self.assertNotEqual(hashed, "CorrectHorseBatteryStaple2026!")
        self.assertTrue(verificar_password("CorrectHorseBatteryStaple2026!", hashed))
        self.assertFalse(verificar_password("incorrect-password", hashed))

    def test_jwt_contains_required_claims(self) -> None:
        token = generar_token_jwt("analista-001")
        payload = jwt.decode(
            token,
            os.environ["JWT_SECRET_KEY"],
            algorithms=[ALGORITHM],
        )
        self.assertEqual(payload["sub"], "analista-001")
        self.assertEqual(payload["rol"], "analista_tactico")
        self.assertIn("iat", payload)
        self.assertIn("exp", payload)
        self.assertGreater(payload["exp"], payload["iat"])


class ImmutableAuditTests(unittest.TestCase):
    def test_chain_is_created_extended_and_verified(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "audit.log"
            audit = AuditoriaInmutable(str(path))
            first_hash = audit.registrar_evento("CASE-1", "INGESTA")
            second_hash = audit.registrar_evento("CASE-1", "ENCOLADO")

            self.assertEqual(len(first_hash), 64)
            self.assertEqual(len(second_hash), 64)
            self.assertNotEqual(first_hash, second_hash)
            self.assertTrue(audit.verificar_integridad())

            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 3)
            genesis = json.loads(lines[0])
            first = json.loads(lines[1])
            second = json.loads(lines[2])
            self.assertEqual(genesis["index"], 0)
            self.assertEqual(first["hash_anterior"], genesis["hash_actual"])
            self.assertEqual(second["hash_anterior"], first["hash_actual"])

    def test_tampering_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "audit.log"
            audit = AuditoriaInmutable(str(path))
            audit.registrar_evento("CASE-2", "ORIGINAL")
            content = path.read_text(encoding="utf-8").replace("ORIGINAL", "ALTERADO")
            path.write_text(content, encoding="utf-8")
            self.assertFalse(audit.verificar_integridad())


class TaskTests(unittest.TestCase):
    def test_clabe_checksum(self) -> None:
        self.assertTrue(_validar_clabe("032180000118359719"))
        self.assertFalse(_validar_clabe("032180000118359710"))

    def test_task_executes_locally_with_valid_inputs(self) -> None:
        digest = hashlib.sha256(b"synthetic-evidence").hexdigest()
        result = procesar_inteligencia_pesada.run(
            digest,
            "+525512345678",
            "032180000118359719",
        )
        self.assertEqual(result["status"], "COMPLETO")
        self.assertEqual(result["hash_evidencia"], digest)
        self.assertTrue(result["telefono_validado"])
        self.assertTrue(result["clabe_validada"])


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(main.app)

    def test_login_rejects_wrong_password(self) -> None:
        response = self.client.post(
            "/api/v1/auth/login",
            json={"usuario": "neo4j", "password": "wrong-password"},
        )
        self.assertEqual(response.status_code, 401)

    def test_login_and_protected_ingestion(self) -> None:
        login_response = self.client.post(
            "/api/v1/auth/login",
            json={
                "usuario": os.environ["NEO4J_USER"],
                "password": os.environ["NEO4J_PASSWORD"],
            },
        )
        self.assertEqual(login_response.status_code, 200)
        token = login_response.json()["access_token"]

        evidence = b"NEXUS synthetic evidence payload"
        expected_hash = hashlib.sha256(evidence).hexdigest()
        with patch.object(
            main.procesar_inteligencia_pesada,
            "delay",
            return_value=SimpleNamespace(id="task-123"),
        ):
            response = self.client.post(
                "/api/v1/investigar",
                headers={"Authorization": f"Bearer {token}"},
                files={"file": ("evidence.bin", evidence, "application/octet-stream")},
                data={
                    "telefono": "+525512345678",
                    "cuenta_bancaria": "032180000118359719",
                },
            )

        self.assertEqual(response.status_code, 202, response.text)
        body = response.json()
        self.assertEqual(body["status"], "ACEPTADO")
        self.assertEqual(body["tarea_id"], "task-123")
        self.assertEqual(body["hash_evidencia_sha256"], expected_hash)
        self.assertTrue(body["caso_id"].startswith("NXS-"))
        self.assertEqual(len(body["audit_hash"]), 64)

    def test_ingestion_requires_bearer_token(self) -> None:
        response = self.client.post(
            "/api/v1/investigar",
            files={"file": ("evidence.bin", b"evidence", "application/octet-stream")},
            data={
                "telefono": "+525512345678",
                "cuenta_bancaria": "032180000118359719",
            },
        )
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
