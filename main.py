from rag_pipeline.chunking.splitter import chunk_page
from rag_pipeline.ingest.reader import iter_pages

PAGES = {"Minigames"}


def main():
    for page in iter_pages():
        if page["title"] not in PAGES:
            continue
        chunks = chunk_page(page)
        print(f"\n=== {page['title']} — {len(chunks)} chunks ===")
        for chunk in chunks:
            section = chunk["section"] or "intro"
            part = f" part={chunk['part']}" if chunk["part"] > 0 else ""
            words = len(chunk["text"].split())
            print(f"  [{section}{part}] {words} words")
            print(f"    {chunk['text'][:80].replace(chr(10), ' ')!r}")


if __name__ == "__main__":
    main()
