from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .bootstrap import bootstrap_ci
from .evaluation import _mean, _prediction_map
from .manifests import read_jsonl, validate_manifest
from .metrics import pair_counts
from .metrics_v2 import disfluency_metrics, normalized_wer_for_rows
from .normalization import normalize_turkish


def evaluate_v2(manifest_path: str | Path, predictions_path: str | Path) -> dict:
    validate_manifest(manifest_path)
    rows = list(read_jsonl(manifest_path))
    predictions = _prediction_map(predictions_path)
    expected = {str(row["sample_id"]) for row in rows}
    if expected != predictions.keys():
        raise ValueError("prediction coverage mismatch")
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[str(row["domain"])].append(
            {**row, "prediction": predictions[str(row["sample_id"])]}
        )
    domains: dict[str, dict] = {}
    for domain, domain_rows in sorted(grouped.items()):
        pairs = [(str(row["reference"]), str(row["prediction"])) for row in domain_rows]
        metric = {"normalized_wer": normalized_wer_for_rows(domain_rows)}
        from .metrics import corpus_metrics

        metric.update(corpus_metrics(pairs))
        if any("[disfluency]" in str(row["reference"]).lower() for row in domain_rows):
            metric.update(disfluency_metrics(pairs))
        for row in domain_rows:
            counts = pair_counts(
                normalize_turkish(str(row["reference"])), normalize_turkish(str(row["prediction"]))
            )
            row["_normalized_word_errors"] = counts.word_errors
            row["_normalized_reference_words"] = counts.reference_words

        def cached_normalized_wer(items: list[dict]) -> float:
            errors = sum(int(item["_normalized_word_errors"]) for item in items)
            words = sum(int(item["_normalized_reference_words"]) for item in items)
            return errors / words if words else 0.0

        block_key = (
            "speaker_id"
            if any(row.get("speaker_id") for row in domain_rows)
            else "source_id"
            if any(row.get("source_id") for row in domain_rows)
            else None
        )
        metric["normalized_wer_ci95"] = bootstrap_ci(
            domain_rows, cached_normalized_wer, block_key=block_key
        )
        domains[domain] = metric
    primary_weights = {"tsc_holdout": 0.6, "mediaspeech_test": 0.4}
    primary_available = {
        name: weight for name, weight in primary_weights.items() if name in domains
    }
    primary = (
        sum(domains[name]["normalized_wer"] * weight for name, weight in primary_available.items())
        / sum(primary_available.values())
        if primary_available
        else None
    )
    by_sample = {str(row["sample_id"]): row for row in rows}
    paired: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        clean_id = row.get("paired_clean_sample_id")
        if clean_id and str(clean_id) in by_sample:
            clean = by_sample[str(clean_id)]
            delta = (
                pair_counts(str(row["reference"]), predictions[str(row["sample_id"])]).rates()[
                    "wer"
                ]
                - pair_counts(
                    str(clean["reference"]), predictions[str(clean["sample_id"])]
                ).rates()["wer"]
            )
            paired[str(row.get("degradation", "unknown"))].append(
                {"delta": delta, "pair_id": str(clean_id)}
            )
    return {
        "schema_version": 2,
        "domain_metrics": domains,
        "primary_target_proxy_normalized_wer": primary,
        "paired_degradation": {
            name: bootstrap_ci(
                items,
                lambda sample: _mean(float(item["delta"]) for item in sample),
                block_key="pair_id",
            )
            for name, items in sorted(paired.items())
        },
    }
