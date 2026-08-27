import unittest

from packages.capabilities.specification import (
    CAPABILITY_SPECIFICATIONS,
    canonical_audit_summary,
    missing_per_capability_evidence_ids,
    missing_specification_ids,
    require_canonical_specification_complete,
)


class CapabilitySpecificationTests(unittest.TestCase):
    def test_matrix_has_exactly_304_rows(self) -> None:
        self.assertEqual(set(CAPABILITY_SPECIFICATIONS), set(range(1, 305)))
        self.assertEqual(len(CAPABILITY_SPECIFICATIONS), 304)

    def test_registry_metadata_is_carried_into_every_row(self) -> None:
        for capability_id, row in CAPABILITY_SPECIFICATIONS.items():
            with self.subTest(capability_id=capability_id):
                self.assertEqual(row.capability_id, capability_id)
                self.assertTrue(row.implementation_refs)
                self.assertIn(row.support_level, {"verified_local", "adapter_contract"})

    def test_current_audit_exposes_missing_authoritative_specs(self) -> None:
        # No authoritative 1..304 source currently exists in the repository.
        # The expected value is deliberately explicit so a future recovery of
        # that source must update both the matrix and this audited baseline.
        self.assertEqual(len(missing_specification_ids()), 304)
        self.assertEqual(len(missing_per_capability_evidence_ids()), 304)
        self.assertEqual(
            canonical_audit_summary(),
            {
                "catalog_total": 304,
                "specified": 0,
                "spec_missing": 304,
                "per_capability_evidenced": 0,
                "per_capability_evidence_missing": 304,
            },
        )

    def test_full_certification_gate_fails_closed(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "full capability certification is blocked"):
            require_canonical_specification_complete()


if __name__ == "__main__":
    unittest.main()
