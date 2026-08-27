from __future__ import annotations

from io import BytesIO
import unittest

import networkx as nx
import piexif
from PIL import Image

from packages.defensive_intel.entity_graph import buscar_eslabon_comun, inicializar_grafo_inteligencia_nexus
from packages.defensive_intel.metadata_forensics import extraer_gps_exif
from packages.defensive_intel.telemetry import ConnectionObservation, auditar_telemetria_kernel
from packages.defensive_intel.threat_intel import verificar_reputacion_amenaza


class TelemetryTests(unittest.TestCase):
    def test_detects_supplied_indicator_and_port(self) -> None:
        assessment = auditar_telemetria_kernel(
            b"header ROP_CHAIN_DETECTED trailer",
            [ConnectionObservation("203.0.113.10", 4444)],
        )
        self.assertEqual(assessment.status_dispositivo, "SUSPICIOUS")
        self.assertEqual(assessment.bytes_analizados, 33)
        self.assertIn("ROP_CHAIN_DETECTED", assessment.indicadores_inyeccion)
        self.assertEqual(len(assessment.conexiones_sospechosas), 1)

    def test_clean_evidence_has_no_known_indicators(self) -> None:
        assessment = auditar_telemetria_kernel(
            b"ordinary-memory-content",
            [ConnectionObservation("198.51.100.2", 443)],
        )
        self.assertEqual(assessment.status_dispositivo, "NO_KNOWN_INDICATORS")


class GraphTests(unittest.TestCase):
    def test_shortest_evidence_path(self) -> None:
        graph = inicializar_grafo_inteligencia_nexus(
            [("entity-a", "uses", "account-1"), ("account-1", "linked-to", "entity-b")]
        )
        self.assertIsInstance(graph, nx.DiGraph)
        self.assertEqual(buscar_eslabon_comun(graph, "entity-a", "entity-b"), ["entity-a", "account-1", "entity-b"])

    def test_unknown_entity_returns_empty_path(self) -> None:
        graph = inicializar_grafo_inteligencia_nexus([])
        self.assertEqual(buscar_eslabon_comun(graph, "a", "b"), [])


class ExifTests(unittest.TestCase):
    def _jpeg_with_gps(self) -> bytes:
        image = Image.new("RGB", (2, 2))
        gps_ifd = {
            piexif.GPSIFD.GPSLatitudeRef: "N",
            piexif.GPSIFD.GPSLatitude: ((19, 1), (25, 1), (572, 100)),
            piexif.GPSIFD.GPSLongitudeRef: "W",
            piexif.GPSIFD.GPSLongitude: ((99, 1), (7, 1), (5952, 100)),
        }
        exif_bytes = piexif.dump({"GPS": gps_ifd})
        output = BytesIO()
        image.save(output, format="JPEG", exif=exif_bytes)
        return output.getvalue()

    def test_extracts_real_exif_gps(self) -> None:
        coordinates = extraer_gps_exif(self._jpeg_with_gps())
        self.assertIsNotNone(coordinates)
        assert coordinates is not None
        self.assertAlmostEqual(coordinates[0], 19.4182555, places=5)
        self.assertAlmostEqual(coordinates[1], -99.1332, places=4)

    def test_rejects_non_image_bytes(self) -> None:
        with self.assertRaises(ValueError):
            extraer_gps_exif(b"not-an-image")


class ThreatIntelValidationTests(unittest.TestCase):
    def test_rejects_blank_indicator_before_network_access(self) -> None:
        with self.assertRaises(ValueError):
            verificar_reputacion_amenaza("   ", "IPv4")

    def test_rejects_nonpositive_timeout_before_network_access(self) -> None:
        with self.assertRaises(ValueError):
            verificar_reputacion_amenaza("203.0.113.10", "IPv4", timeout=0)


if __name__ == "__main__":
    unittest.main()
