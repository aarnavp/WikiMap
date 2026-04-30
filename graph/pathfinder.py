# graph/pathfinder.py
import networkx as nx
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph.builder import load_graph


def find_shortest_path(G: nx.DiGraph, source: str, target: str) -> list[str]:
    """
    Find the shortest directed path between source and target articles.
    Returns a list of article titles from source to target, or [] if none found.
    """
    if source not in G:
        print(f"[pathfinder] '{source}' not in graph")
        return []
    if target not in G:
        print(f"[pathfinder] '{target}' not in graph")
        return []

    try:
        path = nx.shortest_path(G, source=source, target=target)
        print(f"[pathfinder] Path ({len(path)} hops): {' → '.join(path)}")
        return path
    except nx.NetworkXNoPath:
        print(f"[pathfinder] No directed path from '{source}' to '{target}'")
        return []
    except nx.NodeNotFound as e:
        print(f"[pathfinder] Node not found: {e}")
        return []


def find_shortest_path_undirected(G: nx.DiGraph, source: str, target: str) -> list[str]:
    """
    Fallback: find shortest path ignoring edge direction.
    Useful when directed path doesn't exist but articles are connected.
    """
    G_und = G.to_undirected()
    try:
        path = nx.shortest_path(G_und, source=source, target=target)
        print(f"[pathfinder] Undirected path ({len(path)} hops): {' → '.join(path)}")
        return path
    except nx.NetworkXNoPath:
        print(f"[pathfinder] No undirected path from '{source}' to '{target}'")
        return []


def path_to_subgraph(G: nx.DiGraph, path: list[str]) -> nx.DiGraph:
    """
    Return a subgraph containing only the nodes and edges along a path.
    Used by viz to render just the path.
    """
    if not path:
        return nx.DiGraph()
    sub = G.subgraph(path).copy()
    return sub


# --- quick test ---
if __name__ == "__main__":
    print("[pathfinder] Loading graph...")
    G = load_graph()

    if G.number_of_nodes() == 0:
        print("[pathfinder] Graph is empty — run the crawler first.")
    else:
        nodes = list(G.nodes())
        source = nodes[0]
        target = nodes[min(10, len(nodes) - 1)]  # pick a node a few steps away

        print(f"\n[pathfinder] Testing directed path: '{source}' → '{target}'")
        path = find_shortest_path(G, source, target)

        if not path:
            print("[pathfinder] Trying undirected fallback...")
            path = find_shortest_path_undirected(G, source, target)

        if path:
            sub = path_to_subgraph(G, path)
            print(f"[pathfinder] Path subgraph: {sub.number_of_nodes()} nodes, "
                  f"{sub.number_of_edges()} edges")
        else:
            print("[pathfinder] No path found between test nodes.")
