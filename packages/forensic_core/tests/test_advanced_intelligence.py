from __future__ import annotations

import unittest

from packages.forensic_core.advanced_intelligence import (
    AuthorizedAcquisitionRegistry,
    BehavioralNLPProfiler,
    DeterministicEntityResolver,
    IdentityRecord,
    IntelligenceValidationError,
    MobileExploitTelemetryAnalyzer,
    PassiveCTIHarvester,
    PassiveOSINTArchive,
    deduplicate_iocs,
    stable_identity_fingerprint,
)


class AdvancedIntelligenceTests(unittest.TestCase):
    def test_mobile_telemetry_requires_multiple_indicators(self) -> None:
        analyzer = MobileExploitTelemetryAnalyzer()
        finding = analyzer.analyze("Kernel panic after use-after-free and pointer authentication failure")
        self.assertTrue(finding.suspicious)
        self.assertGreaterEqual(finding.score, 2.0 / 3.0)

    def test_mobile_telemetry_rejects_blank_input(self) -> None:
        with self.assertRaises(IntelligenceValidationError):
            MobileExploitTelemetryAnalyzer().analyze("   ")

    def test_entity_resolution_links_shared_phone_and_email(self) -> None:
        resolver = DeterministicEntityResolver()
        left = IdentityRecord(source="case-a", alias="alpha", email="A@EXAMPLE.COM", phone="+5213120000000")
        right = IdentityRecord(source="case-b", alias="beta", email="a@example.com", phone="+5213120000000")
        result = resolver.compare(left, right)
        self.assertTrue(result.linked)
        self.assertEqual(result.confidence, 0.75)
        self.assertEqual(result.shared_attributes, ("email", "phone"))

    def test_behavior_profile_is_deterministic(self) -> None:
        profiler = BehavioralNLPProfiler()
        first = profiler.profile("Paga hoy paga ahora")
        second = profiler.profile("Paga hoy paga ahora")
        self.assertEqual(first, second)
        self.assertAlmostEqual(profiler.cosine_similarity(first, second), 1.0)

    def test_authorized_acquisition_manifest_hashes_image(self) -> None:
        manifest = AuthorizedAcquisitionRegistry().register(
            device_id="device-001",
            examiner_id="examiner-007",
            authorization_reference="AUTH-2026-001",
            image_bytes=b"forensic-image-bytes",
        )
        self.assertEqual(len(manifest.image_sha256), 64)
        self.assertEqual(manifest.byte_length, 20)

    def test_passive_cti_extracts_supplied_iocs(self) -> None:
        text = (
            "contact bad@example.test from 192.0.2.44 hash "
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        )
        harvested = PassiveCTIHarvester().harvest(text, source="public-report")
        self.assertEqual({item.kind for item in harvested}, {"email", "ipv4", "sha256"})
        self.assertEqual(len(deduplicate_iocs(harvested + harvested)), 3)

    def test_passive_osint_records_provenance_without_fetching(self) -> None:
        record = PassiveOSINTArchive().record(
            url="https://example.org/archive/1",
            observed_at="2026-08-27T00:00:00Z",
            content=b"archived public content",
        )
        self.assertEqual(len(record.content_sha256), 64)

    def test_stable_identity_fingerprint_is_order_independent(self) -> None:
        first = IdentityRecord(source="b", email="b@example.test")
        second = IdentityRecord(source="a", phone="+5213120000000")
        self.assertEqual(
            stable_identity_fingerprint((first, second)),
            stable_identity_fingerprint((second, first)),
        )


if __name__ == "__main__":
    unittest.main()
