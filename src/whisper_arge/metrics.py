from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .normalization import normalize_turkish

METRICS_ID = "corpus_wer_cer_v1"


def edit_distance(reference: list[str], hypothesis: list[str]) -> int:
    previous = list(range(len(hypothesis) + 1))
    for row, ref_token in enumerate(reference, start=1):
        current = [row]
        for column, hyp_token in enumerate(hypothesis, start=1):
            current.append(
                min(
                    previous[column] + 1,
                    current[column - 1] + 1,
                    previous[column - 1] + int(ref_token != hyp_token),
                )
            )
        previous = current
    return previous[-1]


@dataclass(frozen=True)
class ErrorCounts:
    word_errors: int = 0
    reference_words: int = 0
    char_errors: int = 0
    reference_chars: int = 0

    def __add__(self, other: "ErrorCounts") -> "ErrorCounts":
        return ErrorCounts(
            self.word_errors + other.word_errors,
            self.reference_words + other.reference_words,
            self.char_errors + other.char_errors,
            self.reference_chars + other.reference_chars,
        )

    def rates(self) -> dict[str, float]:
        return {
            "wer": self.word_errors / self.reference_words if self.reference_words else 0.0,
            "cer": self.char_errors / self.reference_chars if self.reference_chars else 0.0,
        }


def pair_counts(reference: str, hypothesis: str) -> ErrorCounts:
    ref_words, hyp_words = reference.split(), hypothesis.split()
    ref_chars = list(reference.replace(" ", ""))
    hyp_chars = list(hypothesis.replace(" ", ""))
    return ErrorCounts(
        word_errors=edit_distance(ref_words, hyp_words),
        reference_words=len(ref_words),
        char_errors=edit_distance(ref_chars, hyp_chars),
        reference_chars=len(ref_chars),
    )


def corpus_metrics(pairs: Iterable[tuple[str, str]]) -> dict[str, float | int]:
    raw = ErrorCounts()
    normalized = ErrorCounts()
    samples = 0
    for reference, hypothesis in pairs:
        samples += 1
        raw += pair_counts(reference, hypothesis)
        normalized += pair_counts(normalize_turkish(reference), normalize_turkish(hypothesis))
    raw_rates, normalized_rates = raw.rates(), normalized.rates()
    return {
        "samples": samples,
        "raw_wer": raw_rates["wer"],
        "raw_cer": raw_rates["cer"],
        "normalized_wer": normalized_rates["wer"],
        "normalized_cer": normalized_rates["cer"],
        "reference_words": raw.reference_words,
        "reference_chars": raw.reference_chars,
    }

