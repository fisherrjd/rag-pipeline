import json
import os

from rag_pipeline.ingest.reader import _load_manifest, iter_pages


# --- _load_manifest ---


def test_load_manifest_missing_file(tmp_path):
    assert _load_manifest(tmp_path / "manifest.json") == {}


def test_load_manifest_returns_contents(tmp_path):
    manifest = {"123": {"title": "Goblin", "revid": 999}}
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps(manifest))
    assert _load_manifest(p) == manifest


# --- iter_pages ---


def _write_html(pages_dir, pageid, content="<p>Hello</p>"):
    (pages_dir / f"{pageid}.html").write_text(content, encoding="utf-8")


def _write_manifest(tmp_path, data):
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps(data))
    return p


def test_iter_pages_no_html_files(tmp_path):
    pages_dir = tmp_path / "pages"
    pages_dir.mkdir()
    manifest_path = _write_manifest(tmp_path, {})
    results = list(iter_pages(pages_dir, manifest_path))
    assert results == []


def test_iter_pages_converts_html_to_md(tmp_path):
    pages_dir = tmp_path / "pages"
    pages_dir.mkdir()
    manifest_path = _write_manifest(tmp_path, {"42": {"title": "Goblin", "revid": 1}})
    _write_html(pages_dir, "42", "<p>Some content</p>")

    results = list(iter_pages(pages_dir, manifest_path))
    assert len(results) == 1
    assert results[0]["pageid"] == "42"
    assert results[0]["title"] == "Goblin"
    assert "Some content" in results[0]["text"]
    assert (pages_dir / "42.md").exists()


def test_iter_pages_uses_cached_md(tmp_path):
    pages_dir = tmp_path / "pages"
    pages_dir.mkdir()
    manifest_path = _write_manifest(tmp_path, {"7": {"title": "Cow", "revid": 2}})

    html_path = pages_dir / "7.html"
    html_path.write_text("<p>Original</p>", encoding="utf-8")

    # Write md with a newer mtime
    md_path = pages_dir / "7.md"
    md_path.write_text("cached markdown", encoding="utf-8")
    future = html_path.stat().st_mtime + 10
    import os
    os.utime(md_path, (future, future))

    results = list(iter_pages(pages_dir, manifest_path))
    assert results[0]["text"] == "cached markdown"


def test_iter_pages_reconverts_stale_md(tmp_path):
    pages_dir = tmp_path / "pages"
    pages_dir.mkdir()
    manifest_path = _write_manifest(tmp_path, {"9": {"title": "Dragon", "revid": 3}})

    html_path = pages_dir / "9.html"
    html_path.write_text("<p>New content</p>", encoding="utf-8")

    md_path = pages_dir / "9.md"
    md_path.write_text("stale markdown", encoding="utf-8")
    # Force md mtime to be older than html
    past = html_path.stat().st_mtime - 10
    os.utime(md_path, (past, past))

    results = list(iter_pages(pages_dir, manifest_path))
    assert results[0]["text"] != "stale markdown"
    assert "New content" in results[0]["text"]


def test_iter_pages_falls_back_to_pageid_for_title(tmp_path):
    pages_dir = tmp_path / "pages"
    pages_dir.mkdir()
    manifest_path = _write_manifest(tmp_path, {})  # empty manifest
    _write_html(pages_dir, "55")

    results = list(iter_pages(pages_dir, manifest_path))
    assert results[0]["title"] == "55"
