# crawler/parser.py

# Articles that appear everywhere and add no meaningful connection
BLOCKLIST = {
    "United States", "United Kingdom", "England", "France", "Germany",
    "Latin", "Greek language", "Ancient Greece", "Europe", "London",
    "New York City", "Wikipedia", "Wikimedia", "Commons",
}

# Skip articles whose titles start with these (metadata, years, dates)
SKIP_PREFIXES = (
    "List of", "Index of", "Outline of",
    "Portal:", "Category:", "File:", "Help:",
)

# Skip articles whose titles are just a number (years like "1905")
def is_year(title: str) -> bool:
    return title.strip().isdigit()

def filter_links(links: list[str], max_links: int = 50) -> list[str]:
    """
    Clean and trim a raw list of Wikipedia link titles.
    """
    filtered = []
    for title in links:
        if title in BLOCKLIST:
            continue
        if title.startswith(SKIP_PREFIXES):
            continue
        if is_year(title):
            continue
        filtered.append(title)

    # Cap per-article links to avoid explosion at depth 2
    return filtered[:max_links]
