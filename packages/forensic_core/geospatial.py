from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_M = 6_371_008.8


@dataclass(frozen=True, slots=True)
class GeoPoint:
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not -90.0 <= self.latitude <= 90.0:
            raise ValueError("latitude must be between -90 and 90")
        if not -180.0 <= self.longitude <= 180.0:
            raise ValueError("longitude must be between -180 and 180")


def haversine_distance_m(left: GeoPoint, right: GeoPoint) -> float:
    lat1, lon1, lat2, lon2 = map(radians, (left.latitude, left.longitude, right.latitude, right.longitude))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_M * asin(sqrt(a))


def within_radius(point: GeoPoint, center: GeoPoint, radius_m: float) -> bool:
    if radius_m < 0:
        raise ValueError("radius_m must be non-negative")
    return haversine_distance_m(point, center) <= radius_m
