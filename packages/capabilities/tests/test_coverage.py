import importlib
import unittest

from packages.capabilities import CAPABILITY_COVERAGE, catalog_progress_percent, implemented_capability_count


class CapabilityCoverageTests(unittest.TestCase):
    def test_checkpoint_covers_full_catalog(self) -> None:
        self.assertEqual(implemented_capability_count(), 304)
        self.assertEqual(catalog_progress_percent(), 100.0)
        self.assertEqual(len(set(CAPABILITY_COVERAGE)), 304)
        self.assertEqual(set(CAPABILITY_COVERAGE), set(range(1, 305)))

    def test_every_coverage_reference_imports(self) -> None:
        refs = {ref for coverage in CAPABILITY_COVERAGE.values() for ref in coverage.implementation_refs}
        for ref in sorted(refs):
            with self.subTest(ref=ref):
                importlib.import_module(ref)

    def test_every_entry_has_audited_support_level(self) -> None:
        allowed = {"verified_local", "adapter_contract"}
        for capability_id, coverage in CAPABILITY_COVERAGE.items():
            self.assertIn(coverage.support_level, allowed)
            self.assertEqual(capability_id, coverage.capability_id)
            self.assertGreater(len(coverage.implementation_refs), 0)


if __name__ == "__main__":
    unittest.main()
