# Audit 020 — HackRF One read-only inventory

## Scope

Real integration with Great Scott Gadgets' `hackrf_info` utility. The module inventories connected HackRF hardware and parses the current vendor output format. It does not invoke `hackrf_transfer`, `hackrf_sweep`, clock configuration, firmware flashing, RF capture, or RF transmission.

## Vendor behavior verified

The current upstream `hackrf_info` implementation reports tool/libhackrf versions, device index and serial number, board ID, firmware/USB API version, part ID, hardware revision, manufacturer indication, supported hardware platforms, optional Opera Cake addresses, optional CPLD checksum, self-test failures, and USB-bus sharing information.

## Implementation checks

- Exact executable surface is `hackrf_info` only; there are no RF-operation arguments.
- Required device identity fields fail closed when absent.
- Board IDs and current HackRF One IDs are preserved as structured data.
- Firmware and USB API version are parsed separately.
- Hardware-revision and Great Scott Gadgets manufacturer indication are preserved without converting the latter into a cryptographic authenticity claim.
- Supported-platform, Opera Cake, CPLD, and USB-bus data are parsed when present.
- Vendor warnings are preserved.
- Vendor errors and self-test failures are explicit `HackRFInfoError` failures.
- The official no-device result is represented as an empty inventory.
- Collection has an explicit timeout and rejects non-zero process results except the vendor's documented no-board condition.

## Tests

`packages/forensic_core/tests/test_hackrf_info.py` covers current-format device inventory, no-hardware behavior, warnings, self-test failure handling, incomplete identity rejection, and exact read-only command construction.

## Certification gate

Merge only after the final diff is reviewed and all repository pull-request checks complete successfully.
