from __future__ import annotations

from io import BytesIO
from typing import Optional

from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import GPS, TAGS


GpsCoordinate = tuple[float, float]


def _ratio_to_float(value: object) -> float:
    try:
        numerator = float(value.numerator)  # type: ignore[attr-defined]
        denominator = float(value.denominator)  # type: ignore[attr-defined]
        if denominator == 0:
            raise ValueError("EXIF rational denominator is zero")
        return numerator / denominator
    except AttributeError:
        return float(value)  # type: ignore[arg-type]


def _dms_to_decimal(values: tuple[object, object, object], reference: str) -> float:
    degrees = _ratio_to_float(values[0])
    minutes = _ratio_to_float(values[1])
    seconds = _ratio_to_float(values[2])
    decimal = degrees + minutes / 60.0 + seconds / 3600.0
    if reference.upper() in {"S", "W"}:
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
            for tag_id, value in exif.items():
                if TAGS.get(tag_id) == "GPSInfo":
                    gps_ifd = exif.get_ifd(tag_id)
                    break
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValueError("input is not a readable image with valid metadata") from exc

    if not gps_ifd:
        return None
    gps_by_name = {GPS.get(tag_id, str(tag_id)): value for tag_id, value in gps_ifd.items()}
    latitude = gps_by_name.get("GPSLatitude")
    latitude_ref = gps_by_name.get("GPSLatitudeRef")
    longitude = gps_by_name.get("GPSLongitude")
    longitude_ref = gps_by_name.get("GPSLongitudeRef")
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
