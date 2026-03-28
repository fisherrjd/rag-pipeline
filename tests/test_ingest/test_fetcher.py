import json
from unittest.mock import MagicMock, patch

from rag_pipeline.ingest.fetcher import (
    fetch_index,
    fetch_page_html,
    load_manifest,
    pages_to_fetch,
    sync_pages,
)


# --- load_manifest ---


def test_load_manifest_missing(tmp_path):
    assert load_manifest(tmp_path / "manifest.json") == {}


def test_load_manifest_returns_contents(tmp_path):
    data = {"1": {"title": "Abyssal whip", "revid": 42}}
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps(data))
    assert load_manifest(p) == data


# --- pages_to_fetch ---


def test_pages_to_fetch_empty_manifest():
    index = [
        {"pageid": 1, "title": "A", "revid": 100},
        {"pageid": 2, "title": "B", "revid": 200},
    ]
    result = pages_to_fetch(index, {})
    assert result == index


def test_pages_to_fetch_all_current():
    index = [{"pageid": 1, "title": "A", "revid": 100}]
    manifest = {"1": {"title": "A", "revid": 100}}
    assert pages_to_fetch(index, manifest) == []


def test_pages_to_fetch_updated_revid():
    index = [{"pageid": 1, "title": "A", "revid": 101}]
    manifest = {"1": {"title": "A", "revid": 100}}
    result = pages_to_fetch(index, manifest)
    assert len(result) == 1
    assert result[0]["revid"] == 101


def test_pages_to_fetch_mixed():
    index = [
        {"pageid": 1, "title": "A", "revid": 100},  # unchanged
        {"pageid": 2, "title": "B", "revid": 201},  # updated
        {"pageid": 3, "title": "C", "revid": 300},  # new
    ]
    manifest = {
        "1": {"title": "A", "revid": 100},
        "2": {"title": "B", "revid": 200},
    }
    result = pages_to_fetch(index, manifest)
    assert len(result) == 2
    pageids = {p["pageid"] for p in result}
    assert pageids == {2, 3}


# --- fetch_index ---


def _mock_response(data):
    m = MagicMock()
    m.json.return_value = data
    return m


def test_fetch_index_single_batch():
    page_data = {
        "query": {
            "pages": {
                "1": {"pageid": 1, "title": "Goblin", "revisions": [{"revid": 100}]},
                "2": {"pageid": 2, "title": "Cow", "revisions": [{"revid": 200}]},
            }
        }
    }
    with patch("rag_pipeline.ingest.fetcher.requests.get", return_value=_mock_response(page_data)):
        results = list(fetch_index())
    assert len(results) == 2
    assert results[0] == {"pageid": 1, "title": "Goblin", "revid": 100}
    assert results[1] == {"pageid": 2, "title": "Cow", "revid": 200}


def test_fetch_index_follows_continuation():
    batch1 = {
        "query": {
            "pages": {"1": {"pageid": 1, "title": "A", "revisions": [{"revid": 10}]}}
        },
        "continue": {"gapcontinue": "B", "continue": "-||"},
    }
    batch2 = {
        "query": {
            "pages": {"2": {"pageid": 2, "title": "B", "revisions": [{"revid": 20}]}}
        }
    }
    with patch(
        "rag_pipeline.ingest.fetcher.requests.get",
        side_effect=[_mock_response(batch1), _mock_response(batch2)],
    ):
        results = list(fetch_index())
    assert len(results) == 2
    assert {r["title"] for r in results} == {"A", "B"}


def test_fetch_index_empty_result():
    data = {"query": {"pages": {}}}
    with patch("rag_pipeline.ingest.fetcher.requests.get", return_value=_mock_response(data)):
        results = list(fetch_index())
    assert results == []


# --- fetch_page_html ---


def test_fetch_page_html_returns_content():
    data = {"parse": {"text": {"*": "<p>Wiki content</p>"}}}
    with patch("rag_pipeline.ingest.fetcher.requests.get", return_value=_mock_response(data)):
        result = fetch_page_html("Goblin")
    assert result == "<p>Wiki content</p>"


def test_fetch_page_html_missing_parse_key():
    with patch("rag_pipeline.ingest.fetcher.requests.get", return_value=_mock_response({})):
        result = fetch_page_html("Missing")
    assert result == ""


# --- sync_pages ---


def test_sync_pages_writes_html_and_manifest(tmp_path):
    pages_dir = tmp_path / "pages"
    manifest_path = tmp_path / "manifest.json"

    index_data = {
        "query": {
            "pages": {"5": {"pageid": 5, "title": "Dragon", "revisions": [{"revid": 42}]}}
        }
    }
    html_data = {"parse": {"text": {"*": "<p>Dragon info</p>"}}}

    with patch(
        "rag_pipeline.ingest.fetcher.requests.get",
        side_effect=[_mock_response(index_data), _mock_response(html_data)],
    ):
        sync_pages(pages_dir, manifest_path)

    assert (pages_dir / "5.html").read_text(encoding="utf-8") == "<p>Dragon info</p>"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["5"] == {"title": "Dragon", "revid": 42}


def test_sync_pages_skips_unchanged(tmp_path):
    pages_dir = tmp_path / "pages"
    pages_dir.mkdir()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({"5": {"title": "Dragon", "revid": 42}}))

    index_data = {
        "query": {
            "pages": {"5": {"pageid": 5, "title": "Dragon", "revisions": [{"revid": 42}]}}
        }
    }

    with patch("rag_pipeline.ingest.fetcher.requests.get", return_value=_mock_response(index_data)) as mock_get:
        sync_pages(pages_dir, manifest_path)

    # Only one call for the index — no fetch_page_html call
    assert mock_get.call_count == 1
