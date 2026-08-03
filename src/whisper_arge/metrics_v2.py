from __future__ import annotations

from collections.abc import Iterable

from .metrics import corpus_metrics


def disfluency_metrics(pairs: Iterable[tuple[str, str]], marker: str = "[disfluency]") -> dict[str, float | int]:
    true_positive = false_positive = false_negative = 0
    for reference, hypothesis in pairs:
        reference_count, hypothesis_count = reference.lower().count(marker), hypothesis.lower().count(marker)
        true_positive += min(reference_count, hypothesis_count)
        false_positive += max(0, hypothesis_count - reference_count)
        false_negative += max(0, reference_count - hypothesis_count)
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    return {"disfluency_precision": precision, "disfluency_recall": recall, "disfluency_f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0, "disfluency_reference_count": true_positive + false_negative}


def normalized_wer_for_rows(rows: list[dict]) -> float:
    return float(corpus_metrics([(str(row["reference"]), str(row["prediction"])) for row in rows])["normalized_wer"])
