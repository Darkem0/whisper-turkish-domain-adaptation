from __future__ import annotations


def suppress_repeated_ngrams(text: str, n: int = 2) -> str:
    """Remove immediately repeated n-grams; use only as an evaluation condition."""
    words = text.split()
    if n < 1:
        raise ValueError("n must be positive")
    output: list[str] = []
    index = 0
    while index < len(words):
        candidate = words[index:index + n]
        if candidate and len(output) >= n and output[-n:] == candidate:
            index += n
            continue
        output.append(words[index])
        index += 1
    return " ".join(output)
