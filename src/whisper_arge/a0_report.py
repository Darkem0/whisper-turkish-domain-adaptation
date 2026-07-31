from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from .hashing import sha256_file
from .manifests import read_jsonl
from .metrics import corpus_metrics
from .normalization import normalize_turkish


def _prediction_map(path: str | Path) -> tuple[dict[str, str], list[str]]:
    values: dict[str, str] = {}
    duplicates: list[str] = []
    for row in read_jsonl(path):
        sample_id = str(row["sample_id"])
        if sample_id in values:
            duplicates.append(sample_id)
        values[sample_id] = str(row["prediction"])
    return values, sorted(set(duplicates))


def _integrity(manifest: str | Path, predictions: str | Path, progress: str | Path) -> dict:
    rows = list(read_jsonl(manifest))
    prediction_map, prediction_duplicates = _prediction_map(predictions)
    ids = [str(row["sample_id"]) for row in rows]
    stable_keys = [
        (str(row.get("stable_source_id") or ""), str(row.get("degradation") or ""))
        if row.get("degradation")
        else (str(row.get("stable_source_id") or ""), "")
        for row in rows
    ]
    expected, actual = set(ids), set(prediction_map)
    p = json.loads(Path(progress).read_text(encoding="utf-8"))
    return {
        "expected_samples": len(rows),
        "actual_predictions": len(prediction_map),
        "missing_sample_id": sorted(expected - actual),
        "unexpected_sample_id": sorted(actual - expected),
        "duplicate_prediction_sample_id": prediction_duplicates,
        "duplicate_manifest_sample_id": sorted(
            key for key, count in Counter(ids).items() if count > 1
        ),
        "duplicate_stable_id": [
            {"stable_id": key[0], "degradation": key[1] or None}
            for key, count in Counter(stable_keys).items()
            if key[0] and count > 1
        ],
        "incomplete_batches": not bool(p.get("completed"))
        or int(p.get("next", -1)) != int(p.get("total", -2)),
        "prediction_sha256": sha256_file(predictions),
        "manifest_sha256": sha256_file(manifest),
        "wall_seconds_last_batch": p.get("wall_seconds_last_batch"),
        "peak_vram_bytes_last_batch": p.get("peak_vram_bytes_last_batch"),
    }


def _cvsp_style(manifest: str | Path, predictions: str | Path) -> dict:
    rows = list(read_jsonl(manifest))
    prediction_map, _ = _prediction_map(predictions)
    by_speaker: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_speaker[str(row["speaker_id"])].append(row)
    result = {}
    for speaker, items in sorted(by_speaker.items()):
        pairs = [(str(row["reference"]), prediction_map[str(row["sample_id"])]) for row in items]
        result[speaker] = corpus_metrics(pairs)
    aggregate = corpus_metrics(
        [(str(row["reference"]), prediction_map[str(row["sample_id"])]) for row in rows]
    )
    return {
        "per_speaker": result,
        "aggregate": aggregate,
        "hard_acceptance_gate": False,
        "disfluency_metrics": {
            "supported": False,
            "reason": "<disfluency> is an annotation placeholder without lexical filler identity",
        },
    }


def build_a0_report(output_root: str | Path) -> dict:
    root = Path(output_root)
    runs = {
        "mediaspeech_paired": (
            "data/materialized/mediaspeech_v2d/paired/mediaspeech_holdout_paired_v2d.jsonl",
            "runs/a0_v2d_full/mediaspeech_paired/predictions.jsonl",
            "runs/a0_v2d_full/mediaspeech_paired/progress.json",
            "runs/a0_v2d_full/mediaspeech_paired/metrics.json",
        ),
        "cv_scripted": (
            "data/materialized/hf_v2d/cv_scripted_test_v2d.jsonl",
            "runs/a0_v2d_full/cv_scripted/predictions.jsonl",
            "runs/a0_v2d_full/cv_scripted/progress.json",
            "runs/a0_v2d_full/cv_scripted/metrics.json",
        ),
        "fleurs": (
            "data/materialized/fleurs_tr_v2d/fleurs_tr_test_v2d.jsonl",
            "runs/a0_v2d_full/fleurs/predictions.jsonl",
            "runs/a0_v2d_full/fleurs/progress.json",
            "runs/a0_v2d_full/fleurs/metrics.json",
        ),
        "tsc_exploratory": (
            "data/materialized/tsc_v2a/tsc_full_v2a.jsonl",
            "runs/a0_v2d_full/tsc_exploratory/predictions.jsonl",
            "runs/a0_v2d_full/tsc_exploratory/progress.json",
            "runs/a0_v2d_full/tsc_exploratory/metrics.json",
        ),
        "cv_spontaneous": (
            "data/materialized/cv_spontaneous_v2c/cv_spontaneous_holdout_v2c.jsonl",
            "runs/a0_v2d_smoke/cv_spontaneous/predictions.jsonl",
            "runs/a0_v2d_smoke/cv_spontaneous/progress.json",
            "runs/a0_v2d_smoke/cv_spontaneous/metrics.json",
        ),
    }
    integrity = {name: _integrity(*values[:3]) for name, values in runs.items()}
    metrics = {
        name: json.loads(Path(values[3]).read_text(encoding="utf-8"))
        for name, values in runs.items()
    }
    media_rows = [
        row
        for row in read_jsonl(runs["mediaspeech_paired"][0])
        if row.get("degradation") == "clean"
    ]
    media_predictions, _ = _prediction_map(runs["mediaspeech_paired"][1])
    comparisons = []
    for row in sorted(media_rows, key=lambda item: str(item["stable_source_id"]))[:20]:
        prediction = media_predictions[str(row["sample_id"])]
        comparisons.append(
            {
                "stable_id": row["stable_source_id"],
                "reference": row["reference"],
                "raw_prediction": prediction,
                "normalized_prediction": normalize_turkish(prediction),
            }
        )
    root.mkdir(parents=True, exist_ok=True)
    comparison_path = root / "mediaspeech_normalization_comparison_20.jsonl"
    comparison_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in comparisons),
        encoding="utf-8",
    )
    worker_log = Path("runs/a0_v2d_full/worker/worker.stdout.log")
    worker_times = [
        float(value)
        for value in re.findall(
            r'"wall_seconds_last_batch"\s*:\s*([0-9.]+)',
            worker_log.read_text(encoding="utf-8"),
        )
    ]
    report = {
        "run": "A0 openai/whisper-large-v3-turbo base",
        "integrity": integrity,
        "metrics": metrics,
        "cv_spontaneous_style_probe": _cvsp_style(
            runs["cv_spontaneous"][0], runs["cv_spontaneous"][1]
        ),
        "tsc": {"use_for_acceptance": False, "label": "exploratory_only"},
        "normalization_comparison": {
            "rows": len(comparisons),
            "path": str(comparison_path),
            "sha256": sha256_file(comparison_path),
        },
        "runtime": {
            "full_worker_decode_seconds": sum(worker_times),
            "full_worker_batches": len(worker_times),
            "peak_vram_bytes": max(
                item["peak_vram_bytes_last_batch"] or 0 for item in integrity.values()
            ),
        },
    }
    report_path = root / "a0_baseline_report_v2d.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {
        "report": str(report_path),
        "report_sha256": sha256_file(report_path),
        "comparison": str(comparison_path),
        "comparison_sha256": sha256_file(comparison_path),
    }
