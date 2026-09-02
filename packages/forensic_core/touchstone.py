from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

_PORTS_RE = re.compile(r"\.s(\d+)p$", re.IGNORECASE)
_FREQ_SCALE = {"HZ": 1.0, "KHZ": 1e3, "MHZ": 1e6, "GHZ": 1e9}
_FORMATS = {"RI", "MA", "DB"}


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


def _parse_option_line(line: str, ports: int) -> tuple[str, str, str, tuple[float, ...]]:
    tokens = line[1:].split()
    unit = "GHZ"
    parameter = "S"
    data_format = "MA"
    references: tuple[float, ...] = (50.0,) * ports

    if tokens:
        unit = tokens[0].upper()
    if len(tokens) > 1:
        parameter = tokens[1].upper()
    if len(tokens) > 2:
        data_format = tokens[2].upper()
    if unit not in _FREQ_SCALE:
        raise TouchstoneError(f"unsupported frequency unit: {unit}")
    if parameter not in {"S", "Y", "Z", "G", "H"}:
        raise TouchstoneError(f"unsupported network parameter type: {parameter}")
    if data_format not in _FORMATS:
        raise TouchstoneError(f"unsupported data format: {data_format}")

    if len(tokens) > 3:
        if tokens[3].upper() != "R":
            raise TouchstoneError("option line entries after format must begin with R")
        if len(tokens) < 5:
            raise TouchstoneError("option line R requires at least one reference resistance")
        try:
            values = tuple(float(item) for item in tokens[4:])
        except ValueError as exc:
            raise TouchstoneError("invalid reference resistance") from exc
        if len(values) not in {1, ports} or any(value <= 0 for value in values):
            raise TouchstoneError("reference resistance must contain one value or one value per port")
        references = values * ports if len(values) == 1 else values

    return unit, parameter, data_format, references


def _pair_to_complex(first: float, second: float, data_format: str) -> complex:
    if data_format == "RI":
        return complex(first, second)
    magnitude = first if data_format == "MA" else 10 ** (first / 20.0)
    angle = math.radians(second)
    return complex(magnitude * math.cos(angle), magnitude * math.sin(angle))


def parse_touchstone(text: str, *, filename: str) -> TouchstoneNetwork:
    """Parse Full-matrix Touchstone 1.x/2.x network data from VNA exports.

    The implementation covers the standard Full matrix form used for S-parameter
    interchange. Lower/Upper matrices, noise blocks, mixed-mode blocks, and
    information blocks are rejected explicitly instead of being guessed.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    match = _PORTS_RE.search(filename)
    extension_ports = int(match.group(1)) if match else None

    version = "1.0"
    ports = extension_ports
    number_of_frequencies: int | None = None
    two_port_order: str | None = None
    matrix_format = "FULL"
    option_line: str | None = None
    reference_override: tuple[float, ...] | None = None
    data_tokens: list[str] = []
    in_network_data = False
    in_reference = False
    saw_v2_keyword = False

    for raw_line in text.splitlines():
        line = _strip_comment(raw_line)
        if not line:
            continue
        if line.startswith("#"):
            option_line = line
            in_reference = False
            continue
        if line.startswith("["):
            in_reference = False
            keyword, _, argument = line.partition("]")
            key = keyword[1:].strip().lower()
            value = argument.strip()
            saw_v2_keyword = True
            if key == "version":
                if not value:
                    raise TouchstoneError("[Version] requires an argument")
                version = value
            elif key == "number of ports":
                try:
                    parsed_ports = int(value)
                except ValueError as exc:
                    raise TouchstoneError("invalid [Number of Ports]") from exc
                if parsed_ports <= 0:
                    raise TouchstoneError("[Number of Ports] must be positive")
                if extension_ports is not None and parsed_ports != extension_ports:
                    raise TouchstoneError("file extension and [Number of Ports] disagree")
                ports = parsed_ports
            elif key == "number of frequencies":
                try:
                    number_of_frequencies = int(value)
                except ValueError as exc:
                    raise TouchstoneError("invalid [Number of Frequencies]") from exc
                if number_of_frequencies <= 0:
                    raise TouchstoneError("[Number of Frequencies] must be positive")
            elif key == "two-port data order":
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
                in_network_data = True
            elif key == "end":
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
            continue

        if in_reference:
            try:
                values = tuple(float(item) for item in line.split())
            except ValueError as exc:
                raise TouchstoneError("invalid [Reference] data") from exc
            reference_override = (reference_override or ()) + values
            continue
        if saw_v2_keyword and not in_network_data:
            raise TouchstoneError("Touchstone 2.x network values must follow [Network Data]")
        data_tokens.extend(line.split())

    if ports is None:
        raise TouchstoneError("cannot determine port count from filename or [Number of Ports]")
    if ports > 64:
        raise TouchstoneError("port count exceeds supported forensic bound of 64")
    if option_line is None:
        option_line = "# GHZ S MA R 50"
    unit, parameter, data_format, references = _parse_option_line(option_line, ports)
    if reference_override is not None:
        if len(reference_override) != ports or any(value <= 0 for value in reference_override):
            raise TouchstoneError("[Reference] must provide one positive resistance per port")
        references = reference_override

    if version.startswith("2") and ports == 2 and two_port_order is None:
        raise TouchstoneError("Touchstone 2.x two-port data requires [Two-Port Data Order]")
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
        if not math.isfinite(frequency) or frequency < 0:
            raise TouchstoneError("frequency must be finite and non-negative")
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
