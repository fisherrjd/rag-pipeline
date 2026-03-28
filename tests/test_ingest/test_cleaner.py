from rag_pipeline.ingest.cleaner import clean, clean_html


def _soup_text(html: str) -> str:
    """Run clean_html and return the plain text content."""
    from bs4 import BeautifulSoup

    return BeautifulSoup(clean_html(html), "html.parser").get_text()


# --- element removal ---


def test_removes_edit_section_spans():
    html = "<p>Hello <span class='mw-editsection'>[edit]</span></p>"
    assert "[edit]" not in clean_html(html)


def test_removes_toc():
    html = "<div id='toc'><ul><li>Contents</li></ul></div><p>Body</p>"
    result = clean_html(html)
    assert "Contents" not in result
    assert "Body" in result


def test_removes_infobox():
    html = "<table class='infobox'><tr><td>Stats</td></tr></table><p>Text</p>"
    result = clean_html(html)
    assert "Stats" not in result
    assert "Text" in result


def test_removes_infobox_multiclass():
    html = "<table class='infobox infobox-clean'><tr><td>Stats</td></tr></table>"
    assert "Stats" not in clean_html(html)


def test_removes_navbox():
    html = "<table class='navbox'><tr><td>Nav</td></tr></table><p>Body</p>"
    result = clean_html(html)
    assert "Nav" not in result


def test_removes_messagebox():
    html = "<table class='messagebox'><tr><td>Note</td></tr></table><p>Body</p>"
    assert "Note" not in clean_html(html)


def test_removes_figure():
    html = "<figure><img src='x.png'/><figcaption>Cap</figcaption></figure><p>Text</p>"
    result = clean_html(html)
    assert "Cap" not in result
    assert "Text" in result


def test_removes_html_comments():
    html = "<!-- secret --><p>Visible</p>"
    assert "secret" not in clean_html(html)
    assert "Visible" in clean_html(html)


def test_removes_noexcerpt():
    html = "<div class='noexcerpt'>Skip me</div><p>Keep me</p>"
    result = clean_html(html)
    assert "Skip me" not in result
    assert "Keep me" in result


def test_removes_mw_file():
    html = "<span typeof='mw:File'><img src='icon.png'/></span><p>Text</p>"
    result = clean_html(html)
    assert "mw:File" not in result
    assert "Text" in result


def test_removes_tbz_check():
    html = "<span class='tbz-check'>✓</span><p>Region</p>"
    result = clean_html(html)
    assert "tbz-check" not in result


def test_removes_hatnote():
    html = "<div class='hatnote'>Main article: Foo</div><p>Content</p>"
    result = clean_html(html)
    assert "Main article" not in result
    assert "Content" in result


# --- link stripping ---


def test_strips_links_keeps_text():
    html = "<p><a href='/wiki/Rune_platebody'>Rune platebody</a></p>"
    result = clean_html(html)
    assert "Rune platebody" in result
    assert "<a" not in result


# --- complex table flattening ---


def test_flattens_table_with_colspan():
    html = (
        "<table><tr><td colspan='2'>Header</td></tr>"
        "<tr><td>A</td><td>B</td></tr></table>"
    )
    result = clean_html(html)
    assert "<table" not in result
    assert "Header" in result
    assert "A" in result


def test_flattens_table_with_rowspan():
    html = "<table><tr><td rowspan='2'>Span</td><td>X</td></tr></table>"
    result = clean_html(html)
    assert "<table" not in result
    assert "Span" in result


def test_preserves_simple_table():
    html = "<table><tr><td>Cell</td></tr></table>"
    result = clean_html(html)
    assert "<table" in result


# --- clean() produces markdown ---


def test_clean_returns_markdown_heading():
    html = "<h2>Overview</h2><p>Some text.</p>"
    result = clean(html)
    assert "## Overview" in result


def test_clean_returns_string():
    assert isinstance(clean("<p>hello</p>"), str)
