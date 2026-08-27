from __future__ import annotations

from io import BytesIO
from typing import Optional, Protocol, cast

from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import TAGS


GpsCoordinate = tuple[float, float]
GPS_LATITUDE_REF = 1
GPS_LATITUDE = 2
GPS_LONGITUDE_REF = 3
GPS_LONGITUDE = 4


class RationalLike(Protocol):
    numerator: object
    denominator: object


def _ratio_to_float(value: object) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    rational = cast(RationalLike, value)
    try:
        numerator = float(rational.numerator)
        denominator = float(rational.denominator)
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("EXIF coordinate component is not numeric") from exc
    if denominator == 0:
        raise ValueError("EXIF rational denominator is zero")
    return numerator / denominator


def _dms_to_decimal(values: tuple[object, object, object], reference: str) -> float:
    degrees = _ratio_to_float(values[0])
    minutes = _ratio_to_float(values[1])
    seconds = _ratio_to_float(values[2])
    decimal = degrees + minutes / 60.0 + seconds / 3600.0
    normalized_reference = reference.upper()
    if normalized_reference not in {"N", "S", "E", "W"}:
        raise ValueError("EXIF GPS reference is invalid")
    if normalized_reference in {"S", "W"}:
        decimal = -decimal
    return decimal


def extraer_gps_exif(archivo_bytes: bytes) -> Optional[GpsCoordinate]:
    """Extract genuine GPS latitude/longitude from EXIF metadata; never fabricate coordinates."""
    if not archivo_bytes:
        raise ValueError("archivo_bytes must not be empty")
    try:
        with Image.open(BytesIO(archivo_bytes)) as image:
            exif = image.getexif()
            gps_ifd: dict[int, object] | None = None
            for tag_id, _value in exif.items():
                if TAGS.get(tag_id) == "GPSInfo":
                    raw_gps_ifd = exif.get_ifd(tag_id)
                    gps_ifd = {int(key): value for key, value in raw_gps_ifd.items()}
                    break
    except (UnidentifiedImageError, OSError, TypeError, ValueError) as exc:
        raise ValueError("input is not a readable image with valid metadata") from exc

    if not gps_ifd:
        return None
    latitude = gps_ifd.get(GPS_LATITUDE)
    latitude_ref = gps_ifd.get(GPS_LATITUDE_REF)
    longitude = gps_ifd.get(GPS_LONGITUDE)
    longitude_ref = gps_ifd.get(GPS_LONGITUDE_REF)
    if not (
        isinstance(latitude, tuple)
        and len(latitude) == 3
        and isinstance(longitude, tuple)
        and len(longitude) == 3
        and isinstance(latitude_ref, str)
        and isinstance(longitude_ref, str)
    ):
        return None
    lat = _dms_to_decimal(latitude, latitude_ref)
    lon = _dms_to_decimal(longitude, longitude_ref)
    if not -90.0 <= lat <= 90.0 or not -180.0 <= lon <= 180.0:
        raise ValueError("EXIF GPS coordinates are out of range")
    return (lat, lon)
