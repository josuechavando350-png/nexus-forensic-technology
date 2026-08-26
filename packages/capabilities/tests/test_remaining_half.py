from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import unittest

from packages.forensic_core.advanced_graph import connected_components, degree_centrality, jaccard_neighbors
from packages.forensic_core.legal import LegalBasis, admissibility_flags, authority_required, evidence_checklist
from packages.forensic_core.nlp import Stylometry, cosine_text_similarity, normalize_text, scam_script_overlap
from packages.forensic_core.security import RetentionPolicy, hmac_sha256_hex, redact_secrets, sha3_256_hex, verify_backup_manifest, verify_hmac_sha256
from packages.forensic_core.simulation import AuthorizedSimulationPlan, SimulationStep, evaluate_control_results
from packages.forensic_core.streaming import Event, detect_sequence, weighted_sensor_fusion
from packages.integrations.auth import oidc_discovery_request, webauthn_assertion_payload
from packages.integrations.crypto_ops import openssl_sign_command, openssl_verify_command
from packages.integrations.defensive_cli import osquery_local_command, volatility_command, yara_scan_command
from packages.integrations.platforms import opencti_indicator_request, qdrant_search_request, thehive_case_request
from packages.integrations.security_services import pkcs11_uri, restic_check_command, s3_object_lock_configuration_request
from packages.integrations.specs import CommandSpec, RequestSpec
from packages.integrations.web_intel import dig_dns_command, parse_nmap_xml, public_web_request


class RemainingHalfBehaviorTests(unittest.TestCase):
    def test_nlp_similarity_and_stylometry(self) -> None:
        self.assertEqual(normalize_text("ÁRBOL, árbol!"), "árbol árbol")
        self.assertGreater(cosine_text_similarity("alpha beta beta", "alpha beta"), 0.9)
        style = Stylometry.from_text("Uno dos. Tres!")
        self.assertEqual(style.words, 3)
        self.assertEqual(style.sentences, 2)
        self.assertEqual(scam_script_overlap("Paga ahora para liberar", ("paga ahora", "otro")), ("paga ahora",))

    def test_graph_analytics_are_deterministic(self) -> None:
        graph = {"a": {"b"}, "b": {"a", "c"}, "c": {"b"}, "x": set()}
        self.assertEqual(connected_components(graph), (("a", "b", "c"), ("x",)))
        self.assertEqual(degree_centrality(graph)["b"], 2 / 3)
        self.assertEqual(jaccard_neighbors(graph, "a", "c"), 1.0)

    def test_legal_controls_fail_closed(self) -> None:
        basis = LegalBasis("MX", "court-order-1", "forensic review")
        self.assertTrue(basis.is_active(datetime.now(timezone.utc)))
        self.assertTrue(authority_required("unknown_action", {}))
        self.assertEqual(evidence_checklist(("hash", "source"), {"hash"}), {"hash": True, "source": False})
        self.assertEqual(admissibility_flags(integrity_verified=True, provenance_complete=False, authorization_verified=True), ("provenance_incomplete",))

    def test_security_primitives(self) -> None:
        self.assertIn("[REDACTED]", redact_secrets("api_key=secret"))
        self.assertEqual(len(sha3_256_hex(b"x")), 64)
        mac = hmac_sha256_hex(b"k", b"data")
        self.assertTrue(verify_hmac_sha256(b"k", b"data", mac))
        RetentionPolicy(True, 30)
        expected = {"a": sha256(b"one").hexdigest(), "b": sha256(b"two").hexdigest()}
        self.assertEqual(verify_backup_manifest({"a": b"one", "b": b"bad"}, expected), ("b",))

    def test_streaming_and_sensor_fusion(self) -> None:
        now = datetime.now(timezone.utc)
        events = (Event(now, "login", 1), Event(now, "download", 2))
        self.assertTrue(detect_sequence(events, ("login", "download")))
        self.assertEqual(weighted_sensor_fusion(((10.0, 1.0), (20.0, 3.0))), 17.5)

    def test_defensive_cli_is_shell_free_and_read_only(self) -> None:
        yara = yara_scan_command("rules.yar", "sample.bin")
        self.assertIsInstance(yara, CommandSpec)
        self.assertEqual(yara.argv[0], "yara")
        self.assertTrue(yara.read_only)
        self.assertEqual(volatility_command("ram.raw", "windows.pslist").argv[-1], "windows.pslist")
        self.assertRaises(ValueError, osquery_local_command, "delete from processes")

    def test_platform_request_contracts(self) -> None:
        hive = thehive_case_request("https://hive.example/", "case 1", "token")
        self.assertIsInstance(hive, RequestSpec)
        self.assertIn("case%201", hive.url)
        opencti = opencti_indicator_request("https://cti.example/", "id-1", "token")
        self.assertEqual(json.loads(opencti.body or b"{}")["variables"]["id"], "id-1")
        qdrant = qdrant_search_request("https://q.example/", "cases", (0.1, 0.2), 3)
        self.assertEqual(json.loads(qdrant.body or b"{}")["limit"], 3)

    def test_security_service_contracts(self) -> None:
        request = s3_object_lock_configuration_request("https://s3.example", "evidence", 365)
        self.assertIn(b"<Mode>COMPLIANCE</Mode>", request.body or b"")
        self.assertEqual(restic_check_command("/repo").argv[-1], "check")
        self.assertTrue(pkcs11_uri("forensic-hsm", "signing-key").startswith("pkcs11:"))

    def test_auth_and_web_intel_contracts(self) -> None:
        discovery = oidc_discovery_request("https://id.example")
        self.assertTrue(discovery.url.endswith("/.well-known/openid-configuration"))
        payload = webauthn_assertion_payload(challenge="challenge-1", credential_id="cred-1", client_data_json="client", authenticator_data="auth", signature="sig")
        self.assertEqual(json.loads(payload)["credential_id"], "cred-1")
        self.assertEqual(dig_dns_command("example.com", "AAAA").argv[-1], "AAAA")
        self.assertEqual(public_web_request("https://example.com").method, "GET")
        xml = "<nmaprun><host><status state='up'/><address addr='203.0.113.10'/><ports><port portid='443'><service name='https'/></port></ports></host></nmaprun>"
        records = parse_nmap_xml(xml)
        self.assertEqual(records[0].services, ((443, "https"),))

    def test_crypto_command_contracts_are_argument_arrays(self) -> None:
        sign = openssl_sign_command("key.pem", "evidence.bin", "evidence.sig")
        verify = openssl_verify_command("pub.pem", "evidence.bin", "evidence.sig")
        self.assertFalse(sign.read_only)
        self.assertTrue(verify.read_only)
        self.assertEqual(sign.argv[:3], ("openssl", "dgst", "-sha256"))

    def test_authorized_simulation_is_lab_only(self) -> None:
        step = SimulationStep("T1059", "lab-host-1", "process-monitoring")
        plan = AuthorizedSimulationPlan("auth-1", True, (step,))
        self.assertEqual(evaluate_control_results(plan, {"T1059": True}), {"T1059": True})
        with self.assertRaises(ValueError):
            AuthorizedSimulationPlan("auth-1", False, (step,))


if __name__ == "__main__":
    unittest.main()
