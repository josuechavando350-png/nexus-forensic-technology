from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest

# auditoria.py imports runtime settings at module import time. Supply deterministic
# test-only values before importing it; no external services are contacted here.
os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")
os.environ.setdefault("NEO4J_USER", "test")
os.environ.setdefault("NEO4J_PASSWORD", "test-password")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-key-with-at-least-32-bytes")
os.environ.setdefault("LOG_FILE_PATH", "/tmp/nexus-audit-test.log")

from auditoria import AuditoriaInmutable


class RecoveredAuditLogCapabilityTests(unittest.TestCase):
    def test_capability_253_immutable_audit_log_chains_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.log"
            audit = AuditoriaInmutable(str(path))
            first_hash = audit.registrar_evento("case-1", "ingest evidence")
            second_hash = audit.registrar_evento("case-1", "verify evidence")

            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(records[0]["index"], 0)
            self.assertEqual(records[0]["hash_anterior"], "0" * 64)
            self.assertEqual(records[1]["hash_anterior"], records[0]["hash_actual"])
            self.assertEqual(records[1]["hash_actual"], first_hash)
            self.assertEqual(records[2]["hash_anterior"], first_hash)
            self.assertEqual(records[2]["hash_actual"], second_hash)
            self.assertTrue(audit.verificar_integridad())

    def test_capability_298_tamper_evident_logging_rejects_modified_chain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.log"
            audit = AuditoriaInmutable(str(path))
            audit.registrar_evento("case-2", "original action")
            self.assertTrue(audit.verificar_integridad())

            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            records[1]["accion"] = "tampered action"
            path.write_text(
                "\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n",
                encoding="utf-8",
            )

            self.assertFalse(audit.verificar_integridad())


if __name__ == "__main__":
    unittest.main()
