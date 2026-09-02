import unittest

from packages.capabilities.specification import (
    CAPABILITY_SPECIFICATIONS,
    canonical_audit_summary,
    missing_per_capability_evidence_ids,
    missing_specification_ids,
    require_canonical_specification_complete,
)


RECOVERED_SPEC_IDS = {104, 131, 134, 181, 185, 219, 224, 247, 253, 262, 295, 298}
EVIDENCED_CAPABILITY_IDS = {253, 298}


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

    def test_recovered_document_specs_are_explicit_and_sourced(self) -> None:
        recovered = {
            capability_id
            for capability_id, row in CAPABILITY_SPECIFICATIONS.items()
            if row.is_specified
        }
        self.assertEqual(recovered, RECOVERED_SPEC_IDS)
        for capability_id in sorted(RECOVERED_SPEC_IDS):
            with self.subTest(capability_id=capability_id):
                row = CAPABILITY_SPECIFICATIONS[capability_id]
                self.assertTrue(row.title)
                self.assertTrue(row.description)
                self.assertTrue(row.acceptance_criteria)
                self.assertIn("NEXUS_", row.specification_source or "")

    def test_only_individually_proven_capabilities_get_evidence_refs(self) -> None:
        evidenced = {
            capability_id
            for capability_id, row in CAPABILITY_SPECIFICATIONS.items()
            if row.has_per_capability_evidence
        }
        self.assertEqual(evidenced, EVIDENCED_CAPABILITY_IDS)
        for capability_id in sorted(EVIDENCED_CAPABILITY_IDS):
            self.assertTrue(CAPABILITY_SPECIFICATIONS[capability_id].evidence_refs)

    def test_current_audit_exposes_remaining_spec_and_evidence_debt(self) -> None:
        self.assertEqual(len(missing_specification_ids()), 292)
        self.assertEqual(len(missing_per_capability_evidence_ids()), 302)
        self.assertEqual(
            canonical_audit_summary(),
            {
                "catalog_total": 304,
                "specified": 12,
                "spec_missing": 292,
                "per_capability_evidenced": 2,
                "per_capability_evidence_missing": 302,
            },
        )

    def test_full_certification_gate_fails_closed(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "full capability certification is blocked"):
            require_canonical_specification_complete()


if __name__ == "__main__":
    unittest.main()
