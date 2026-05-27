"""Text chunking utilities for document ingestion."""


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 80) -> list[str]:
    """
    Split text into overlapping chunks by character count.
    Tries to break on sentence boundaries when possible.
    """
    text = text.strip()
    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)
        if end < length:
            boundary = text.rfind(". ", start, end)
            if boundary == -1:
                boundary = text.rfind("\n", start, end)
            if boundary != -1 and boundary > start + chunk_size // 2:
                end = boundary + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= length:
            break
        start = max(end - overlap, start + 1)

    # Remove duplicate chunks
    unique_chunks = []
    seen = set()

    for chunk in chunks:
        normalized = chunk.strip().lower()

        if normalized in seen:
            continue

        seen.add(normalized)
        unique_chunks.append(chunk)

    return unique_chunks
