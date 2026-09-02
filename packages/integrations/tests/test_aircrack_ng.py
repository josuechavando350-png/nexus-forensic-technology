from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from packages.integrations.aircrack_ng import (
    AirodumpParseError,
    load_airodump_csv,
    parse_airodump_csv,
)


_SAMPLE = """BSSID, First time seen, Last time seen, channel, Speed, Privacy, Cipher, Authentication, Power, # beacons, # IV, LAN IP, ID-length, ESSID, Key
AA:BB:CC:DD:EE:FF, 2026-09-01 10:00:00, 2026-09-01 10:02:00, 6, 54, WPA2, CCMP, PSK, -42, 120, 0, 0.  0.  0.  0, 9, OfficeNet,

Station MAC, First time seen, Last time seen, Power, # packets, BSSID, Probed ESSIDs
11:22:33:44:55:66, 2026-09-01 10:00:10, 2026-09-01 10:01:55, -55, 18, AA:BB:CC:DD:EE:FF, GuestNet
22:33:44:55:66:77, 2026-09-01 10:00:20, 2026-09-01 10:01:45, -70, 3, (not associated), CafeWiFi, AirportFree
"""


class AirodumpParserTests(unittest.TestCase):
    def test_parses_access_points_and_stations(self) -> None:
        snapshot = parse_airodump_csv(_SAMPLE)
        self.assertEqual(len(snapshot.access_points), 1)
        self.assertEqual(len(snapshot.stations), 2)

        access_point = snapshot.access_points[0]
        self.assertEqual(access_point.bssid, "AA:BB:CC:DD:EE:FF")
        self.assertEqual(access_point.channel, 6)
        self.assertEqual(access_point.privacy, "WPA2")
        self.assertEqual(access_point.essid, "OfficeNet")

        associated = snapshot.stations[0]
        self.assertEqual(associated.bssid, "AA:BB:CC:DD:EE:FF")
        self.assertEqual(associated.probed_essids, ("GuestNet",))

        unassociated = snapshot.stations[1]
        self.assertIsNone(unassociated.bssid)
        self.assertEqual(unassociated.probed_essids, ("CafeWiFi", "AirportFree"))

    def test_rejects_malformed_mac(self) -> None:
        bad = _SAMPLE.replace("AA:BB:CC:DD:EE:FF", "not-a-mac", 1)
        with self.assertRaisesRegex(AirodumpParseError, "invalid BSSID"):
            parse_airodump_csv(bad)

    def test_rejects_truncated_row(self) -> None:
        bad = "BSSID, First time seen, Last time seen, channel\nAA:BB:CC:DD:EE:FF, now\n"
        with self.assertRaisesRegex(AirodumpParseError, "truncated access-point row"):
            parse_airodump_csv(bad)

    def test_requires_recognized_header(self) -> None:
        with self.assertRaisesRegex(AirodumpParseError, "recognized header"):
            parse_airodump_csv("AA:BB:CC:DD:EE:FF,unexpected\n")

    def test_loads_local_export(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "capture-01.csv"
            path.write_text(_SAMPLE, encoding="utf-8")
            snapshot = load_airodump_csv(path)
        self.assertEqual(snapshot.access_points[0].essid, "OfficeNet")

    def test_missing_file_is_explicit(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_airodump_csv("/definitely/missing/airodump.csv")


if __name__ == "__main__":
    unittest.main()
