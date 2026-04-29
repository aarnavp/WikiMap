# graph/builder.py
import networkx as nx
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph.store import get_connection

def load_graph(limit: int = None) -> nx.DiGraph:
    """
    Load the graph from SQLite into a networkx DiGraph.
    Optionally limit to a subgraph of `limit` nodes.
    """
    conn = get_connection()
    G = nx.DiGraph()

    # load nodes
    if limit:
        rows = conn.execute(
            "SELECT id, title, url FROM nodes WHERE crawled = 1 LIMIT ?", (limit,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, title, url FROM nodes WHERE crawled = 1"
        ).fetchall()

    node_ids = set()
    for id, title, url in rows:
        G.add_node(title, id=id, url=url)
        node_ids.add(id)

    print(f"[builder] Loaded {G.number_of_nodes()} nodes")

    # load edges between those nodes only
    edges = conn.execute(
        "SELECT n1.title, n2.title FROM edges e "
        "JOIN nodes n1 ON e.source_id = n1.id "
        "JOIN nodes n2 ON e.target_id = n2.id"
    ).fetchall()

    for source, target in edges:
        if source in G and target in G:
            G.add_edge(source, target)

    print(f"[builder] Loaded {G.number_of_edges()} edges")
    conn.close()
    return G


def get_subgraph(G: nx.DiGraph, seed: str, depth: int) -> nx.DiGraph:
    """
    Extract a subgraph of all nodes reachable from seed within given depth.
    This is what the viz layer calls — not the whole graph.
    """
    if seed not in G:
        print(f"[builder] '{seed}' not found in graph")
        return nx.DiGraph()

    # BFS to collect nodes within depth
    visited = {seed}
    frontier = {seed}

    for _ in range(depth):
        next_frontier = set()
        for node in frontier:
            neighbours = set(G.successors(node)) | set(G.predecessors(node))
            next_frontier |= neighbours - visited
        visited |= next_frontier
        frontier = next_frontier

    sub = G.subgraph(visited).copy()
    print(f"[builder] Subgraph around '{seed}' at depth {depth}: "
          f"{sub.number_of_nodes()} nodes, {sub.number_of_edges()} edges")
    return sub


# --- quick test ---
if __name__ == "__main__":
    G = load_graph()
    print(f"\nFull graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # test subgraph extraction
    seed = list(G.nodes())[0]
    sub = get_subgraph(G, seed, depth=2)
    print(f"Subgraph from '{seed}': {sub.number_of_nodes()} nodes")
