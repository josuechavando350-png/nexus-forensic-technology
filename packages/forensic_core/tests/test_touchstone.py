from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from packages.forensic_core.touchstone import TouchstoneError, load_touchstone, parse_touchstone


class TouchstoneTests(unittest.TestCase):
    def test_parses_v1_two_port_ri_in_standard_21_12_order(self) -> None:
        network = parse_touchstone(
            "# GHz S RI R 50\n"
            "1.0 1 0 0.5 0.1 0.4 -0.1 0.9 0\n"
            "2.0 0.9 0 0.45 0.05 0.35 -0.05 0.8 0\n",
            filename="measurement.s2p",
        )
        self.assertEqual(network.version, "1.0")
        self.assertEqual(network.ports, 2)
        self.assertEqual(network.parameter_labels(), ("S11", "S21", "S12", "S22"))
        self.assertEqual(network.points[0].frequency_hz, 1e9)
        self.assertEqual(network.points[0].parameters[1], complex(0.5, 0.1))
        self.assertEqual(network.reference_ohms, (50.0, 50.0))

    def test_parses_order_independent_option_line(self) -> None:
        network = parse_touchstone(
            "# S R 100 GHz RI\n1 1 0 0.5 0 0.25 0 0.1 0\n",
            filename="rohde-schwarz.s2p",
        )
        self.assertEqual(network.parameter_type, "S")
        self.assertEqual(network.data_format, "RI")
        self.assertEqual(network.reference_ohms, (100.0, 100.0))
        self.assertEqual(network.points[0].frequency_hz, 1e9)

    def test_detects_legacy_v11_per_port_references(self) -> None:
        network = parse_touchstone(
            "# MHz S MA R 50 75\n100 1 0 0.5 90 0.25 -90 0.1 180\n",
            filename="anritsu.s2p",
        )
        self.assertEqual(network.version, "1.1")
        self.assertEqual(network.reference_ohms, (50.0, 75.0))
        self.assertAlmostEqual(network.points[0].parameters[1].real, 0.0, places=12)
        self.assertAlmostEqual(network.points[0].parameters[1].imag, 0.5, places=12)

    def test_parses_v2_reference_and_12_21_order(self) -> None:
        network = parse_touchstone(
            "[Version] 2.1\n"
            "# GHz S DB R 50\n"
            "[Number of Ports] 2\n"
            "[Two-Port Data Order] 12_21\n"
            "[Number of Frequencies] 1\n"
            "[Matrix Format] Full\n"
            "[Reference] 50 75\n"
            "[Network Data]\n"
            "1 -3 0 -20 90 -30 -90 -6 180\n"
            "[End]\n",
            filename="network.s2p",
        )
        self.assertEqual(network.version, "2.1")
        self.assertEqual(network.parameter_labels(), ("S11", "S12", "S21", "S22"))
        self.assertEqual(network.reference_ohms, (50.0, 75.0))
        self.assertAlmostEqual(abs(network.points[0].parameters[0]), 10 ** (-3 / 20), places=12)

    def test_uses_row_major_order_for_three_port_full_matrix(self) -> None:
        network = parse_touchstone(
            "# GHz S RI R 50\n"
            "1 1 0 2 0 3 0 4 0 5 0 6 0 7 0 8 0 9 0\n",
            filename="matrix.s3p",
        )
        self.assertEqual(
            network.parameter_labels(),
            ("S11", "S12", "S13", "S21", "S22", "S23", "S31", "S32", "S33"),
        )
        self.assertEqual(network.points[0].parameters[5], complex(6, 0))

    def test_rejects_port_count_mismatch_and_sparse_matrix(self) -> None:
        with self.assertRaisesRegex(TouchstoneError, "disagree"):
            parse_touchstone(
                "[Version] 2.0\n# GHz S RI R 50\n[Number of Ports] 3\n",
                filename="bad.s2p",
            )
        with self.assertRaisesRegex(TouchstoneError, "Lower/Upper"):
            parse_touchstone(
                "[Version] 2.0\n# GHz S RI R 50\n[Number of Ports] 2\n[Matrix Format] Lower\n",
                filename="bad.s2p",
            )

    def test_rejects_missing_v2_required_keywords(self) -> None:
        with self.assertRaisesRegex(TouchstoneError, "Two-Port Data Order"):
            parse_touchstone(
                "[Version] 2.0\n# GHz S RI R 50\n[Number of Ports] 2\n"
                "[Number of Frequencies] 1\n[Network Data]\n1 1 0 1 0 1 0 1 0\n[End]\n",
                filename="bad.s2p",
            )
        with self.assertRaisesRegex(TouchstoneError, "Number of Ports"):
            parse_touchstone(
                "[Version] 2.1\n# GHz S RI R 50\n[Number of Frequencies] 1\n"
                "[Network Data]\n1 1 0\n[End]\n",
                filename="bad.s1p",
            )
        with self.assertRaisesRegex(TouchstoneError, "requires \[End\]"):
            parse_touchstone(
                "[Version] 2.1\n# GHz S RI R 50\n[Number of Ports] 1\n"
                "[Number of Frequencies] 1\n[Network Data]\n1 1 0\n",
                filename="network.ts",
            )

    def test_rejects_version_keyword_after_option_line(self) -> None:
        with self.assertRaisesRegex(TouchstoneError, "must precede"):
            parse_touchstone(
                "# GHz S RI R 50\n[Version] 2.1\n[Number of Ports] 1\n",
                filename="bad.s1p",
            )

    def test_rejects_incomplete_nonincreasing_and_nonfinite_data(self) -> None:
        with self.assertRaisesRegex(TouchstoneError, "complete frequency blocks"):
            parse_touchstone("# GHz S RI R 50\n1 1 0 1\n", filename="bad.s2p")
        with self.assertRaisesRegex(TouchstoneError, "strictly increasing"):
            parse_touchstone(
                "# GHz S RI R 50\n1 1 0 1 0 1 0 1 0\n1 1 0 1 0 1 0 1 0\n",
                filename="bad.s2p",
            )
        with self.assertRaisesRegex(TouchstoneError, "finite numeric"):
            parse_touchstone("# GHz S RI R 50\n1 nan 0\n", filename="bad.s1p")

    def test_rejects_g_or_h_parameters_outside_two_port_domain(self) -> None:
        with self.assertRaisesRegex(TouchstoneError, "two-port"):
            parse_touchstone("# GHz H RI R 50\n1 1 0\n", filename="bad.s1p")

    def test_loads_bounded_local_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "capture.s1p"
            path.write_text("# MHz S RI R 50\n100 0.1 -0.2\n", encoding="utf-8")
            network = load_touchstone(path)
        self.assertEqual(network.ports, 1)
        self.assertEqual(network.parameter_labels(), ("S11",))


if __name__ == "__main__":
    unittest.main()
