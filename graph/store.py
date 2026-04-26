# graph/store.py
import sqlite3
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_PATH

def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")  # 64MB cache, speeds up lookups
    return conn

def setup_db():
    """Create tables and indexes if they don't exist."""
    conn = get_connection()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS nodes (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    title   TEXT UNIQUE NOT NULL,
    url     TEXT,
    crawled INTEGER DEFAULT 0   -- 0 = just a link target, 1 = fully crawled
);

        CREATE TABLE IF NOT EXISTS edges (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL REFERENCES nodes(id),
            target_id INTEGER NOT NULL REFERENCES nodes(id),
            UNIQUE(source_id, target_id)
        );

        CREATE INDEX IF NOT EXISTS idx_nodes_title
            ON nodes(title);

        CREATE INDEX IF NOT EXISTS idx_edges_source
            ON edges(source_id);

        CREATE INDEX IF NOT EXISTS idx_edges_target
            ON edges(target_id);
    """)
    conn.commit()
    conn.close()
    print("[db] Tables and indexes ready.")

def insert_node(conn: sqlite3.Connection, title: str) -> int:
    """Insert a node if it doesn't exist. Returns its ID either way."""
    url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
    conn.execute(
        "INSERT OR IGNORE INTO nodes (title, url) VALUES (?, ?)",
        (title, url)
    )
    row = conn.execute(
        "SELECT id FROM nodes WHERE title = ?", (title,)
    ).fetchone()
    return row[0]

def insert_edge(conn: sqlite3.Connection, source_id: int, target_id: int):
    """Insert an edge if it doesn't exist."""
    conn.execute(
        "INSERT OR IGNORE INTO edges (source_id, target_id) VALUES (?, ?)",
        (source_id, target_id)
    )

def save_article(conn: sqlite3.Connection, title: str, links: list[str]):
    """
    Save one article and all its links to the DB.
    Accepts an existing connection — no open/close overhead.
    """
    source_id = insert_node(conn, title)
    for link in links:
        target_id = insert_node(conn, link)
        insert_edge(conn, source_id, target_id)

def is_visited(conn: sqlite3.Connection, title: str) -> bool:
    """Check if an article already exists in the DB."""
    row = conn.execute(
        "SELECT id FROM nodes WHERE title = ?", (title,)
    ).fetchone()
    return row is not None

def get_stats(conn: sqlite3.Connection) -> dict:
    """Quick summary of what's in the DB."""
    nodes = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    edges = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
    return {"nodes": nodes, "edges": edges}

def mark_crawled(conn: sqlite3.Connection, title: str):
    conn.execute(
        "UPDATE nodes SET crawled = 1 WHERE title = ?", (title,)
    )

def is_crawled(conn: sqlite3.Connection, title: str) -> bool:
    row = conn.execute(
        "SELECT crawled FROM nodes WHERE title = ?", (title,)
    ).fetchone()
    return row is not None and row[0] == 1

# --- quick test ---
if __name__ == "__main__":
    setup_db()
    conn = get_connection()
    save_article(conn, "Quantum mechanics", ["Wave function", "Albert Einstein", "Niels Bohr"])
    save_article(conn, "Wave function", ["Quantum mechanics", "Schrödinger equation"])
    conn.commit()
    print(get_stats(conn))
    conn.close()
