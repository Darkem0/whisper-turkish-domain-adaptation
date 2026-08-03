from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .acceptance_stats import _counts, _prediction_map, paired_corpus_delta_bootstrap
from .baseline_resolver import resolve_a0_baseline_predictions
from .evaluation_v2 import evaluate_v2
from .hashing import sha256_file
from .manifests import read_jsonl


LAYOUTS = {
    "mediaspeech_paired": "data/materialized/mediaspeech_v2d/paired/mediaspeech_holdout_paired_v2d.jsonl",
    "cv_scripted": "data/materialized/hf_v2d/cv_scripted_test_v2d.jsonl",
    "fleurs": "data/materialized/fleurs_tr_v2d/fleurs_tr_test_v2d.jsonl",
    "cv_spontaneous": "data/materialized/cv_spontaneous_v2c/cv_spontaneous_holdout_v2c.jsonl",
    "tsc_exploratory": "data/materialized/tsc_v2a/tsc_full_v2a.jsonl",
}


def dry_run_candidate_v2d(candidate_root: str | Path) -> dict:
    candidate_root = Path(candidate_root)
    layouts = {name: Path(path) for name, path in LAYOUTS.items()}
    baseline = resolve_a0_baseline_predictions(layouts, project_root=".")
    candidate = {}
    for name, manifest in layouts.items():
        expected = {str(row["sample_id"]) for row in read_jsonl(manifest)}
        path = candidate_root / name / "predictions.jsonl"
        ids = [str(row["sample_id"]) for row in read_jsonl(path)]
        actual = set(ids)
        candidate[name] = {
            "path": str(path),
            "samples": len(ids),
            "missing_stable_id": len(expected - actual),
            "duplicate_stable_id": len(ids) - len(actual),
            "unexpected_stable_id": len(actual - expected),
            "status": "pass" if actual == expected and len(ids) == len(actual) else "fail",
        }
    if any(value["status"] != "pass" for value in candidate.values()):
        raise ValueError("candidate prediction integrity failure")
    return {
        "status": "pass",
        "baseline_resolution": baseline,
        "candidate_prediction_integrity": candidate,
    }


def _paired_model_delta(
    rows: list[dict], baseline: dict[str, str], candidate: dict[str, str], *, seed: int
) -> dict:
    baseline_errors, words = _counts(rows, baseline)
    candidate_errors, candidate_words = _counts(rows, candidate)
    if not np.array_equal(words, candidate_words):
        raise ValueError("reference word counts do not align")
    return paired_corpus_delta_bootstrap(
        baseline_errors, candidate_errors, words, replicates=10000, seed=seed
    )


def _proxy_delta(
    grouped: dict[str, list[dict]],
    baseline: dict[str, str],
    candidate: dict[str, str],
    *,
    seed: int,
) -> dict:
    names = ("clean", "phone_8khz", "g711_mulaw")
    arrays = {
        name: (_counts(grouped[name], baseline), _counts(grouped[name], candidate))
        for name in names
    }
    total = len(grouped["clean"])
    if not all(len(grouped[name]) == total for name in names):
        raise ValueError("MediaSpeech paired variants have unequal row counts")
    rng = np.random.default_rng(seed)
    samples = np.empty(10000, dtype=np.float64)
    weights = {"clean": 0.50, "phone_8khz": 0.25, "g711_mulaw": 0.25}
    base_point = 0.0
    candidate_point = 0.0
    for name in names:
        (base_errors, words), (candidate_errors, candidate_words) = arrays[name]
        if not np.array_equal(words, candidate_words):
            raise ValueError("MediaSpeech pair reference mismatch")
        base_point += weights[name] * base_errors.sum() / words.sum()
        candidate_point += weights[name] * candidate_errors.sum() / words.sum()
    for index in range(len(samples)):
        drawn = rng.integers(0, total, size=total, endpoint=False)
        base_value = 0.0
        candidate_value = 0.0
        for name in names:
            (base_errors, words), (candidate_errors, _) = arrays[name]
            denominator = words[drawn].sum()
            base_value += weights[name] * base_errors[drawn].sum() / denominator
            candidate_value += weights[name] * candidate_errors[drawn].sum() / denominator
        samples[index] = candidate_value - base_value
    return {
        "baseline_proxy_score": float(base_point),
        "candidate_proxy_score": float(candidate_point),
        "point": float(candidate_point - base_point),
        "lower": float(np.quantile(samples, 0.025, method="linear")),
        "upper": float(np.quantile(samples, 0.975, method="linear")),
        "replicates": 10000,
        "seed": seed,
        "resampling": "paired_stable_id_with_replacement",
        "estimator": "weighted_media_normalized_wer_proxy_delta",
    }


def evaluate_candidate_v2d(
    candidate_root: str | Path,
    *,
    baseline_root: str | Path | None = None,
    seed: int = 20260730,
) -> dict:
    candidate_root = Path(candidate_root)
    layouts = LAYOUTS
    resolved_baseline = resolve_a0_baseline_predictions(
        {name: Path(path) for name, path in layouts.items()}, project_root="."
    )
    if baseline_root is not None:
        raise ValueError(
            "baseline_root override is prohibited; resolve immutable A0 artifacts instead"
        )
    per_domain = {}
    deltas = {}
    loaded = {}
    for name, manifest in layouts.items():
        candidate_predictions_path = candidate_root / name / "predictions.jsonl"
        baseline_predictions_path = Path(resolved_baseline["predictions"][name]["path"])
        rows = list(read_jsonl(manifest))
        baseline = _prediction_map(baseline_predictions_path)
        candidate = _prediction_map(candidate_predictions_path)
        expected = {str(row["sample_id"]) for row in rows}
        if set(baseline) != expected or set(candidate) != expected:
            raise ValueError(f"prediction coverage mismatch for {name}")
        per_domain[name] = evaluate_v2(manifest, candidate_predictions_path)
        deltas[name] = _paired_model_delta(rows, baseline, candidate, seed=seed)
        loaded[name] = (rows, baseline, candidate)
    media_rows, media_base, media_candidate = loaded["mediaspeech_paired"]
    grouped = {
        name: sorted(
            [row for row in media_rows if row.get("degradation") == name],
            key=lambda row: str(row["stable_source_id"]),
        )
        for name in ("clean", "phone_8khz", "g711_mulaw")
    }
    media_variant_deltas = {
        name: _paired_model_delta(grouped[name], media_base, media_candidate, seed=seed)
        for name in grouped
    }
    report = {
        "schema_version": 1,
        "status": "complete",
        "candidate_root": str(candidate_root),
        "baseline_resolution": resolved_baseline,
        "evaluation_policy": {
            "cv_spontaneous": "report_only_style_probe",
            "tsc": "exploratory_only_not_acceptance",
            "raw_wer": "diagnostic_only",
        },
        "domain_metrics": per_domain,
        "paired_normalized_wer_delta_vs_a0": deltas,
        "mediaspeech_variant_paired_normalized_wer_delta_vs_a0": media_variant_deltas,
        "robustness_proxy": _proxy_delta(grouped, media_base, media_candidate, seed=seed),
        "prediction_sha256": {
            name: sha256_file(candidate_root / name / "predictions.jsonl") for name in layouts
        },
    }
    condition = candidate_root.name.split("_", 1)[0].lower()
    output = candidate_root / f"{condition}_evaluation_v2d.json"
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {**report, "report": str(output), "report_sha256": sha256_file(output)}
