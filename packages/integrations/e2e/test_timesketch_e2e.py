from __future__ import annotations

import os
import unittest

from packages.integrations.timesketch import create_timesketch_client, list_sketch_summaries


@unittest.skipUnless(os.getenv("NEXUS_RUN_TIMESKETCH_E2E") == "1", "live Timesketch E2E disabled")
class TimesketchE2ETests(unittest.TestCase):
    def test_authenticated_server_round_trip(self) -> None:
        host = os.environ.get("NEXUS_TIMESKETCH_URL", "http://127.0.0.1:5000")
        username = os.environ.get("NEXUS_TIMESKETCH_USER", "dev")
        password = os.environ.get("NEXUS_TIMESKETCH_PASSWORD", "dev")
        api = create_timesketch_client(host, username, password, verify=False)
        summaries = list_sketch_summaries(api)
        self.assertIsInstance(summaries, tuple)


if __name__ == "__main__":
    unittest.main()
