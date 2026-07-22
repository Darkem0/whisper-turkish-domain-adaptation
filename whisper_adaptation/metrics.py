from __future__ import annotations

import re
import unicodedata


def normalize_turkish(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    # Casefold turns the capital dotted Turkish I into i plus a combining dot.
    # Collapse only that sequence; do not strip the meaningful Turkish letters.
    text = text.replace("i\u0307", "i")
    text = re.sub(r"[^\w\sçğıöşü]", " ", text, flags=re.UNICODE)
    return " ".join(text.split())


def edit_distance(reference: list[str], hypothesis: list[str]) -> int:
    previous = list(range(len(hypothesis) + 1))
    for i, ref_token in enumerate(reference, start=1):
        current = [i]
        for j, hyp_token in enumerate(hypothesis, start=1):
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + (ref_token != hyp_token),
                )
            )
        previous = current
    return previous[-1]


def error_rate(reference: str, hypothesis: str, unit: str = "word", normalize: bool = False) -> float:
    if normalize:
        reference, hypothesis = normalize_turkish(reference), normalize_turkish(hypothesis)
    if unit == "word":
        ref, hyp = reference.split(), hypothesis.split()
    elif unit == "char":
        ref, hyp = list(reference.replace(" ", "")), list(hypothesis.replace(" ", ""))
    else:
        raise ValueError("unit must be word or char")
    return 0.0 if not ref else edit_distance(ref, hyp) / len(ref)


def score_pair(reference: str, hypothesis: str) -> dict[str, float]:
    return {
        "raw_wer": round(error_rate(reference, hypothesis, "word"), 4),
        "normalized_wer": round(error_rate(reference, hypothesis, "word", normalize=True), 4),
        "raw_cer": round(error_rate(reference, hypothesis, "char"), 4),
        "normalized_cer": round(error_rate(reference, hypothesis, "char", normalize=True), 4),
    }
