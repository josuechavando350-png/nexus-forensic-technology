from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

_PORTS_RE = re.compile(r"\.s(\d+)p$", re.IGNORECASE)
_FREQ_SCALE = {"HZ": 1.0, "KHZ": 1e3, "MHZ": 1e6, "GHZ": 1e9}
_PARAMETER_TYPES = {"S", "Y", "Z", "G", "H"}
_FORMATS = {"RI", "MA", "DB"}
_V2_VERSIONS = {"2.0", "2.1"}
_OPTION_KEYWORDS = set(_FREQ_SCALE) | _PARAMETER_TYPES | _FORMATS | {"R"}


class TouchstoneError(ValueError):
    """Raised when Touchstone measurement evidence is invalid or unsupported."""


@dataclass(frozen=True, slots=True)
class TouchstonePoint:
    frequency_hz: float
    parameters: tuple[complex, ...]


@dataclass(frozen=True, slots=True)
class TouchstoneNetwork:
    version: str
    ports: int
    parameter_type: str
    data_format: str
    reference_ohms: tuple[float, ...]
    two_port_data_order: str | None
    points: tuple[TouchstonePoint, ...]

    def parameter_labels(self) -> tuple[str, ...]:
        if self.ports == 1:
            return (f"{self.parameter_type}11",)
        if self.ports == 2 and self.two_port_data_order == "21_12":
            indices = ((1, 1), (2, 1), (1, 2), (2, 2))
        else:
            indices = tuple(
                (row, column)
                for row in range(1, self.ports + 1)
                for column in range(1, self.ports + 1)
            )
        return tuple(f"{self.parameter_type}{row}{column}" for row, column in indices)


def _strip_comment(line: str) -> str:
    return line.split("!", 1)[0].strip()


def _parse_option_line(
    line: str, ports: int
) -> tuple[str, str, str, tuple[float, ...], bool]:
    """Parse the order-independent Touchstone option line.

    With the exception of a multi-valued per-port reference list, option-line
    tokens may appear in any order. The boolean return value records whether
    the line used the legacy Version 1.1 per-port-reference form.
    """

    tokens = line[1:].split()
    unit = "GHZ"
    parameter = "S"
    data_format = "MA"
    references: tuple[float, ...] = (50.0,) * ports
    reference_count = 0
    saw_reference = False

    index = 0
    while index < len(tokens):
        token = tokens[index]
        upper = token.upper()
        if upper in _FREQ_SCALE:
            unit = upper
            index += 1
            continue
        if upper in _PARAMETER_TYPES:
            parameter = upper
            index += 1
            continue
        if upper in _FORMATS:
            data_format = upper
            index += 1
            continue
        if upper == "R":
            if saw_reference:
                raise TouchstoneError("option line contains more than one R clause")
            saw_reference = True
            index += 1
            raw_values: list[str] = []
            while index < len(tokens) and tokens[index].upper() not in _OPTION_KEYWORDS:
                raw_values.append(tokens[index])
                index += 1
            if not raw_values:
                raise TouchstoneError("option line R requires a reference resistance")
            try:
                values = tuple(float(item) for item in raw_values)
            except ValueError as exc:
                raise TouchstoneError("invalid reference resistance") from exc
            if len(values) not in {1, ports} or any(
                not math.isfinite(value) or value <= 0 for value in values
            ):
                raise TouchstoneError(
                    "reference resistance must contain one value or one value per port"
                )
            reference_count = len(values)
            references = values * ports if len(values) == 1 else values
            continue
        raise TouchstoneError(f"unrecognized option-line token: {token}")

    if parameter in {"G", "H"} and ports != 2:
        raise TouchstoneError(f"{parameter}-parameters are defined only for two-port networks")
    return unit, parameter, data_format, references, reference_count == ports and ports > 1


def _pair_to_complex(first: float, second: float, data_format: str) -> complex:
    if data_format == "RI":
        return complex(first, second)
    magnitude = first if data_format == "MA" else 10 ** (first / 20.0)
    angle = math.radians(second)
    return complex(magnitude * math.cos(angle), magnitude * math.sin(angle))


def parse_touchstone(text: str, *, filename: str) -> TouchstoneNetwork:
    """Parse bounded Full-matrix Touchstone network data from VNA exports."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    match = _PORTS_RE.search(filename)
    extension_ports = int(match.group(1)) if match else None

    version: str | None = None
    ports = extension_ports
    number_of_frequencies: int | None = None
    two_port_order: str | None = None
    matrix_format = "FULL"
    option_line: str | None = None
    reference_override: tuple[float, ...] | None = None
    data_tokens: list[str] = []
    in_network_data = False
    in_reference = False
    saw_non_comment = False
    saw_keyword = False
    saw_version = False
    saw_number_ports = False
    saw_number_frequencies = False
    saw_network_data = False
    saw_end = False

    for raw_line in text.splitlines():
        line = _strip_comment(raw_line)
        if not line:
            continue
        if saw_end:
            raise TouchstoneError("non-comment text appears after [End]")

        if line.startswith("#"):
            if option_line is None:
                option_line = line
            in_reference = False
            saw_non_comment = True
            continue

        if line.startswith("["):
            keyword, separator, argument = line.partition("]")
            if not separator:
                raise TouchstoneError("unterminated Touchstone keyword")
            key = keyword[1:].strip().lower()
            value = argument.strip()
            saw_keyword = True
            in_reference = False

            if key == "version":
                if saw_version:
                    raise TouchstoneError("duplicate [Version] keyword")
                if saw_non_comment:
                    raise TouchstoneError("[Version] must precede all other non-comment lines")
                if value not in _V2_VERSIONS:
                    raise TouchstoneError(
                        f"unsupported Touchstone version keyword: {value or '<missing>'}"
                    )
                version = value
                saw_version = True
            elif key == "number of ports":
                if saw_number_ports:
                    raise TouchstoneError("duplicate [Number of Ports] keyword")
                try:
                    parsed_ports = int(value)
                except ValueError as exc:
                    raise TouchstoneError("invalid [Number of Ports]") from exc
                if parsed_ports <= 0:
                    raise TouchstoneError("[Number of Ports] must be positive")
                if extension_ports is not None and parsed_ports != extension_ports:
                    raise TouchstoneError("file extension and [Number of Ports] disagree")
                ports = parsed_ports
                saw_number_ports = True
            elif key == "number of frequencies":
                if saw_number_frequencies:
                    raise TouchstoneError("duplicate [Number of Frequencies] keyword")
                try:
                    number_of_frequencies = int(value)
                except ValueError as exc:
                    raise TouchstoneError("invalid [Number of Frequencies]") from exc
                if number_of_frequencies <= 0:
                    raise TouchstoneError("[Number of Frequencies] must be positive")
                saw_number_frequencies = True
            elif key == "two-port data order":
                if two_port_order is not None:
                    raise TouchstoneError("duplicate [Two-Port Data Order] keyword")
                two_port_order = value.upper()
                if two_port_order not in {"12_21", "21_12"}:
                    raise TouchstoneError("invalid [Two-Port Data Order]")
            elif key == "matrix format":
                matrix_format = value.upper()
                if matrix_format not in {"FULL", "LOWER", "UPPER"}:
                    raise TouchstoneError("invalid [Matrix Format]")
                if matrix_format != "FULL":
                    raise TouchstoneError("Lower/Upper Touchstone matrices are not supported")
            elif key == "reference":
                in_reference = True
                if value:
                    try:
                        reference_override = tuple(float(item) for item in value.split())
                    except ValueError as exc:
                        raise TouchstoneError("invalid [Reference]") from exc
            elif key == "network data":
                if saw_network_data:
                    raise TouchstoneError("duplicate [Network Data] keyword")
                saw_network_data = True
                in_network_data = True
            elif key == "end":
                saw_end = True
                in_network_data = False
            elif key in {
                "noise data",
                "number of noise frequencies",
                "mixed-mode order",
                "begin information",
                "end information",
            }:
                raise TouchstoneError(f"unsupported Touchstone section [{key}]")
            else:
                raise TouchstoneError(f"unsupported Touchstone keyword [{key}]")
            saw_non_comment = True
            continue

        if in_reference:
            try:
                values = tuple(float(item) for item in line.split())
            except ValueError as exc:
                raise TouchstoneError("invalid [Reference] data") from exc
            reference_override = (reference_override or ()) + values
            saw_non_comment = True
            continue
        if saw_keyword and not in_network_data:
            raise TouchstoneError("Touchstone 2.x network values must follow [Network Data]")
        data_tokens.extend(line.split())
        saw_non_comment = True

    if saw_keyword and not saw_version:
        raise TouchstoneError("Touchstone keyword files require [Version] 2.0 or 2.1")
    if ports is None:
        raise TouchstoneError("cannot determine port count from filename or [Number of Ports]")
    if ports > 64:
        raise TouchstoneError("port count exceeds supported forensic bound of 64")
    if option_line is None:
        raise TouchstoneError("Touchstone data requires an option line")

    unit, parameter, data_format, references, legacy_per_port = _parse_option_line(
        option_line, ports
    )
    if version is None:
        version = "1.1" if legacy_per_port else "1.0"

    if reference_override is not None:
        if len(reference_override) != ports or any(
            not math.isfinite(value) or value <= 0 for value in reference_override
        ):
            raise TouchstoneError("[Reference] must provide one positive resistance per port")
        references = reference_override

    if version.startswith("2"):
        if not saw_number_ports:
            raise TouchstoneError("Touchstone 2.x requires [Number of Ports]")
        if not saw_number_frequencies:
            raise TouchstoneError("Touchstone 2.x requires [Number of Frequencies]")
        if not saw_network_data:
            raise TouchstoneError("Touchstone 2.x requires [Network Data]")
        if not saw_end:
            raise TouchstoneError("Touchstone 2.x requires [End]")
        if ports == 2 and two_port_order is None:
            raise TouchstoneError("Touchstone 2.x two-port data requires [Two-Port Data Order]")
        if ports != 2 and two_port_order is not None:
            raise TouchstoneError("[Two-Port Data Order] is permitted only for two-port data")
    elif two_port_order is not None:
        raise TouchstoneError("[Two-Port Data Order] is not permitted in Touchstone 1.x")

    if ports == 2 and two_port_order is None:
        two_port_order = "21_12"
    if matrix_format != "FULL":
        raise TouchstoneError("only Full matrices are supported")

    values_per_point = 1 + 2 * ports * ports
    if not data_tokens or len(data_tokens) % values_per_point:
        raise TouchstoneError("network data does not contain complete frequency blocks")

    points: list[TouchstonePoint] = []
    scale = _FREQ_SCALE[unit]
    for offset in range(0, len(data_tokens), values_per_point):
        block = data_tokens[offset : offset + values_per_point]
        try:
            frequency = float(block[0]) * scale
            raw_values = [float(item) for item in block[1:]]
        except ValueError as exc:
            raise TouchstoneError("network data contains a non-numeric value") from exc
        if not math.isfinite(frequency) or frequency < 0 or any(
            not math.isfinite(value) for value in raw_values
        ):
            raise TouchstoneError("network data must contain finite numeric values")
        if points and frequency <= points[-1].frequency_hz:
            raise TouchstoneError("frequency points must be strictly increasing")
        parameters = tuple(
            _pair_to_complex(raw_values[index], raw_values[index + 1], data_format)
            for index in range(0, len(raw_values), 2)
        )
        points.append(TouchstonePoint(frequency, parameters))

    if number_of_frequencies is not None and number_of_frequencies != len(points):
        raise TouchstoneError("[Number of Frequencies] does not match network data")

    return TouchstoneNetwork(
        version=version,
        ports=ports,
        parameter_type=parameter,
        data_format=data_format,
        reference_ohms=references,
        two_port_data_order=two_port_order,
        points=tuple(points),
    )


def load_touchstone(path: str | Path) -> TouchstoneNetwork:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(source)
    if source.stat().st_size > 64 * 1024 * 1024:
        raise TouchstoneError("Touchstone evidence exceeds 64 MiB")
    return parse_touchstone(source.read_text(encoding="utf-8-sig"), filename=source.name)
