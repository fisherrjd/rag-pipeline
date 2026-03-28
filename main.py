from rag_pipeline.chunking.splitter import _parse_sections
from rag_pipeline.ingest.reader import iter_pages


def main():
    page = next(iter_pages())
    print(f"Page: {page['title']}\n")
    for title, content in _parse_sections(page["text"]):
        print(f"  [{title!r}] {len(content.split())} words")
        print(f"    {content[:80].replace(chr(10), ' ')!r}")


if __name__ == "__main__":
    main()
