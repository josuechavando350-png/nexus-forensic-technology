import unittest

from packages.capabilities.certification import (
    AUDITED_SUPPORT_BASELINE,
    catalog_certification_summary,
    contract_only_capability_ids,
    require_full_production_certification,
)


class CatalogCertificationTests(unittest.TestCase):
    def test_audited_support_baseline_is_explicit(self) -> None:
        summary = catalog_certification_summary()
        self.assertEqual(summary.total, 304)
        self.assertEqual(summary.verified_local, AUDITED_SUPPORT_BASELINE["verified_local"])
        self.assertEqual(summary.adapter_contract, AUDITED_SUPPORT_BASELINE["adapter_contract"])
        self.assertEqual(summary.verified_local + summary.adapter_contract, summary.total)

    def test_contract_only_ids_are_not_mislabeled_as_certified(self) -> None:
        summary = catalog_certification_summary()
        pending = contract_only_capability_ids()
        self.assertEqual(len(pending), summary.adapter_contract)
        self.assertFalse(summary.fully_production_certified)
        self.assertGreater(len(pending), 0)

    def test_full_production_certification_fails_closed(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "full production certification is not satisfied"):
            require_full_production_certification()


if __name__ == "__main__":
    unittest.main()
