from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from packages.integrations.defensive_cli import volatility_command


@unittest.skipUnless(os.environ.get("NEXUS_RUN_VOLATILITY_E2E") == "1", "Volatility E2E disabled")
class VolatilityE2ETests(unittest.TestCase):
    def test_volatility_banner_scan_against_real_cli(self) -> None:
        synthetic_banner = b"Linux version 6.8.0-nexus-certification #1 SMP PREEMPT_DYNAMIC\x00"
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "synthetic-memory.raw"
            image_path.write_bytes(b"\x00" * 4096 + synthetic_banner + b"\x00" * 4096)

            spec = volatility_command(str(image_path), "banners.Banners")
            self.assertEqual(spec.argv[0], "vol")
            self.assertEqual(spec.argv[1], "-f")
            self.assertEqual(spec.argv[2], str(image_path))
            self.assertEqual(spec.argv[3], "banners.Banners")

            completed = subprocess.run(
                list(spec.argv),
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
                shell=False,
            )

            combined_output = f"{completed.stdout}\n{completed.stderr}"
            self.assertEqual(completed.returncode, 0, combined_output)
            self.assertIn("Linux version 6.8.0-nexus-certification", combined_output)


if __name__ == "__main__":
    unittest.main()
