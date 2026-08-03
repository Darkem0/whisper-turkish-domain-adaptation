from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from .manifests import read_jsonl, validate_manifest
from .metrics import corpus_metrics

PREDICTION_FIELDS = {"sample_id", "prediction"}


def _prediction_map(path: str | Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line_number, row in enumerate(read_jsonl(path), start=1):
        missing = PREDICTION_FIELDS - row.keys()
        if missing:
            raise ValueError(f"{path}:{line_number}: missing {sorted(missing)}")
        sample_id = str(row["sample_id"])
        if sample_id in result:
            raise ValueError(f"{path}:{line_number}: duplicate prediction {sample_id}")
        result[sample_id] = str(row["prediction"])
    return result


def _mean(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def evaluate(
    manifest_path: str | Path,
    predictions_path: str | Path,
    baseline_report_path: str | Path | None = None,
) -> dict:
    validate_manifest(manifest_path)
    rows = list(read_jsonl(manifest_path))
    predictions = _prediction_map(predictions_path)
    expected = {str(row["sample_id"]) for row in rows}
    missing, extra = expected - predictions.keys(), predictions.keys() - expected
    if missing or extra:
        raise ValueError(
            f"prediction coverage mismatch: missing={sorted(missing)[:5]}, extra={sorted(extra)[:5]}"
        )

    grouped: dict[str, list[tuple[str, str]]] = defaultdict(list)
    domain_groups: dict[str, str] = {}
    for row in rows:
        domain = str(row["domain"])
        grouped[domain].append((str(row["reference"]), predictions[str(row["sample_id"])]))
        domain_groups[domain] = str(row.get("domain_group", "unspecified"))

    domains = {domain: corpus_metrics(pairs) for domain, pairs in sorted(grouped.items())}
    clean_domains = [name for name, group in domain_groups.items() if group == "clean"]
    degraded_domains = [name for name, group in domain_groups.items() if group == "degraded"]
    report = {
        "schema_version": 1,
        "domain_metrics": domains,
        "macro": {
            "normalized_wer": _mean(float(value["normalized_wer"]) for value in domains.values()),
            "normalized_cer": _mean(float(value["normalized_cer"]) for value in domains.values()),
            "clean_normalized_wer": _mean(
                float(domains[name]["normalized_wer"]) for name in clean_domains
            ),
            "degraded_normalized_wer": _mean(
                float(domains[name]["normalized_wer"]) for name in degraded_domains
            ),
        },
    }
    if baseline_report_path:
        baseline = json.loads(Path(baseline_report_path).read_text(encoding="utf-8"))
        deltas = {
            domain: float(metrics["normalized_wer"])
            - float(baseline["domain_metrics"][domain]["normalized_wer"])
            for domain, metrics in domains.items()
        }
        report["vs_baseline"] = {
            "domain_normalized_wer_delta": deltas,
            "clean_negative_transfer_max": max((deltas[name] for name in clean_domains), default=0.0),
            "clean_negative_transfer_mean": _mean(deltas[name] for name in clean_domains),
            "macro_normalized_wer_delta": report["macro"]["normalized_wer"]
            - float(baseline["macro"]["normalized_wer"]),
        }
    return report

