from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from packages.integrations.forensics_cli import sleuthkit_fls


@unittest.skipUnless(os.environ.get("NEXUS_RUN_SLEUTHKIT_E2E") == "1", "Sleuth Kit E2E disabled")
class SleuthKitE2ETests(unittest.TestCase):
    def test_fls_lists_file_from_real_ext4_image(self) -> None:
        with tempfile.TemporaryDirectory(prefix="nexus-sleuthkit-") as temporary_directory:
            workspace = Path(temporary_directory)
            image_path = workspace / "evidence.ext4"
            source_path = workspace / "nexus-evidence.txt"
            source_path.write_text("NEXUS synthetic forensic certification artifact\n", encoding="utf-8")

            subprocess.run(
                ["truncate", "-s", "16M", str(image_path)],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["mkfs.ext4", "-F", str(image_path)],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["debugfs", "-w", "-R", f"write {source_path} nexus-evidence.txt", str(image_path)],
                check=True,
                capture_output=True,
                text=True,
            )

            listing = sleuthkit_fls(image_path)

            self.assertIn("nexus-evidence.txt", listing)
            self.assertNotIn(str(source_path), listing)


if __name__ == "__main__":
    unittest.main()
