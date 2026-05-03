from __future__ import annotations

from collections import deque
from typing import Dict, Iterable, List, Set, Tuple

import networkx as nx


def build_adjacency(G: nx.DiGraph, undirected: bool = False) -> Dict[str, Set[str]]:
    """Build adjacency lists keyed by node title."""
    adjacency: Dict[str, Set[str]] = {node: set() for node in G.nodes()}
    for source, target in G.edges():
        adjacency.setdefault(source, set()).add(target)
        if undirected:
            adjacency.setdefault(target, set()).add(source)
    if undirected:
        for source, target in G.edges():
            adjacency.setdefault(target, set()).add(source)
    return adjacency


def bfs_layers(G: nx.DiGraph, seed: str, depth: int) -> Dict[str, int]:
    """Return {node_title: distance} for nodes within `depth` of `seed`."""
    if seed not in G:
        return {}

    dist = {seed: 0}
    q: deque[str] = deque([seed])

    while q:
        node = q.popleft()
        if dist[node] >= depth:
            continue
        neighbors = set(G.successors(node)) | set(G.predecessors(node))
        for nb in neighbors:
            if nb not in dist:
                dist[nb] = dist[node] + 1
                q.append(nb)
    return dist


def shortest_path_titles(
    G: nx.DiGraph,
    source: str,
    target: str,
    fallback_to_undirected: bool = True,
) -> List[str]:
    """Shortest directed path, optionally falling back to an undirected path."""
    if source not in G or target not in G:
        return []
    try:
        return nx.shortest_path(G, source=source, target=target)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        if not fallback_to_undirected:
            return []
    try:
        return nx.shortest_path(G.to_undirected(), source=source, target=target)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []


def undirected_shortest_path_titles(G: nx.DiGraph, source: str, target: str) -> List[str]:
    """Shortest path ignoring direction."""
    if source not in G or target not in G:
        return []
    try:
        return nx.shortest_path(G.to_undirected(), source=source, target=target)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []


def path_edges(path: Iterable[str]) -> Set[Tuple[str, str]]:
    """Return consecutive edges in a node path."""
    path = list(path)
    return {(path[i], path[i + 1]) for i in range(len(path) - 1)}
