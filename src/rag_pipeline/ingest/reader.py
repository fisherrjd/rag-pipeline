import json
import logging
from pathlib import Path
from collections.abc import Iterator

from rag_pipeline.ingest.cleaner import clean

log = logging.getLogger(__name__)

PAGES_DIR = Path.cwd() / "data" / "pages"
MANIFEST_PATH = Path.cwd() / "data" / "manifest.json"


def iter_pages(pages_dir: Path = PAGES_DIR, manifest_path: Path = MANIFEST_PATH) -> Iterator[dict]:
    """Yield cleaned page dicts with keys: pageid, title, text.

    For each page, uses a cached .md if present. Otherwise converts the .html
    via cleaner and saves the result as .md alongside the source file.
    """
    manifest = _load_manifest(manifest_path)
    log.info(f"Reading pages from {pages_dir}")

    for html_path in sorted(pages_dir.glob("*.html")):
        pageid = html_path.stem
        md_path = html_path.with_suffix(".md")

        if md_path.exists() and md_path.stat().st_mtime >= html_path.stat().st_mtime:
            log.debug(f"Cache hit {pageid}")
            text = md_path.read_text(encoding="utf-8")
        else:
            log.info(f"Converting {pageid} to markdown...")
            html = html_path.read_text(encoding="utf-8")
            text = clean(html)
            md_path.write_text(text, encoding="utf-8")
            log.info(f"Wrote {md_path}")

        title = manifest.get(pageid, {}).get("title", pageid)
        yield {"pageid": pageid, "title": title, "text": text}


def _load_manifest(manifest_path: Path = MANIFEST_PATH) -> dict:
    if manifest_path.exists():
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    return {}
