from __future__ import annotations

import unittest

from packages.forensic_core.hackrf_info import (
    HackRFInfoError,
    hackrf_info_argv,
    parse_hackrf_info,
)


_SAMPLE = """hackrf_info version: 2024.02.1
libhackrf version: 2024.02.1 (0.9)
Found HackRF
Index: 0
Serial number: 0000000000000000909864c8324a735f
Board ID Number: 4 (HackRF One)
Firmware Version: 2024.02.1 (API:1.08)
Part ID Number: 0xa000cb3c 0x005d474e
Hardware Revision: r10
Hardware appears to have been manufactured by Great Scott Gadgets.
Hardware supported by installed firmware:
HackRF One
Opera Cake found, address: 0
CPLD checksum: 0x1234abcd
There are 2 other devices on the same USB bus.
You may have problems at high sample rates.
"""


class HackRFInfoTests(unittest.TestCase):
    def test_parses_current_inventory_output(self) -> None:
        inventory = parse_hackrf_info(_SAMPLE)
        self.assertEqual(inventory.hackrf_info_version, "2024.02.1")
        self.assertEqual(inventory.libhackrf_version, "2024.02.1 (0.9)")
        self.assertEqual(len(inventory.devices), 1)

        device = inventory.devices[0]
        self.assertEqual(device.index, 0)
        self.assertTrue(device.is_hackrf_one)
        self.assertEqual(device.board_id, 4)
        self.assertEqual(device.board_revision, "r10")
        self.assertEqual(device.usb_api_version, "1.08")
        self.assertTrue(device.manufactured_by_gsg)
        self.assertEqual(device.supported_platforms, ("HackRF One",))
        self.assertEqual(device.operacake_addresses, (0,))
        self.assertEqual(device.cpld_checksum, "0x1234abcd")
        self.assertEqual(device.usb_bus_other_devices, 2)

    def test_no_hardware_is_empty_inventory(self) -> None:
        inventory = parse_hackrf_info(
            "hackrf_info version: 2024.02.1\n"
            "libhackrf version: 2024.02.1 (0.9)\n"
            "No HackRF boards found.\n"
        )
        self.assertEqual(inventory.devices, ())

    def test_warning_is_preserved(self) -> None:
        text = _SAMPLE.replace(
            "Hardware Revision: r10\n"
            "Hardware appears to have been manufactured by Great Scott Gadgets.\n",
            "Warning: Hardware revision not recognized by firmware.\n",
        )
        inventory = parse_hackrf_info(text)
        self.assertIsNone(inventory.devices[0].board_revision)
        self.assertEqual(
            inventory.devices[0].warnings,
            ("Hardware revision not recognized by firmware.",),
        )

    def test_self_test_failure_is_not_silently_accepted(self) -> None:
        with self.assertRaisesRegex(HackRFInfoError, "self-test failed"):
            parse_hackrf_info(_SAMPLE + "Self-test FAIL:\nRF path test failed\n")

    def test_requires_complete_device_identity(self) -> None:
        with self.assertRaisesRegex(HackRFInfoError, "missing firmware version"):
            parse_hackrf_info(
                "Found HackRF\n"
                "Index: 0\n"
                "Board ID Number: 4 (HackRF One)\n"
                "Part ID Number: 0xa000cb3c 0x005d474e\n"
            )

    def test_inventory_command_is_only_hackrf_info(self) -> None:
        self.assertEqual(hackrf_info_argv("/usr/bin/hackrf_info"), ("/usr/bin/hackrf_info",))


if __name__ == "__main__":
    unittest.main()
