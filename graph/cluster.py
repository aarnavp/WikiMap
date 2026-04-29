# graph/cluster.py
import networkx as nx
import community as community_louvain
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph.builder import load_graph, get_subgraph

def detect_clusters(G: nx.DiGraph) -> dict[str, int]:
    """
    Run Louvain community detection on the graph.
    Returns {title: cluster_id} for every node.
    """
    # Louvain requires undirected graph
    G_undirected = G.to_undirected()

    partition = community_louvain.best_partition(G_undirected)

    num_clusters = len(set(partition.values()))
    print(f"[cluster] Found {num_clusters} clusters across {len(partition)} nodes")

    return partition


def attach_clusters(G: nx.DiGraph, partition: dict[str, int]) -> nx.DiGraph:
    """
    Attach cluster IDs as node attributes on the graph.
    Returns the same graph with cluster data added.
    """
    for node, cluster_id in partition.items():
        if node in G:
            G.nodes[node]["cluster"] = cluster_id
    return G


def get_cluster_summary(partition: dict[str, int]) -> dict[int, list[str]]:
    """
    Invert partition into {cluster_id: [titles]}.
    Useful for debugging — see which articles ended up together.
    """
    clusters = {}
    for title, cluster_id in partition.items():
        clusters.setdefault(cluster_id, []).append(title)
    return clusters


# --- quick test ---
if __name__ == "__main__":
    G = load_graph()

    partition = detect_clusters(G)
    G = attach_clusters(G, partition)

    summary = get_cluster_summary(partition)
    print(f"\nCluster breakdown:")
    for cluster_id, titles in sorted(summary.items()):
        print(f"  Cluster {cluster_id} ({len(titles)} articles):")
        for t in titles[:5]:
            print(f"    - {t}")
        if len(titles) > 5:
            print(f"    ... and {len(titles) - 5} more")
