from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class PostGISAdapter:
    connection: Any

    def distance_m(self, *, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        for lat in (lat1, lat2):
            if not -90 <= lat <= 90:
                raise ValueError("latitude out of range")
        for lon in (lon1, lon2):
            if not -180 <= lon <= 180:
                raise ValueError("longitude out of range")
        sql = """
            SELECT ST_Distance(
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
            ) AS distance_m
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (lon1, lat1, lon2, lat2))
            row = cursor.fetchone()
        if row is None:
            raise RuntimeError("PostGIS returned no distance row")
        return float(row[0])

    def points_within_radius(self, *, table: str, geom_column: str, latitude: float, longitude: float, radius_m: float, limit: int = 1000) -> list[tuple[Any, ...]]:
        if not table.replace("_", "").isalnum() or not geom_column.replace("_", "").isalnum():
            raise ValueError("table and geom_column must be identifier-safe")
        if radius_m < 0 or not 1 <= limit <= 10_000:
            raise ValueError("invalid radius or limit")
        sql = f"""
            SELECT *
            FROM {table}
            WHERE ST_DWithin(
                {geom_column}::geography,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                %s
            )
            LIMIT %s
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (longitude, latitude, radius_m, limit))
            return list(cursor.fetchall())


class H3Adapter:
    @staticmethod
    def cell(latitude: float, longitude: float, resolution: int) -> str:
        if not 0 <= resolution <= 15:
            raise ValueError("H3 resolution must be between 0 and 15")
        try:
            import h3
        except ImportError as exc:
            raise RuntimeError("h3 is required for H3Adapter") from exc
        if hasattr(h3, "latlng_to_cell"):
            return str(h3.latlng_to_cell(latitude, longitude, resolution))
        return str(h3.geo_to_h3(latitude, longitude, resolution))
