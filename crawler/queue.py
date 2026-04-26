# crawler/queue.py
from collections import deque
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.fetcher import fetch_links
from config import MAX_DEPTH, MAX_NODES

def crawl(seed: str) -> dict[str, list[str]]:
    """
    BFS crawl starting from seed article.
    Returns {title: [linked_titles]} for all visited articles.
    """
    queue = deque()
    queue.append((seed, 0))        # (article_title, current_depth)
    visited = set()
    visited.add(seed.lower())      # lowercase to avoid duplicate visits
    results = {}                   # title -> [links]

    print(f"\n Starting crawl from '{seed}' (max depth={MAX_DEPTH}, max nodes={MAX_NODES})\n")

    while queue:
        # stop if we've hit the node cap
        if len(results) >= MAX_NODES:
            print(f"\n  [!] Node cap ({MAX_NODES}) reached, stopping crawl.")
            break

        title, depth = queue.popleft()

        # fetch links for this article
        fetched_title, links = fetch_links(title)
        results[fetched_title] = links

        # don't go deeper if we're at max depth
        if depth >= MAX_DEPTH:
            continue

        # add unvisited links to the queue
        for link in links:
            if link.lower() not in visited:
                visited.add(link.lower())
                queue.append((link, depth + 1))

    print(f"\n Crawl complete — {len(results)} articles visited.")
    return results


# --- quick test ---
if __name__ == "__main__":
    results = crawl("Quantum mechanics")
    print(f"\nSample articles crawled:")
    for title in list(results.keys())[:10]:
        print(f"  {title} → {len(results[title])} links")
