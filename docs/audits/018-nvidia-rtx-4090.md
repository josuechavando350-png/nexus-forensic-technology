# Audit 018 — NVIDIA RTX 4090 telemetry

## Scope

Read-only NVIDIA GPU inventory and health telemetry through the vendor-provided `nvidia-smi` CLI. The module specifically identifies RTX 4090 devices while remaining valid for other NVIDIA GPUs.

## Verified implementation properties

- Uses only documented query-style `nvidia-smi` arguments.
- No clock, power-limit, persistence-mode, compute-mode, reset, or device-control operations.
- Explicit telemetry schema: name, UUID, driver version, total/used memory, GPU temperature, and power draw.
- Strict CSV field-count and numeric validation.
- Preserves multi-GPU ordering and UUID identity.
- Explicit timeout and non-zero-process error handling.
- No runtime dependency beyond Python and an installed NVIDIA driver toolchain.

## Tests

`packages/forensic_core/tests/test_nvidia_rtx.py` verifies RTX 4090 identification, numeric telemetry parsing, multi-GPU ordering, malformed telemetry rejection, and exact read-only command construction.

## Certification gate

The module must pass repository compilation, forensic-core unit discovery, the global quality workflow, and all pull-request workflows before merge. The final PR diff must contain only the intended implementation, tests, and this audit record.
