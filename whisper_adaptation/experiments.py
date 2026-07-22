from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .metrics import score_pair
from .routing import choose_adapter


def load_manifest(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def evaluate_manifest(path: str) -> dict[str, object]:
    manifest = load_manifest(path)
    dataset_path = Path(path).parent.parent / manifest["dataset"]
    rows = [json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines() if line]
    by_domain: dict[str, list[dict[str, float]]] = defaultdict(list)
    for row in rows:
        prediction = row[manifest["prediction_field"]]
        by_domain[row["domain"]].append(score_pair(row["reference"], prediction))
    summary = {
        domain: {
            metric: round(sum(sample[metric] for sample in values) / len(values), 4)
            for metric in ("raw_wer", "normalized_wer", "raw_cer", "normalized_cer")
        }
        for domain, values in by_domain.items()
    }
    routing = manifest.get("routing", {})
    return {
        "mode": "synthetic_reproducible_mock",
        "experiment": manifest["id"],
        "domain_metrics": summary,
        "routing_preview": {domain: choose_adapter(domain, routing) for domain in summary},
        "private_data_used": False,
    }
