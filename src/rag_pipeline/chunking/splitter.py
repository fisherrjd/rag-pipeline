import re
from collections.abc import Callable

SEPARATORS = ["\n\n", "\n", ". ", " ", ""]
HEADER_RE = re.compile(r'^(#{2,3})\s+(.+)$', re.MULTILINE)


def _parse_sections(text: str) -> list[tuple[str, str]]:
    """Split markdown text into (section_title, content) pairs.

    Intro text before the first header gets the title "".
    Each ## or ### header starts a new section; content runs until the next header.
    """
    sections = []
    matches = list(HEADER_RE.finditer(text))

    # Capture any intro text that appears before the first header
    intro_end = matches[0].start() if matches else len(text)
    intro = text[:intro_end].strip()
    if intro:
        sections.append(("", intro))

    for i, match in enumerate(matches):
        title = match.group(2).strip()
        content_start = match.end()
        content_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[content_start:content_end].strip()
        sections.append((title, content))

    return sections


def _count_words(text: str) -> int:
    return len(text.split())


def _recursive_split(
    text: str,
    separators: list[str],
    chunk_size: int,
    count_tokens: Callable[[str], int],
) -> list[str]:
    # Base case: text already fits in a chunk
    if count_tokens(text) <= chunk_size:
        return [text]

    separator, *remaining = separators

    # Last resort: no separator left, hard-split word by word
    if separator == "":
        words = text.split()
        chunks, current = [], []
        for word in words:
            current.append(word)
            if count_tokens(" ".join(current)) > chunk_size:
                chunks.append(" ".join(current[:-1]))
                current = [word]
        if current:
            chunks.append(" ".join(current))
        return chunks

    parts = text.split(separator)
    chunks, current = [], ""

    for i, part in enumerate(parts):
        # Re-attach the separator to all parts except the last
        piece = part + (separator if i < len(parts) - 1 else "")
        candidate = current + piece if current else piece

        if count_tokens(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            # If this piece alone is too big, recurse with the next separator
            if count_tokens(piece) > chunk_size:
                chunks.extend(_recursive_split(piece, remaining, chunk_size, count_tokens))
                current = ""
            else:
                current = piece

    if current:
        chunks.append(current)

    return chunks


def _apply_overlap(
    chunks: list[str],
    overlap: int,
    count_tokens: Callable[[str], int],
) -> list[str]:
    if overlap == 0 or len(chunks) <= 1:
        return chunks

    result = [chunks[0]]
    for i in range(1, len(chunks)):
        prev_words = chunks[i - 1].split()
        overlap_text = " ".join(prev_words[-overlap:])
        result.append(overlap_text + " " + chunks[i])

    return result


def split(
    text: str,
    chunk_size: int = 512,
    overlap: int = 50,
    count_tokens: Callable[[str], int] = _count_words,
) -> list[str]:
    chunks = _recursive_split(text, SEPARATORS, chunk_size, count_tokens)
    return _apply_overlap(chunks, overlap, count_tokens)


def chunk_page(
    page: dict,
    chunk_size: int = 512,
    overlap: int = 50,
    count_tokens: Callable[[str], int] = _count_words,
) -> list[dict]:
    """Chunk a page dict into sections, falling back to recursive splitting for
    sections that exceed chunk_size. Returns list of chunk dicts with metadata."""
    chunks = []

    for section, content in _parse_sections(page["text"]):
        if not content:
            continue

        if count_tokens(content) <= chunk_size:
            sub_chunks = [content]
        else:
            sub_chunks = _apply_overlap(
                _recursive_split(content, SEPARATORS, chunk_size, count_tokens),
                overlap,
                count_tokens,
            )

        for i, text in enumerate(sub_chunks):
            chunks.append({
                "pageid": page["pageid"],
                "title": page["title"],
                "section": section,
                "part": i,
                "text": text,
            })

    return chunks
