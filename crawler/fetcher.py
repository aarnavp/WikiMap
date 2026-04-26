# crawler/fetcher.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import wikipediaapi
from config import REQUEST_DELAY
from crawler.parser import filter_links
from crawler.parser import *

wiki = wikipediaapi.Wikipedia(
    language="en",
    user_agent="wiki-graph-explorer/1.0 (learning project)"
)

def fetch_links(title: str) -> tuple[str, list[str]]:
    """
    Fetch all internal Wikipedia links for a given article title.
    Returns (title, [linked_titles])
    """
    page = wiki.page(title)

    if not page.exists():
        print(f"  [!] Article not found: '{title}'")
        return title, []

    links = list(page.links.keys())
    links = filter_links(links)
    print(f"  [+] '{title}' → {len(links)} links (filtered)")
    return title, links


def fetch_many(titles: list[str]) -> dict[str, list[str]]:
    """
    Fetch links for a list of titles sequentially.
    Returns {title: [linked_titles]}
    """
    results = {}
    for title in titles:
        t, links = fetch_links(title)
        results[t] = links
    return results

from config import MAX_LINKS_PER_ARTICLE

def filter_links(links: list[str]) -> list[str]:
    filtered = []
    for title in links:
        if title in BLOCKLIST:
            continue
        if title.startswith(SKIP_PREFIXES):
            continue
        if is_year(title):
            continue
        filtered.append(title)

    return filtered[:MAX_LINKS_PER_ARTICLE]
# --- quick test ---
if __name__ == "__main__":
    title = "Quantum mechanics"
    t, links = fetch_links(title)
    print(f"\nArticle: {t}")
    print(f"Links found: {len(links)}")
    print(f"First 10: {links[:10]}")
