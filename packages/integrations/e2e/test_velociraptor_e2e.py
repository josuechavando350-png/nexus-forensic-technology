from __future__ import annotations

import os
from pathlib import Path
import unittest

from packages.integrations.velociraptor_cli import (
    velociraptor_query,
    velociraptor_version,
)


@unittest.skipUnless(
    os.environ.get("NEXUS_RUN_VELOCIRAPTOR_E2E") == "1",
    "live Velociraptor certification is disabled",
)
class VelociraptorE2ETest(unittest.TestCase):
    def setUp(self) -> None:
        executable = os.environ.get("NEXUS_VELOCIRAPTOR_BIN", "velociraptor")
        self.executable = Path(executable)

    def test_real_binary_version_and_read_only_vql(self) -> None:
        version = velociraptor_version(executable=self.executable)
        self.assertIn("0.77.2", version)

        rows = velociraptor_query(
            "host_info",
            executable=self.executable,
            timeout=60.0,
        )
        self.assertGreaterEqual(len(rows), 1)
        row = rows[0]
        self.assertIsInstance(row.get("OS"), str)
        self.assertTrue(str(row.get("OS", "")).strip())
        self.assertIsInstance(row.get("Architecture"), str)
        self.assertTrue(str(row.get("Architecture", "")).strip())

    def test_arbitrary_vql_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            velociraptor_query(
                "SELECT * FROM execve(argv=['id'])",
                executable=self.executable,
            )


if __name__ == "__main__":
    unittest.main()
