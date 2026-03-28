import pytest

from rag_pipeline.chunking.splitter import (
    _apply_overlap,
    _count_words,
    _parse_sections,
    _recursive_split,
    chunk_page,
    split,
)

SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


# --- _count_words ---


def test_count_words_basic():
    assert _count_words("hello world foo") == 3


def test_count_words_empty():
    assert _count_words("") == 0


# --- _parse_sections ---


def test_parse_sections_no_headers():
    text = "Just some intro text with no headers."
    sections = _parse_sections(text)
    assert sections == [("", "Just some intro text with no headers.")]


def test_parse_sections_intro_and_headers():
    text = "Intro text.\n\n## Section One\nContent one.\n\n## Section Two\nContent two."
    sections = _parse_sections(text)
    assert sections[0] == ("", "Intro text.")
    assert sections[1] == ("Section One", "Content one.")
    assert sections[2] == ("Section Two", "Content two.")


def test_parse_sections_no_intro():
    text = "## Section One\nContent.\n\n### Sub\nSub content."
    sections = _parse_sections(text)
    assert sections[0] == ("Section One", "Content.")
    assert sections[1] == ("Sub", "Sub content.")


def test_parse_sections_empty_section():
    text = "## Empty\n\n## Has content\nSome text."
    sections = _parse_sections(text)
    assert sections[0] == ("Empty", "")
    assert sections[1] == ("Has content", "Some text.")


def test_parse_sections_h3_only():
    text = "### Deep section\nContent here."
    sections = _parse_sections(text)
    assert sections[0] == ("Deep section", "Content here.")


def test_parse_sections_ignores_h1():
    text = "# Title\nIntro.\n\n## Section\nContent."
    sections = _parse_sections(text)
    # H1 is not a split boundary — treated as intro text
    assert sections[0][0] == ""
    assert "Title" in sections[0][1]


# --- _recursive_split ---


def test_recursive_split_fits_in_one_chunk():
    text = "one two three"
    result = _recursive_split(text, SEPARATORS, 10, _count_words)
    assert result == ["one two three"]


def test_recursive_split_on_paragraphs():
    para = "word " * 10  # 10 words
    text = (para.strip() + "\n\n") * 3 + para.strip()
    result = _recursive_split(text, SEPARATORS, 15, _count_words)
    assert len(result) > 1
    for chunk in result:
        assert _count_words(chunk) <= 15


def test_recursive_split_all_chunks_within_size():
    text = " ".join([f"word{i}" for i in range(200)])
    result = _recursive_split(text, SEPARATORS, 50, _count_words)
    for chunk in result:
        assert _count_words(chunk) <= 50


def test_recursive_split_hard_split_fallback():
    # Single long line with no separators — forces word-by-word split
    text = " ".join([f"word{i}" for i in range(100)])
    result = _recursive_split(text, [""], 20, _count_words)
    assert len(result) > 1
    for chunk in result:
        assert _count_words(chunk) <= 20


# --- _apply_overlap ---


def test_apply_overlap_single_chunk():
    chunks = ["only chunk"]
    assert _apply_overlap(chunks, 5, _count_words) == ["only chunk"]


def test_apply_overlap_zero():
    chunks = ["chunk one", "chunk two"]
    assert _apply_overlap(chunks, 0, _count_words) == chunks


def test_apply_overlap_prepends_tail_of_previous():
    chunks = ["alpha beta gamma", "delta epsilon"]
    result = _apply_overlap(chunks, 2, _count_words)
    assert result[0] == "alpha beta gamma"
    assert result[1].startswith("beta gamma")
    assert "delta epsilon" in result[1]


def test_apply_overlap_first_chunk_unchanged():
    chunks = ["a b c d e", "f g h"]
    result = _apply_overlap(chunks, 3, _count_words)
    assert result[0] == "a b c d e"


# --- split ---


def test_split_returns_list_of_strings():
    text = " ".join([f"word{i}" for i in range(100)])
    result = split(text, chunk_size=20, overlap=5)
    assert isinstance(result, list)
    assert all(isinstance(c, str) for c in result)


def test_split_with_overlap_second_chunk_starts_with_overlap():
    text = " ".join([f"word{i}" for i in range(60)])
    chunks = split(text, chunk_size=20, overlap=5)
    assert len(chunks) > 1
    # The tail of chunk 0 should appear at the start of chunk 1
    tail_words = chunks[0].split()[-5:]
    for word in tail_words:
        assert word in chunks[1]


# --- chunk_page ---


def _make_page(text, pageid="1", title="Test Page"):
    return {"pageid": pageid, "title": title, "text": text}


def test_chunk_page_returns_dicts_with_metadata():
    page = _make_page("## Section\nSome content here.")
    chunks = chunk_page(page)
    assert len(chunks) == 1
    assert chunks[0]["pageid"] == "1"
    assert chunks[0]["title"] == "Test Page"
    assert chunks[0]["section"] == "Section"
    assert chunks[0]["part"] == 0
    assert "content" in chunks[0]["text"]


def test_chunk_page_skips_empty_sections():
    page = _make_page("## Empty\n\n## Has content\nSome text.")
    chunks = chunk_page(page)
    assert len(chunks) == 1
    assert chunks[0]["section"] == "Has content"


def test_chunk_page_intro_has_empty_section_key():
    page = _make_page("Intro text.\n\n## Section\nContent.")
    chunks = chunk_page(page)
    assert chunks[0]["section"] == ""
    assert "Intro" in chunks[0]["text"]


def test_chunk_page_large_section_splits_into_parts():
    big_content = " ".join([f"word{i}" for i in range(600)])
    page = _make_page(f"## Big Section\n{big_content}")
    chunks = chunk_page(page, chunk_size=100, overlap=0)
    assert len(chunks) > 1
    assert all(c["section"] == "Big Section" for c in chunks)
    parts = [c["part"] for c in chunks]
    assert parts == list(range(len(chunks)))


def test_chunk_page_custom_tokenizer():
    page = _make_page("## Section\n" + " ".join(["x"] * 200))
    chunks = chunk_page(page, chunk_size=50, overlap=0, count_tokens=_count_words)
    assert len(chunks) > 1
