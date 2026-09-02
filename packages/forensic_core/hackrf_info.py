from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass

_BOARD_ID_RE = re.compile(r"^Board ID Number:\s*(\d+)\s*\((.+)\)$")
_FIRMWARE_RE = re.compile(
    r"^Firmware Version:\s*(.*?)\s*\(API:([0-9A-Fa-f]+\.[0-9A-Fa-f]+)\)$"
)
_PART_ID_RE = re.compile(
    r"^Part ID Number:\s*(0x[0-9A-Fa-f]{8})\s+(0x[0-9A-Fa-f]{8})$"
)
_INDEX_RE = re.compile(r"^Index:\s*(\d+)$")
_CPLD_RE = re.compile(r"^CPLD checksum:\s*(0x[0-9A-Fa-f]{8})$")
_BUS_MANY_RE = re.compile(r"^There are (\d+) other devices on the same USB bus\.$")


class HackRFInfoError(RuntimeError):
    """Raised when read-only HackRF inventory cannot be collected or parsed."""


@dataclass(frozen=True, slots=True)
class HackRFDeviceInfo:
    index: int
    serial_number: str | None
    board_id: int
    board_name: str
    firmware_version: str
    usb_api_version: str
    part_id: tuple[str, str]
    board_revision: str | None
    manufactured_by_gsg: bool | None
    supported_platforms: tuple[str, ...]
    operacake_addresses: tuple[int, ...]
    cpld_checksum: str | None
    usb_bus_other_devices: int | None
    warnings: tuple[str, ...]

    @property
    def is_hackrf_one(self) -> bool:
        return self.board_id in {2, 4} or "hackrf one" in self.board_name.lower()


@dataclass(frozen=True, slots=True)
class HackRFInventory:
    hackrf_info_version: str | None
    libhackrf_version: str | None
    devices: tuple[HackRFDeviceInfo, ...]


def hackrf_info_argv(executable: str = "hackrf_info") -> tuple[str, ...]:
    """Return the vendor inventory command; it performs no RF streaming."""

    return (executable,)


def _require_device_field(value: object | None, field: str, index: int) -> object:
    if value is None:
        raise HackRFInfoError(f"device {index}: missing {field}")
    return value


def parse_hackrf_info(text: str) -> HackRFInventory:
    """Parse Great Scott Gadgets `hackrf_info` output into immutable inventory."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    tool_version: str | None = None
    library_version: str | None = None
    devices: list[HackRFDeviceInfo] = []
    current: dict[str, object] | None = None
    collecting_platforms = False

    def finish_current() -> None:
        nonlocal current, collecting_platforms
        if current is None:
            return
        index = int(_require_device_field(current.get("index"), "index", -1))
        part_id_raw = _require_device_field(current.get("part_id"), "part ID", index)
        if not (
            isinstance(part_id_raw, tuple)
            and len(part_id_raw) == 2
            and all(isinstance(item, str) for item in part_id_raw)
        ):
            raise HackRFInfoError(f"device {index}: invalid part ID")
        platforms_raw = current.get("supported_platforms", [])
        addresses_raw = current.get("operacake_addresses", [])
        warnings_raw = current.get("warnings", [])
        if not isinstance(platforms_raw, list) or not all(
            isinstance(item, str) for item in platforms_raw
        ):
            raise HackRFInfoError(f"device {index}: invalid platform list")
        if not isinstance(addresses_raw, list) or not all(
            isinstance(item, int) for item in addresses_raw
        ):
            raise HackRFInfoError(f"device {index}: invalid Opera Cake list")
        if not isinstance(warnings_raw, list) or not all(
            isinstance(item, str) for item in warnings_raw
        ):
            raise HackRFInfoError(f"device {index}: invalid warning list")

        devices.append(
            HackRFDeviceInfo(
                index=index,
                serial_number=(
                    current.get("serial_number")
                    if isinstance(current.get("serial_number"), str)
                    else None
                ),
                board_id=int(
                    _require_device_field(current.get("board_id"), "board ID", index)
                ),
                board_name=str(
                    _require_device_field(current.get("board_name"), "board name", index)
                ),
                firmware_version=str(
                    _require_device_field(
                        current.get("firmware_version"), "firmware version", index
                    )
                ),
                usb_api_version=str(
                    _require_device_field(
                        current.get("usb_api_version"), "USB API version", index
                    )
                ),
                part_id=(part_id_raw[0], part_id_raw[1]),
                board_revision=(
                    current.get("board_revision")
                    if isinstance(current.get("board_revision"), str)
                    else None
                ),
                manufactured_by_gsg=(
                    current.get("manufactured_by_gsg")
                    if isinstance(current.get("manufactured_by_gsg"), bool)
                    else None
                ),
                supported_platforms=tuple(platforms_raw),
                operacake_addresses=tuple(addresses_raw),
                cpld_checksum=(
                    current.get("cpld_checksum")
                    if isinstance(current.get("cpld_checksum"), str)
                    else None
                ),
                usb_bus_other_devices=(
                    current.get("usb_bus_other_devices")
                    if isinstance(current.get("usb_bus_other_devices"), int)
                    else None
                ),
                warnings=tuple(warnings_raw),
            )
        )
        current = None
        collecting_platforms = False

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("hackrf_info version:"):
            tool_version = line.split(":", 1)[1].strip() or None
            continue
        if line.startswith("libhackrf version:"):
            library_version = line.split(":", 1)[1].strip() or None
            continue
        if line == "No HackRF boards found.":
            finish_current()
            return HackRFInventory(tool_version, library_version, tuple(devices))
        if line == "Found HackRF":
            finish_current()
            current = {
                "supported_platforms": [],
                "operacake_addresses": [],
                "warnings": [],
            }
            continue
        if current is None:
            raise HackRFInfoError(f"line {line_number}: unexpected device data")

        if line.startswith("Error:") or line.startswith("hackrf_read_selftest() failed:"):
            raise HackRFInfoError(f"line {line_number}: {line}")
        if line == "Self-test FAIL:":
            raise HackRFInfoError(f"line {line_number}: HackRF self-test failed")
        if line.startswith("Warning:"):
            warnings = current["warnings"]
            assert isinstance(warnings, list)
            warnings.append(line.removeprefix("Warning:").strip())
            collecting_platforms = False
            continue

        match = _INDEX_RE.match(line)
        if match:
            current["index"] = int(match.group(1))
            collecting_platforms = False
            continue
        if line.startswith("Serial number:"):
            serial = line.split(":", 1)[1].strip()
            current["serial_number"] = serial or None
            collecting_platforms = False
            continue
        match = _BOARD_ID_RE.match(line)
        if match:
            current["board_id"] = int(match.group(1))
            current["board_name"] = match.group(2).strip()
            collecting_platforms = False
            continue
        match = _FIRMWARE_RE.match(line)
        if match:
            current["firmware_version"] = match.group(1).strip()
            current["usb_api_version"] = match.group(2).lower()
            collecting_platforms = False
            continue
        match = _PART_ID_RE.match(line)
        if match:
            current["part_id"] = (match.group(1).lower(), match.group(2).lower())
            collecting_platforms = False
            continue
        if line.startswith("Hardware Revision:") or line.startswith("Board Revision:"):
            current["board_revision"] = line.split(":", 1)[1].strip() or None
            collecting_platforms = False
            continue
        if line == "Hardware appears to have been manufactured by Great Scott Gadgets.":
            current["manufactured_by_gsg"] = True
            collecting_platforms = False
            continue
        if line == "Hardware does not appear to have been manufactured by Great Scott Gadgets.":
            current["manufactured_by_gsg"] = False
            collecting_platforms = False
            continue
        if line == "Hardware supported by installed firmware:":
            collecting_platforms = True
            continue
        if line.startswith("Opera Cake found, address:"):
            try:
                address = int(line.rsplit(":", 1)[1].strip())
            except ValueError as exc:
                raise HackRFInfoError(
                    f"line {line_number}: invalid Opera Cake address"
                ) from exc
            if not 0 <= address <= 7:
                raise HackRFInfoError(f"line {line_number}: invalid Opera Cake address")
            addresses = current["operacake_addresses"]
            assert isinstance(addresses, list)
            addresses.append(address)
            collecting_platforms = False
            continue
        match = _CPLD_RE.match(line)
        if match:
            current["cpld_checksum"] = match.group(1).lower()
            collecting_platforms = False
            continue
        if line == "This device is on its own USB bus.":
            current["usb_bus_other_devices"] = 0
            collecting_platforms = False
            continue
        if line == "There is 1 other device on the same USB bus.":
            current["usb_bus_other_devices"] = 1
            collecting_platforms = False
            continue
        match = _BUS_MANY_RE.match(line)
        if match:
            current["usb_bus_other_devices"] = int(match.group(1))
            collecting_platforms = False
            continue
        if line == "You may have problems at high sample rates.":
            collecting_platforms = False
            continue
        if collecting_platforms:
            platforms = current["supported_platforms"]
            assert isinstance(platforms, list)
            platforms.append(line)
            continue
        raise HackRFInfoError(f"line {line_number}: unrecognized hackrf_info output")

    finish_current()
    return HackRFInventory(tool_version, library_version, tuple(devices))


def collect_hackrf_inventory(
    executable: str = "hackrf_info", *, timeout_seconds: float = 15.0
) -> HackRFInventory:
    """Collect read-only connected-device inventory through `hackrf_info`."""

    resolved = shutil.which(executable) if "/" not in executable else executable
    if not resolved:
        raise FileNotFoundError(executable)
    try:
        completed = subprocess.run(
            hackrf_info_argv(resolved),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise HackRFInfoError("hackrf_info timed out") from exc
    if completed.returncode != 0 and "No HackRF boards found." not in completed.stdout:
        detail = completed.stderr.strip() or "hackrf_info returned a non-zero status"
        raise HackRFInfoError(detail)
    return parse_hackrf_info(completed.stdout)
