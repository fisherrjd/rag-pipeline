from bs4 import BeautifulSoup, Comment
from markdownify import markdownify as md


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all("span", class_="mw-editsection"):
        tag.decompose()
    for tag in soup.find_all("div", id="toc"):
        tag.decompose()
    for tag in soup.find_all("table", class_="infobox"):
        tag.decompose()
    for tag in soup.find_all("table", class_="navbox"):
        tag.decompose()
    for tag in soup.find_all("table", class_="messagebox"):
        tag.decompose()
    for tag in soup.find_all("figure"):
        tag.decompose()
    # Correctly remove HTML comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    for tag in soup.find_all("div", class_="noexcerpt"):
        tag.decompose()
    # Remove inline image spans (red star icons, logo columns, etc.)
    for tag in soup.find_all(attrs={"typeof": "mw:File"}):
        tag.decompose()
    # Remove league region checkmarks
    for tag in soup.find_all("span", class_="tbz-check"):
        tag.decompose()
    # Remove hatnotes ("Main article: ...")
    for tag in soup.find_all("div", class_="hatnote"):
        tag.decompose()
    # Strip links but keep their text
    for tag in soup.find_all("a"):
        tag.replace_with(tag.get_text())

    return str(soup)


def transform_md(html: str) -> str:
    return md(html)


def clean(html: str) -> str:
    return transform_md(clean_html(html))
