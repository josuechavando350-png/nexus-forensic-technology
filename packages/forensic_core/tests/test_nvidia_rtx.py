from __future__ import annotations

import unittest

from packages.forensic_core.nvidia_rtx import (
    NvidiaSmiError,
    nvidia_smi_query_argv,
    parse_nvidia_smi_csv,
)


class NvidiaRtxTests(unittest.TestCase):
    def test_parses_rtx_4090_telemetry(self) -> None:
        rows = parse_nvidia_smi_csv(
            "NVIDIA GeForce RTX 4090, GPU-1234, 580.88, 24564, 1024, 61, 182.75\n"
        )
        self.assertEqual(len(rows), 1)
        gpu = rows[0]
        self.assertTrue(gpu.is_rtx_4090)
        self.assertEqual(gpu.memory_total_mib, 24564)
        self.assertEqual(gpu.memory_used_mib, 1024)
        self.assertEqual(gpu.temperature_c, 61)
        self.assertEqual(gpu.power_draw_w, 182.75)

    def test_multiple_gpus_preserve_order(self) -> None:
        rows = parse_nvidia_smi_csv(
            "NVIDIA GeForce RTX 4090, GPU-A, 580.88, 24564, 100, 41, 50.0\n"
            "NVIDIA RTX A6000, GPU-B, 580.88, 49140, 200, 44, 61.5\n"
        )
        self.assertEqual([item.uuid for item in rows], ["GPU-A", "GPU-B"])
        self.assertFalse(rows[1].is_rtx_4090)

    def test_rejects_wrong_field_count(self) -> None:
        with self.assertRaisesRegex(NvidiaSmiError, "expected 7 fields"):
            parse_nvidia_smi_csv("NVIDIA GeForce RTX 4090, GPU-1234\n")

    def test_rejects_invalid_numeric_telemetry(self) -> None:
        with self.assertRaisesRegex(NvidiaSmiError, "memory.total"):
            parse_nvidia_smi_csv(
                "NVIDIA GeForce RTX 4090, GPU-1234, 580.88, unknown, 0, 40, 20.0\n"
            )

    def test_query_is_read_only_and_explicit(self) -> None:
        argv = nvidia_smi_query_argv("/usr/bin/nvidia-smi")
        self.assertEqual(argv[0], "/usr/bin/nvidia-smi")
        self.assertIn("--query-gpu=name,uuid,driver_version,memory.total,memory.used,temperature.gpu,power.draw", argv)
        self.assertEqual(argv[-1], "--format=csv,noheader,nounits")


if __name__ == "__main__":
    unittest.main()
