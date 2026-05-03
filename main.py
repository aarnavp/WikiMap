from __future__ import annotations

import argparse

from graph.builder import load_graph
from graph.pathfinder import (
    find_shortest_path,
    find_shortest_path_undirected,
)
from viz.pyvis_render import render_interactive_graph

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="WikiGraph visualizer and path finder")
    parser.add_argument("--seed", default=None, help="Starting article for the neighborhood view")
    parser.add_argument("--depth", type=int, default=2, help="Neighborhood depth")
    parser.add_argument("--source", default=None, help="Source article for shortest-path search")
    parser.add_argument("--target", default=None, help="Target article for shortest-path search")
    parser.add_argument("--out", default="output/wikigraph.html", help="Output HTML file")
    parser.add_argument("--limit", type=int, default=None, help="Optional node limit when loading the graph")
    parser.add_argument("--open", action="store_true", help="Open the HTML in the browser after rendering")
    return parser



def resolve_node(G, name: str):
    if not name:
        return None

    
    if name in G:
        return name

    name_lower = name.lower()

    
    for n in G.nodes():
        if n.lower() == name_lower:
            print(f"[resolver] Using exact match '{n}' for '{name}'")
            return n

    
    matches = [n for n in G.nodes() if name_lower in n.lower()]
    if matches:
        print(f"[resolver] Using partial match '{matches[0]}' for '{name}'")
        return matches[0]

    print(f"[resolver] Could not find node for '{name}'")
    return None



def main() -> None:
    args = build_parser().parse_args()

    print("[main] Loading graph...")
    G = load_graph(limit=args.limit)

    print(f"[main] Graph loaded: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    
    seed = resolve_node(G, args.seed)
    source = resolve_node(G, args.source) if args.source else None
    target = resolve_node(G, args.target) if args.target else None

    
    path = []

    if source and target:
        if source not in G or target not in G:
            print("[main] Invalid source/target — skipping pathfinding")
        else:
            print(f"[main] Finding path: {source} → {target}")
            path = find_shortest_path(G, source, target)

            if not path:
                print("[main] Trying undirected fallback...")
                path = find_shortest_path_undirected(G, source, target)

    
    out = render_interactive_graph(
        G,
        seed=seed,
        depth=args.depth,
        source=source,
        target=target,
        #path=path,  
        output_path=args.out,
        open_browser=args.open,
    )

    print(f"[main] Wrote interactive viz to {out}")


if __name__ == "__main__":
    main()
