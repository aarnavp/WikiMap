# crawler/queue.py
from collections import deque
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.fetcher import fetch_links
from graph.store import setup_db, get_connection, save_article, is_crawled, mark_crawled, get_stats
from config import MAX_DEPTH, MAX_NODES, SEED_ARTICLES

COMMIT_EVERY = 50  # commit to DB every N articles

#from graph.store import setup_db, get_connection, save_article, is_crawled, mark_crawled, get_stats

def crawl(seed: str):
    conn = get_connection()

    queue = deque()
    queue.append((seed, 0))

    visited = set()
    visited.add(seed.lower())
    count = 0

    print(f"\n[crawl] Starting from '{seed}' (max_depth={MAX_DEPTH}, max_nodes={MAX_NODES})\n")

    while queue:
        if count >= MAX_NODES:
            print(f"\n  [!] Node cap ({MAX_NODES}) reached.")
            break

        title, depth = queue.popleft()

        # skip if already fully crawled (from a previous run)
        if is_crawled(conn, title):
            print(f"  [~] '{title}' already crawled, skipping.")
            continue

        fetched_title, links = fetch_links(title)
        save_article(conn, fetched_title, links)
        mark_crawled(conn, fetched_title)  # mark as fully crawled
        count += 1

        if count % COMMIT_EVERY == 0:
            conn.commit()
            stats = get_stats(conn)
            print(f"  [db] {stats['nodes']} nodes, {stats['edges']} edges in DB")

        if depth >= MAX_DEPTH:
            continue

        for link in links:
            if link.lower() not in visited:
                visited.add(link.lower())
                queue.append((link, depth + 1))

    conn.commit()
    stats = get_stats(conn)
    print(f"\n[crawl] Done — {stats['nodes']} nodes, {stats['edges']} edges in DB.")
    conn.close()


def crawl_all():
    """Loop over all seeds in config."""
    setup_db()
    for seed in SEED_ARTICLES:
        print(f"\n{'='*50}")
        print(f"  Seed: {seed}")
        print(f"{'='*50}")
        crawl(seed)


# --- quick test ---
if __name__ == "__main__":
    crawl_all()
