from __future__ import annotations

from collections import deque


def _validate_adjacency(adjacency: dict[str, set[str]]) -> None:
    if any(not isinstance(node, str) or not node for node in adjacency):
        raise ValueError("graph node identifiers must be non-empty strings")


def connected_components(adjacency: dict[str, set[str]]) -> tuple[tuple[str, ...], ...]:
    _validate_adjacency(adjacency)
    unseen = set(adjacency)
    components: list[tuple[str, ...]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        component = {start}
        while queue:
            current = queue.popleft()
            for neighbor in sorted(adjacency.get(current, set())):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(tuple(sorted(component)))
    return tuple(sorted(components))


def degree_centrality(adjacency: dict[str, set[str]]) -> dict[str, float]:
    _validate_adjacency(adjacency)
    n = len(adjacency)
    if n <= 1:
        return {node: 0.0 for node in adjacency}
    return {node: len(neighbors) / (n - 1) for node, neighbors in sorted(adjacency.items())}


def jaccard_neighbors(adjacency: dict[str, set[str]], left: str, right: str) -> float:
    _validate_adjacency(adjacency)
    a = adjacency.get(left, set())
    b = adjacency.get(right, set())
    union = a | b
    return 0.0 if not union else len(a & b) / len(union)


def shortest_hops(adjacency: dict[str, set[str]], source: str, target: str) -> int | None:
    _validate_adjacency(adjacency)
    if source == target:
        return 0
    seen = {source}
    queue = deque([(source, 0)])
    while queue:
        node, distance = queue.popleft()
        for neighbor in adjacency.get(node, set()):
            if neighbor == target:
                return distance + 1
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append((neighbor, distance + 1))
    return None
