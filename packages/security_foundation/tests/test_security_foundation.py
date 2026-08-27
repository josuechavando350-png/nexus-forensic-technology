from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from packages.security_foundation.hardware_audit import (
    BitacoraEndurecidaHardware,
    SoftwareAnchor,
)
from packages.security_foundation.pqc import MLDSA65EvidenceSigner
from packages.security_foundation.sensor_fusion import fusionar_sensores_inteligencia
from packages.security_foundation.zero_trust import MAX_PAYLOAD_BYTES, ejecutar_modulo_aislado


class ZeroTrustTests(unittest.TestCase):
    def test_isolated_worker_processes_and_hashes_payload(self) -> None:
        result = ejecutar_modulo_aislado(b"forensic-evidence")
        self.assertEqual(result["status"], "PROCESS_ISOLATED")
        self.assertEqual(result["bytes_procesados"], len(b"forensic-evidence"))
        self.assertEqual(len(result["sha256"]), 64)
        self.assertTrue(result["integridad_entorno"])

    def test_rejects_oversized_payload(self) -> None:
        with self.assertRaises(ValueError):
            ejecutar_modulo_aislado(b"x" * (MAX_PAYLOAD_BYTES + 1))

    def test_rejects_root_execution(self) -> None:
        with patch("packages.security_foundation.zero_trust.os.getuid", return_value=0):
            with self.assertRaises(PermissionError):
                ejecutar_modulo_aislado(b"evidence")


class PQCTests(unittest.TestCase):
    def test_ml_dsa_65_sign_and_verify(self) -> None:
        signer = MLDSA65EvidenceSigner.generate()
        evidence = b"NEXUS synthetic evidence"
        bundle = signer.sign_evidence(evidence)
        self.assertEqual(bundle.algorithm, "ML-DSA-65")
        self.assertTrue(signer.verify_evidence(evidence, bundle))
        self.assertFalse(signer.verify_evidence(evidence + b"tampered", bundle))


class SensorFusionTests(unittest.TestCase):
    def test_temporal_correlation_score(self) -> None:
        satellite = [
            {"timestamp_utc": 100.0},
            {"timestamp_utc": 200.0},
        ]
        network = [
            {"timestamp_utc": 100.0},
            {"timestamp_utc": 201.0},
        ]
        score = fusionar_sensores_inteligencia(satellite, network)
        self.assertGreater(score, 50.0)
        self.assertLessEqual(score, 100.0)

    def test_empty_stream_has_zero_score(self) -> None:
        self.assertEqual(fusionar_sensores_inteligencia([], []), 0.0)


class HardwareAuditTests(unittest.TestCase):
    def test_chain_detects_file_tampering_and_anchor_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            anchor = SoftwareAnchor()
            audit = BitacoraEndurecidaHardware(path, anchor)
            first = audit.inyectar_log_militar("agent-1", "ingest")
            second = audit.inyectar_log_militar("agent-1", "analyze")
            self.assertNotEqual(first, second)
            self.assertEqual(anchor.read(), second)
            self.assertEqual(audit.verify_chain(), second)

            lines = path.read_text(encoding="utf-8").splitlines()
            record = json.loads(lines[1])
            record["accion"] = "tampered"
            lines[1] = json.dumps(record, sort_keys=True, separators=(",", ":"))
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")

            with self.assertRaises(RuntimeError):
                audit.verify_chain()


if __name__ == "__main__":
    unittest.main()
