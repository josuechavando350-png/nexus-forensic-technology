from __future__ import annotations

import os
import time
import unittest
from typing import Callable

import requests

from packages.integrations.cti import MISPAdapter, OpenCTIAdapter


def _wait_until(check: Callable[[], bool], *, timeout_s: float = 180.0, interval_s: float = 2.0) -> None:
    deadline = time.monotonic() + timeout_s
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            if check():
                return
        except Exception as exc:
            last_error = exc
        time.sleep(interval_s)
    raise RuntimeError(f"service did not become ready within {timeout_s:.0f}s") from last_error


@unittest.skipUnless(os.environ.get("NEXUS_RUN_OPENCTI_E2E") == "1", "OpenCTI E2E disabled")
class OpenCTIE2ETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base_url = os.environ.get("NEXUS_OPENCTI_URL", "http://127.0.0.1:8080")
        cls.token = os.environ.get("NEXUS_OPENCTI_TOKEN", "11111111-1111-4111-8111-111111111111")
        _wait_until(cls._ready)

    @classmethod
    def _ready(cls) -> bool:
        response = requests.get(
            f"{cls.base_url}/health",
            params={"health_access_key": "22222222-2222-4222-8222-222222222222"},
            timeout=5,
        )
        return response.status_code == 200

    def test_opencti_graphql_adapter_against_real_platform(self) -> None:
        adapter = OpenCTIAdapter(
            http_client=requests.Session(),
            endpoint=f"{self.base_url}/graphql",
            token=self.token,
        )
        data = adapter.graphql(query="query NexusCertification { me { id name user_email } }")
        self.assertIn("me", data)
        self.assertIsInstance(data["me"], dict)
        self.assertTrue(data["me"].get("id"))
        self.assertEqual(data["me"].get("user_email"), "admin@nexus.test")


@unittest.skipUnless(os.environ.get("NEXUS_RUN_MISP_E2E") == "1", "MISP E2E disabled")
class MISPE2ETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from pymisp import PyMISP

        cls.base_url = os.environ.get("NEXUS_MISP_URL", "http://127.0.0.1:8081")
        cls.key = os.environ.get("NEXUS_MISP_KEY", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
        _wait_until(cls._ready)
        cls.pymisp = PyMISP(cls.base_url, cls.key, ssl=False, timeout=30)

    @classmethod
    def _ready(cls) -> bool:
        response = requests.get(
            f"{cls.base_url}/servers/getVersion",
            headers={
                "Authorization": cls.key,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=5,
        )
        return response.status_code == 200

    def test_misp_adapter_against_real_platform(self) -> None:
        from pymisp import MISPAttribute, MISPEvent

        event = MISPEvent()
        event.info = "NEXUS CTI certification synthetic event"
        event.distribution = 0
        event.threat_level_id = 4
        event.analysis = 0
        created = self.pymisp.add_event(event, pythonify=True)
        self.assertTrue(created.id)

        attribute = MISPAttribute()
        attribute.type = "domain"
        attribute.category = "Network activity"
        attribute.value = "nexus-certification.invalid"
        attribute.to_ids = False
        added = self.pymisp.add_attribute(created.id, attribute, pythonify=True)
        self.assertEqual(added.value, "nexus-certification.invalid")

        adapter = MISPAdapter(self.pymisp)
        results = adapter.search_attributes(
            value="nexus-certification.invalid",
            attribute_type="domain",
            limit=10,
        )
        values = {item.get("value") for item in results}
        self.assertIn("nexus-certification.invalid", values)

        self.pymisp.delete_event(created.id)


if __name__ == "__main__":
    unittest.main()
