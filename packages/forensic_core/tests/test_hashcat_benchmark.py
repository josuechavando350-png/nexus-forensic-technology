from __future__ import annotations

import unittest

from packages.forensic_core.hashcat_benchmark import (
    HashcatBenchmarkError,
    hashcat_benchmark_argv,
    parse_hashcat_benchmark,
)


class HashcatBenchmarkTests(unittest.TestCase):
    def test_parses_machine_readable_benchmark(self) -> None:
        records = parse_hashcat_benchmark(
            "# version: v7.1.2\n"
            "1:0:1683:4513:55.02:10240000000\n"
            "2:0:1657:4513:55.82:10183130102\n"
            "Started: Tue Sep  1 20:00:00 2026\n"
            "Stopped: Tue Sep  1 20:00:05 2026\n"
        )
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].device_id, 1)
        self.assertEqual(records[0].metadata_fields, ("0", "1683", "4513"))
        self.assertEqual(records[0].execution_runtime_ms, 55.02)
        self.assertEqual(records[0].hashes_per_second, 10_240_000_000)

    def test_benchmark_command_has_no_attack_inputs(self) -> None:
        argv = hashcat_benchmark_argv(0, "/usr/bin/hashcat")
        self.assertEqual(
            argv,
            (
                "/usr/bin/hashcat",
                "--benchmark",
                "--hash-type",
                "0",
                "--machine-readable",
                "--quiet",
            ),
        )

    def test_rejects_invalid_hash_mode(self) -> None:
        with self.assertRaises(ValueError):
            hashcat_benchmark_argv(-1)
        with self.assertRaises(TypeError):
            hashcat_benchmark_argv(True)

    def test_rejects_malformed_benchmark(self) -> None:
        with self.assertRaises(HashcatBenchmarkError):
            parse_hashcat_benchmark("device:bad\n")

    def test_rejects_negative_values(self) -> None:
        with self.assertRaisesRegex(HashcatBenchmarkError, "negative"):
            parse_hashcat_benchmark("1:0:10.0:-2\n")


if __name__ == "__main__":
    unittest.main()
