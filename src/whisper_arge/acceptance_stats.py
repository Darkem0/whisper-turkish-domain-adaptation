from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .hashing import sha256_file
from .manifests import read_jsonl
from .metrics import pair_counts
from .normalization import normalize_turkish


def _prediction_map(path: str | Path) -> dict[str, str]:
    return {str(row["sample_id"]): str(row["prediction"]) for row in read_jsonl(path)}


def _counts(rows: list[dict], predictions: dict[str, str]) -> tuple[np.ndarray, np.ndarray]:
    errors, words = [], []
    for row in rows:
        counts = pair_counts(
            normalize_turkish(str(row["reference"])),
            normalize_turkish(predictions[str(row["sample_id"])]),
        )
        errors.append(counts.word_errors)
        words.append(counts.reference_words)
    return np.asarray(errors, dtype=np.int64), np.asarray(words, dtype=np.int64)


def _percentile(values: np.ndarray, probability: float) -> float:
    return float(np.quantile(values, probability, method="linear"))


def utterance_corpus_ratio_bootstrap(
    errors: np.ndarray, words: np.ndarray, *, replicates: int, seed: int
) -> dict:
    if len(errors) != len(words) or not len(errors):
        raise ValueError("nonempty, aligned corpus counts are required")
    rng = np.random.default_rng(seed)
    samples = np.empty(replicates, dtype=np.float64)
    for index in range(replicates):
        drawn = rng.integers(0, len(errors), size=len(errors), endpoint=False)
        samples[index] = errors[drawn].sum() / words[drawn].sum()
    point = float(errors.sum() / words.sum())
    return {
        "point": point,
        "lower": _percentile(samples, 0.025),
        "upper": _percentile(samples, 0.975),
        "width": _percentile(samples, 0.975) - _percentile(samples, 0.025),
        "replicates": replicates,
        "seed": seed,
        "resampling": "utterance_with_replacement",
        "estimator": "corpus_error_sum_over_corpus_reference_word_sum",
    }


def paired_corpus_delta_bootstrap(
    clean_errors: np.ndarray,
    variant_errors: np.ndarray,
    words: np.ndarray,
    *,
    replicates: int,
    seed: int,
) -> dict:
    if not (len(clean_errors) == len(variant_errors) == len(words)) or not len(words):
        raise ValueError("aligned nonempty pair counts are required")
    rng = np.random.default_rng(seed)
    samples = np.empty(replicates, dtype=np.float64)
    for index in range(replicates):
        drawn = rng.integers(0, len(words), size=len(words), endpoint=False)
        denominator = words[drawn].sum()
        samples[index] = (
            variant_errors[drawn].sum() / denominator - clean_errors[drawn].sum() / denominator
        )
    point = float(variant_errors.sum() / words.sum() - clean_errors.sum() / words.sum())
    return {
        "point": point,
        "lower": _percentile(samples, 0.025),
        "upper": _percentile(samples, 0.975),
        "width": _percentile(samples, 0.975) - _percentile(samples, 0.025),
        "replicates": replicates,
        "seed": seed,
        "resampling": "paired_stable_id_with_replacement",
        "estimator": "paired_corpus_normalized_wer_delta",
    }


def audit_acceptance_statistics(
    output: str | Path, *, replicates: int = 10000, seed: int = 20260730
) -> dict:
    if replicates < 10000:
        raise ValueError("acceptance audit requires at least 10000 replicates")
    media_manifest = list(
        read_jsonl("data/materialized/mediaspeech_v2d/paired/mediaspeech_holdout_paired_v2d.jsonl")
    )
    media_predictions = _prediction_map("runs/a0_v2d_full/mediaspeech_paired/predictions.jsonl")
    grouped = {
        name: sorted(
            [row for row in media_manifest if row.get("degradation") == name],
            key=lambda row: str(row["stable_source_id"]),
        )
        for name in ("clean", "phone_8khz", "g711_mulaw")
    }
    stable_sets = {
        name: [str(row["stable_source_id"]) for row in rows] for name, rows in grouped.items()
    }
    if not (stable_sets["clean"] == stable_sets["phone_8khz"] == stable_sets["g711_mulaw"]):
        raise ValueError("MediaSpeech paired stable_id alignment failure")
    media_counts = {name: _counts(rows, media_predictions) for name, rows in grouped.items()}
    clean_errors, words = media_counts["clean"]
    paired = {
        name: paired_corpus_delta_bootstrap(
            clean_errors, media_counts[name][0], words, replicates=replicates, seed=seed
        )
        for name in ("phone_8khz", "g711_mulaw")
    }
    ratios = {
        name: utterance_corpus_ratio_bootstrap(
            *media_counts[name], replicates=replicates, seed=seed
        )
        for name in media_counts
    }
    diagnostics = {}
    for name, manifest, predictions in (
        (
            "cv_scripted",
            "data/materialized/hf_v2d/cv_scripted_test_v2d.jsonl",
            "runs/a0_v2d_full/cv_scripted/predictions.jsonl",
        ),
        (
            "fleurs",
            "data/materialized/fleurs_tr_v2d/fleurs_tr_test_v2d.jsonl",
            "runs/a0_v2d_full/fleurs/predictions.jsonl",
        ),
    ):
        diagnostics[name] = utterance_corpus_ratio_bootstrap(
            *_counts(list(read_jsonl(manifest)), _prediction_map(predictions)),
            replicates=replicates,
            seed=seed,
        )
    proxy = (
        0.50 * ratios["clean"]["point"]
        + 0.25 * ratios["phone_8khz"]["point"]
        + 0.25 * ratios["g711_mulaw"]["point"]
    )
    report = {
        "status": "pass",
        "replicates": replicates,
        "seed": seed,
        "media_stable_id_count": len(stable_sets["clean"]),
        "media_normalized_wer": ratios,
        "paired_normalized_wer_delta": paired,
        "robustness_proxy_score": proxy,
        "cv_scripted_bootstrap_diagnostics": diagnostics["cv_scripted"],
        "fleurs_bootstrap_diagnostics": diagnostics["fleurs"],
        "raw_wer": "diagnostic_only_not_used_for_acceptance",
    }
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {**report, "report": str(path), "report_sha256": sha256_file(path)}
