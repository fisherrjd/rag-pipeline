import json
import logging
import time
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE_URL = "https://oldschool.runescape.wiki/api.php"

HEADERS = {
    "User-Agent": "@PapaBear#2007",
    "From": "dev@jade.rip",
}


def fetch_index():
    """Fetch all non-redirect pages from the wiki, including their latest revid.

    Uses generator=allpages + prop=revisions so revid comes back in the same
    bulk call — no extra requests needed.

    Yields dicts with keys: pageid, title, revid.
    """
    params = {
        "action": "query",
        "generator": "allpages",
        "gapnamespace": "0",
        "gapfilterredir": "nonredirects",
        "gaplimit": "500",
        "prop": "revisions",
        "rvprop": "ids",
        "format": "json",
    }

    batch = 0
    while True:
        batch += 1
        log.info(f"Fetching index batch {batch}...")
        data = requests.get(BASE_URL, headers=HEADERS, params=params).json()
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            yield {
                "pageid": page["pageid"],
                "title": page["title"],
                "revid": page["revisions"][0]["revid"],
            }
        if "continue" in data:
            params.update(data["continue"])
        else:
            break


def fetch_page_html(title):
    """Fetch the rendered HTML for a single page by title."""
    params = {
        "action": "parse",
        "page": title,
        "prop": "text",
        "format": "json",
    }
    data = requests.get(BASE_URL, headers=HEADERS, params=params).json()
    return data.get("parse", {}).get("text", {}).get("*", "")


def load_manifest(manifest_path: Path) -> dict:
    if manifest_path.exists():
        return json.loads(manifest_path.read_text())
    return {}


def pages_to_fetch(fresh_index: list, manifest: dict) -> list:
    return [
        p
        for p in fresh_index
        if str(p["pageid"]) not in manifest
        or manifest[str(p["pageid"])]["revid"] != p["revid"]
    ]


def sync_pages(pages_dir: Path, manifest_path: Path) -> None:
    pages_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(manifest_path)

    log.info("Fetching index...")
    fresh_index = list(fetch_index())
    log.info(f"Index contains {len(fresh_index)} pages")

    to_fetch = pages_to_fetch(fresh_index, manifest)
    log.info(
        f"{len(to_fetch)} pages to fetch (new or updated), {len(fresh_index) - len(to_fetch)} unchanged"
    )

    for i, page in enumerate(to_fetch):
        pageid = str(page["pageid"])
        title = page["title"]
        log.info(f"[{i + 1}/{len(to_fetch)}] {title}")
        html = fetch_page_html(title)
        (pages_dir / f"{pageid}.html").write_text(html, encoding="utf-8")
        manifest[pageid] = {"title": title, "revid": page["revid"]}
        manifest_path.write_text(json.dumps(manifest, indent=2))

    log.info("Done.")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[3]
    sync_pages(
        pages_dir=project_root / "data" / "pages",
        manifest_path=project_root / "data" / "manifest.json",
    )

    from src.rag_pipeline.ingest.reader import iter_pages

    for page in iter_pages():
        print(f"{page['pageid']}: {page['title']} ({len(page['text'])} chars)")
