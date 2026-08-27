from __future__ import annotations

from typing import Iterable

import networkx as nx


EvidenceLink = tuple[str, str, str]


def _require_label(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be blank")
    if len(normalized) > 512:
        raise ValueError(f"{field_name} exceeds 512 characters")
    return normalized


def inicializar_grafo_inteligencia_nexus(vinculos_evidencia: Iterable[EvidenceLink]) -> nx.DiGraph:
    """Build a directed evidence graph without inferring identity beyond supplied links."""
    graph = nx.DiGraph()
    for origin, relation, destination in vinculos_evidencia:
        source = _require_label(origin, "origin")
        edge_relation = _require_label(relation, "relation")
        target = _require_label(destination, "destination")
        graph.add_node(source, tipo="Entidad")
        graph.add_node(target, tipo="Entidad")
        graph.add_edge(source, target, relacion=edge_relation)
    return graph


def buscar_eslabon_comun(grafo: nx.DiGraph, entidad_a: str, entidad_b: str) -> list[str]:
    """Return the shortest evidence path between two known graph entities, if one exists."""
    source = _require_label(entidad_a, "entidad_a")
    target = _require_label(entidad_b, "entidad_b")
    if source not in grafo or target not in grafo:
        return []
    try:
        return [str(node) for node in nx.shortest_path(grafo, source=source, target=target)]
    except nx.NetworkXNoPath:
        return []
