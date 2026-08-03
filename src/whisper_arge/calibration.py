from __future__ import annotations

import json
import math
from pathlib import Path


CALIBRATION_IDS = ("A1", "A2", "A3", "A6")


def _ranks(values: list[float]) -> list[float]:
    ranked = sorted(enumerate(values), key=lambda item: item[1])
    result = [0.0] * len(values)
    start = 0
    while start < len(ranked):
        end = start + 1
        while end < len(ranked) and ranked[end][1] == ranked[start][1]:
            end += 1
        rank = (start + 1 + end) / 2
        for index, _ in ranked[start:end]:
            result[index] = rank
        start = end
    return result


def spearman_rank_correlation(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        raise ValueError("Spearman correlation requires equally sized vectors with at least two values")
    x, y = _ranks(left), _ranks(right)
    mean_x, mean_y = sum(x) / len(x), sum(y) / len(y)
    numerator = sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y))
    denominator = math.sqrt(sum((a - mean_x) ** 2 for a in x) * sum((b - mean_y) ** 2 for b in y))
    return numerator / denominator if denominator else 0.0


def smoke_calibration(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = payload["results"] if isinstance(payload, dict) else payload
    scores = {str(row["id"]): row for row in rows}
    missing = [item for item in CALIBRATION_IDS if item not in scores]
    if missing:
        raise ValueError(f"missing calibration results: {missing}")
    smoke = [float(scores[item]["normalized_wer_200"]) for item in CALIBRATION_IDS]
    medium = [float(scores[item]["normalized_wer_750"]) for item in CALIBRATION_IDS]
    rho = spearman_rank_correlation(smoke, medium)
    return {"ids": list(CALIBRATION_IDS), "metric": "primary_target_proxy_normalized_wer", "spearman_rho": rho, "minimum_rho": 0.7, "autoresearch_promotion_enabled": rho >= 0.7, "rule": "200-step ordering must not drive promotion unless rho >= 0.70."}
