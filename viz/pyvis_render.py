from __future__ import annotations

import html
import json
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional

import networkx as nx

from graph.builder import load_graph


def _node_payload(G: nx.DiGraph) -> List[Dict[str, Any]]:
    nodes: List[Dict[str, Any]] = []
    for title, data in G.nodes(data=True):
        degree = G.degree(title)
        nodes.append(
            {
                "id": title,
                "label": title,
                "title": f"{title}\n{data.get('url', '')}",
                "url": data.get("url", ""),
                "degree": degree,
                "size": max(8, min(30, 8 + degree * 1.5)),
            }
        )
    return nodes


def _edge_payload(G: nx.DiGraph) -> List[Dict[str, Any]]:
    edges: List[Dict[str, Any]] = []
    for source, target in G.edges():
        edges.append({"from": source, "to": target, "arrows": "to"})
    return edges


def _escape(s: str) -> str:
    return html.escape(s, quote=True)


_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>__TITLE__</title>
  <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style>
    :root {
      --bg: #0b1020;
      --panel: rgba(15, 22, 42, 0.92);
      --panel-border: rgba(160, 190, 255, 0.18);
      --text: #e8eefc;
      --muted: #9aa8cc;
    }
    html, body {
      margin: 0;
      width: 100%;
      height: 100%;
      background: radial-gradient(circle at top, #121a36 0%, #090d18 50%, #05070d 100%);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
      overflow: hidden;
    }
    .app {
      display: grid;
      grid-template-columns: 340px 1fr;
      height: 100vh;
      width: 100vw;
    }
    .sidebar {
      background: var(--panel);
      border-right: 1px solid var(--panel-border);
      padding: 18px 16px;
      box-sizing: border-box;
      overflow-y: auto;
      backdrop-filter: blur(10px);
    }
    .brand { font-size: 1.25rem; font-weight: 700; margin-bottom: 6px; }
    .subtitle { color: var(--muted); font-size: 0.92rem; line-height: 1.35; margin-bottom: 16px; }
    .section { margin: 14px 0 18px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.08); }
    .section h3 { margin: 0 0 10px; font-size: 0.95rem; color: #f0f4ff; }
    label { display: block; font-size: 0.8rem; color: var(--muted); margin: 10px 0 6px; }
    input, button {
      width: 100%; box-sizing: border-box; border-radius: 12px; border: 1px solid rgba(255,255,255,0.12);
      background: rgba(255,255,255,0.05); color: var(--text); padding: 10px 12px; outline: none; font-size: 0.95rem;
    }
    input:focus { border-color: rgba(122,162,255,0.65); box-shadow: 0 0 0 3px rgba(122,162,255,0.18); }
    button { cursor: pointer; margin-top: 10px; background: linear-gradient(135deg, rgba(122,162,255,0.22), rgba(141,242,192,0.16)); }
    button:hover { background: linear-gradient(135deg, rgba(122,162,255,0.34), rgba(141,242,192,0.22)); }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .stats, .status { font-size: 0.88rem; color: var(--muted); line-height: 1.5; }
    .status strong { color: var(--text); }
    .note { color: var(--muted); font-size: 0.82rem; line-height: 1.45; margin-top: 10px; }
    #network { width: 100%; height: 100%; background: radial-gradient(circle at center, rgba(120,160,255,0.08), transparent 60%); }
    .pill { display: inline-block; margin: 4px 6px 0 0; padding: 4px 8px; border-radius: 999px; background: rgba(255,255,255,0.07); color: var(--muted); font-size: 0.76rem; }
    .small { font-size: 0.8rem; color: var(--muted); }
    .divider { height: 1px; background: rgba(255,255,255,0.08); margin: 12px 0; }
    .error { color: #ffb4c0; }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="brand">WikiGraph</div>
      <div class="subtitle">Constellation-style Wikipedia graph explorer with neighborhood focus and shortest-path search.</div>

      <div class="section">
        <h3>Neighborhood view</h3>
        <label for="seedInput">Start article</label>
        <input id="seedInput" list="nodeList" value="__SEED__" placeholder="Type a Wikipedia title..." />

        <label for="depthInput">Depth</label>
        <input id="depthInput" type="number" min="0" max="10" value="__DEPTH__" />

        <button id="applySeedBtn">Show neighborhood</button>
      </div>

      <div class="section">
        <h3>Shortest path</h3>
        <label for="sourceInput">Source article</label>
        <input id="sourceInput" list="nodeList" value="__SOURCE__" placeholder="Source title..." />

        <label for="targetInput">Target article</label>
        <input id="targetInput" list="nodeList" value="__TARGET__" placeholder="Target title..." />

        <div class="row">
          <button id="pathDirBtn">Directed path</button>
          <button id="pathUndirBtn">Undirected path</button>
        </div>

        <div id="pathStatus" class="status note">Enter two titles and search for a path.</div>
      </div>

      <div class="section">
        <h3>Graph info</h3>
        <div id="graphStats" class="stats"></div>
        <div class="note">
          <span class="pill">drag nodes</span>
          <span class="pill">hover titles</span>
          <span class="pill">click to center</span>
          <span class="pill">search path</span>
        </div>
      </div>

      <div class="section">
        <h3>Selection</h3>
        <div id="selectionInfo" class="stats">Nothing selected.</div>
        <div class="divider"></div>
        <div class="small">Directed edges are used for the main graph, and undirected fallback is available for path search.</div>
      </div>
    </aside>

    <main id="network"></main>
  </div>

  <datalist id="nodeList"></datalist>

  <script>
    const RAW_NODES = __NODES__;
    const RAW_EDGES = __EDGES__;

    const nodes = new vis.DataSet(RAW_NODES.map(n => ({
      id: n.id,
      label: n.label,
      title: n.title,
      url: n.url || "",
      degree: n.degree || 0,
      size: n.size || 12,
      hidden: false,
      color: {
        background: "rgba(219,231,255,0.92)",
        border: "rgba(122,162,255,0.65)",
        highlight: {
          background: "rgba(141,242,192,0.95)",
          border: "rgba(255,255,255,0.95)"
        }
      },
      font: {
        color: "#eef4ff",
        size: 16,
        face: "Inter"
      },
      shape: "dot",
      borderWidth: 1,
      shadow: {
        enabled: true,
        color: "rgba(122,162,255,0.35)",
        size: 10,
        x: 0,
        y: 0
      }
    })));

    const edges = new vis.DataSet(RAW_EDGES.map(e => ({
      from: e.from,
      to: e.to,
      arrows: e.arrows || "to",
      color: {
        color: "rgba(183,204,255,0.18)",
        highlight: "rgba(255,255,255,0.95)"
      },
      width: 1,
      selectionWidth: 2,
      smooth: {
        enabled: true,
        type: "dynamic"
      }
    })));

    const container = document.getElementById("network");
    const data = { nodes, edges };
    const options = {
      interaction: {
        hover: true,
        multiselect: false,
        navigationButtons: true,
        keyboard: true
      },
      physics: {
        enabled: true,
        solver: "barnesHut",
        barnesHut: {
          gravitationalConstant: -18000,
          centralGravity: 0.18,
          springLength: 140,
          springConstant: 0.02,
          damping: 0.16,
          avoidOverlap: 0.6
        },
        stabilization: {
          iterations: 220,
          fit: true
        }
      },
      layout: { improvedLayout: true },
      nodes: { scaling: { min: 6, max: 28 } },
      edges: {
        arrows: { to: { enabled: true, scaleFactor: 0.7 } },
        smooth: { type: "dynamic" }
      }
    };

    const network = new vis.Network(container, data, options);

    const adjacencyOut = new Map();
    const adjacencyUndir = new Map();
    RAW_NODES.forEach(n => {
      adjacencyOut.set(n.id, new Set());
      adjacencyUndir.set(n.id, new Set());
    });
    RAW_EDGES.forEach(e => {
      if (!adjacencyOut.has(e.from)) adjacencyOut.set(e.from, new Set());
      if (!adjacencyOut.has(e.to)) adjacencyOut.set(e.to, new Set());
      if (!adjacencyUndir.has(e.from)) adjacencyUndir.set(e.from, new Set());
      if (!adjacencyUndir.has(e.to)) adjacencyUndir.set(e.to, new Set());
      adjacencyOut.get(e.from).add(e.to);
      adjacencyUndir.get(e.from).add(e.to);
      adjacencyUndir.get(e.to).add(e.from);
    });

    const seedInput = document.getElementById("seedInput");
    const depthInput = document.getElementById("depthInput");
    const sourceInput = document.getElementById("sourceInput");
    const targetInput = document.getElementById("targetInput");
    const applySeedBtn = document.getElementById("applySeedBtn");
    const pathDirBtn = document.getElementById("pathDirBtn");
    const pathUndirBtn = document.getElementById("pathUndirBtn");
    const pathStatus = document.getElementById("pathStatus");
    const selectionInfo = document.getElementById("selectionInfo");
    const graphStats = document.getElementById("graphStats");
    const nodeList = document.getElementById("nodeList");

    function resetVisualState() {
      const allNodes = nodes.get();
      nodes.update(allNodes.map(n => ({
        ...n,
        hidden: false,
        color: {
          background: "rgba(219,231,255,0.92)",
          border: "rgba(122,162,255,0.65)",
          highlight: {
            background: "rgba(141,242,192,0.95)",
            border: "rgba(255,255,255,0.95)"
          }
        },
        shadow: {
          enabled: true,
          color: "rgba(122,162,255,0.35)",
          size: 10,
          x: 0,
          y: 0
        },
        font: {
          color: "#eef4ff",
          size: 16,
          face: "Inter"
        }
      })));

      edges.update(edges.get().map(e => ({
        ...e,
        color: {
          color: "rgba(183,204,255,0.18)",
          highlight: "rgba(255,255,255,0.95)"
        },
        width: 1
      })));
      pathStatus.innerHTML = "Enter two titles and search for a path.";
    }

    function bfsNeighborhood(seed, depth) {
      if (!adjacencyUndir.has(seed)) return new Set();
      const visited = new Set([seed]);
      let frontier = [seed];
      for (let d = 0; d < depth; d++) {
        const next = [];
        for (const node of frontier) {
          for (const nb of (adjacencyUndir.get(node) || [])) {
            if (!visited.has(nb)) {
              visited.add(nb);
              next.push(nb);
            }
          }
        }
        frontier = next;
        if (frontier.length === 0) break;
      }
      return visited;
    }

    function showNeighborhood() {
      const seed = seedInput.value.trim();
      const depth = Math.max(0, parseInt(depthInput.value || "0", 10));
      resetVisualState();

      if (!seed || !adjacencyUndir.has(seed)) {
        pathStatus.innerHTML = `<span class="error">Article not found:</span> ${seed ? seed : "(empty)"}`;
        return;
      }

      const keep = bfsNeighborhood(seed, depth);
      nodes.update(nodes.get().map(n => ({
        id: n.id,
        hidden: !keep.has(n.id),
        color: keep.has(n.id) ? n.color : {
          background: "rgba(219,231,255,0.03)",
          border: "rgba(122,162,255,0.04)"
        },
        font: keep.has(n.id) ? n.font : { color: "rgba(0,0,0,0)" }
      })));

      const seedNode = nodes.get(seed);
      if (seedNode) {
        nodes.update({
          id: seed,
          size: Math.max(20, (seedNode.size || 12) + 8),
          color: {
            background: "rgba(122,162,255,0.96)",
            border: "rgba(255,255,255,0.95)",
            highlight: {
              background: "rgba(141,242,192,0.98)",
              border: "rgba(255,255,255,0.98)"
            }
          }
        });
      }

      graphStats.innerHTML = `Visible nodes: <strong>${keep.size}</strong> / ${RAW_NODES.length}<br>Neighborhood depth: <strong>${depth}</strong><br>Seed: <strong>${seed}</strong>`;
      pathStatus.innerHTML = `Showing neighborhood around <strong>${seed}</strong> at depth <strong>${depth}</strong>.`;
      network.fit({ animation: true });
    }

    function shortestPath(source, target, useUndirected) {
      if (!source || !target) return [];
      const adjacency = useUndirected ? adjacencyUndir : adjacencyOut;
      if (!adjacency.has(source) || !adjacency.has(target)) return [];
      const queue = [source];
      const prev = new Map();
      const seen = new Set([source]);

      while (queue.length) {
        const node = queue.shift();
        if (node === target) break;
        for (const nb of (adjacency.get(node) || [])) {
          if (!seen.has(nb)) {
            seen.add(nb);
            prev.set(nb, node);
            queue.push(nb);
          }
        }
      }

      if (!seen.has(target)) return [];
      const path = [target];
      let cur = target;
      while (cur !== source) {
        cur = prev.get(cur);
        if (cur === undefined) return [];
        path.push(cur);
      }
      path.reverse();
      return path;
    }

    function highlightPath(path) {
      if (!path.length) return;
      resetVisualState();

      const pathSet = new Set(path);
      const pathEdgeSet = new Set();
      for (let i = 0; i < path.length - 1; i++) {
        pathEdgeSet.add(`${path[i]}>>>${path[i + 1]}`);
        pathEdgeSet.add(`${path[i + 1]}>>>${path[i]}`);
      }

      nodes.update(nodes.get().map(n => {
        const isOnPath = pathSet.has(n.id);
        return {
          id: n.id,
          hidden: false,
          size: isOnPath ? Math.max(22, (n.size || 12) + 9) : Math.max(6, (n.size || 12) * 0.75),
          color: isOnPath ? {
            background: n.id === path[0] ? "rgba(122,162,255,0.98)" : (n.id === path[path.length - 1] ? "rgba(255,122,144,0.98)" : "rgba(141,242,192,0.96)"),
            border: "rgba(255,255,255,0.96)"
          } : {
            background: "rgba(219,231,255,0.1)",
            border: "rgba(122,162,255,0.15)"
          },
          font: {
            color: isOnPath ? "#ffffff" : "rgba(232,238,252,0.5)",
            size: isOnPath ? 17 : 14,
            face: "Inter"
          },
          shadow: {
            enabled: isOnPath,
            color: "rgba(255,255,255,0.4)",
            size: 16,
            x: 0,
            y: 0
          }
        };
      }));

      edges.update(edges.get().map(e => {
        const isOnPath = pathEdgeSet.has(`${e.from}>>>${e.to}`);
        return {
          id: e.id,
          width: isOnPath ? 4 : 1,
          color: {
            color: isOnPath ? "rgba(141,242,192,0.9)" : "rgba(183,204,255,0.08)",
            highlight: "rgba(255,255,255,0.95)"
          }
        };
      }));

      network.fit({ nodes: path, animation: true });
      pathStatus.innerHTML = `Shortest path found: <strong>${path.join(" → ")}</strong><br>Hops: <strong>${Math.max(0, path.length - 1)}</strong>`;
    }

    function showPath(useUndirected) {
      const source = sourceInput.value.trim();
      const target = targetInput.value.trim();
      const path = shortestPath(source, target, useUndirected);
      if (!path.length) {
        pathStatus.innerHTML = `<span class="error">No ${useUndirected ? "undirected" : "directed"} path found</span> between <strong>${source || "(empty)"}</strong> and <strong>${target || "(empty)"}</strong>.`;
        return;
      }
      highlightPath(path);
    }

    function populateDatalist() {
      nodeList.innerHTML = RAW_NODES.map(n => `<option value="${n.id}"></option>`).join("");
    }

    function wireClickSelection() {
      network.on("click", params => {
        if (params.nodes.length) {
          const nodeId = params.nodes[0];
          const node = nodes.get(nodeId);
          selectionInfo.innerHTML = `<strong>${node.label}</strong><br><span class="small">${node.url || ""}</span><br>Degree: <strong>${node.degree || 0}</strong>`;
          sourceInput.value = node.label;
          seedInput.value = node.label;
        } else {
          selectionInfo.textContent = "Nothing selected.";
        }
      });
    }

    applySeedBtn.addEventListener("click", showNeighborhood);
    pathDirBtn.addEventListener("click", () => showPath(false));
    pathUndirBtn.addEventListener("click", () => showPath(true));
    seedInput.addEventListener("keydown", e => { if (e.key === "Enter") showNeighborhood(); });
    sourceInput.addEventListener("keydown", e => { if (e.key === "Enter") showPath(false); });
    targetInput.addEventListener("keydown", e => { if (e.key === "Enter") showPath(false); });
    depthInput.addEventListener("keydown", e => { if (e.key === "Enter") showNeighborhood(); });

    populateDatalist();
    wireClickSelection();
    graphStats.innerHTML = `Loaded nodes: <strong>${RAW_NODES.length}</strong><br>Loaded edges: <strong>${RAW_EDGES.length}</strong>`;
    showNeighborhood();
  </script>
</body>
</html>
"""


def render_interactive_graph(
    G: Optional[nx.DiGraph] = None,
    *,
    seed: Optional[str] = None,
    depth: int = 2,
    source: Optional[str] = None,
    target: Optional[str] = None,
    output_path: str = "output/wikigraph.html",
    title: str = "WikiGraph",
    open_browser: bool = False,
) -> str:
    """Render the full graph into an interactive HTML file."""
    if G is None:
        G = load_graph()

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    html_text = _TEMPLATE
    html_text = html_text.replace("__TITLE__", _escape(title))
    html_text = html_text.replace("__SEED__", _escape(seed or (next(iter(G.nodes()), "") if G.number_of_nodes() else "")))
    html_text = html_text.replace("__DEPTH__", str(depth))
    html_text = html_text.replace("__SOURCE__", _escape(source or ""))
    html_text = html_text.replace("__TARGET__", _escape(target or ""))
    html_text = html_text.replace("__NODES__", json.dumps(_node_payload(G), ensure_ascii=False))
    html_text = html_text.replace("__EDGES__", json.dumps(_edge_payload(G), ensure_ascii=False))

    output.write_text(html_text, encoding="utf-8")
    if open_browser:
        webbrowser.open(output.resolve().as_uri())
    return str(output.resolve())


def render_graph_view(
    *,
    seed: Optional[str] = None,
    depth: int = 2,
    source: Optional[str] = None,
    target: Optional[str] = None,
    limit: Optional[int] = None,
    output_path: str = "output/wikigraph.html",
    open_browser: bool = False,
) -> str:
    """Load the graph from SQLite and render it."""
    G = load_graph(limit=limit)
    return render_interactive_graph(
        G,
        seed=seed,
        depth=depth,
        source=source,
        target=target,
        output_path=output_path,
        open_browser=open_browser,
    )


if __name__ == "__main__":
    render_graph_view(open_browser=True)
