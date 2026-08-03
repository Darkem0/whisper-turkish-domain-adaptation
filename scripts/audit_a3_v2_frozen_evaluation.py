"""Read-only audit of completed A3_v2 frozen-evaluation artefacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from whisper_arge.acceptance_stats import _counts, _prediction_map
from whisper_arge.manifests import read_jsonl
from whisper_arge.metrics import pair_counts
from whisper_arge.normalization import normalize_turkish


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "A3_v2_frozen_evaluation"
REPORTS = ROOT / "reports"
CHECKPOINTS = ("step-050", "step-100", "step-150", "step-200")
TARGETS = ("mediaspeech_clean", "mediaspeech_phone", "mediaspeech_g711", "cv_scripted", "fleurs", "cv_spontaneous", "tsc_exploratory")
MANIFESTS = {
    "mediaspeech_clean": ("data/materialized/mediaspeech_v2d/paired/mediaspeech_holdout_paired_v2d.jsonl", "clean"),
    "mediaspeech_phone": ("data/materialized/mediaspeech_v2d/paired/mediaspeech_holdout_paired_v2d.jsonl", "phone_8khz"),
    "mediaspeech_g711": ("data/materialized/mediaspeech_v2d/paired/mediaspeech_holdout_paired_v2d.jsonl", "g711_mulaw"),
    "cv_scripted": ("data/materialized/hf_v2d/cv_scripted_test_v2d.jsonl", None),
    "fleurs": ("data/materialized/fleurs_tr_v2d/fleurs_tr_test_v2d.jsonl", None),
    "cv_spontaneous": ("data/materialized/cv_spontaneous_v2c/cv_spontaneous_holdout_v2c.jsonl", None),
    "tsc_exploratory": ("data/materialized/tsc_v2a/tsc_full_v2a.jsonl", None),
}
REFERENCES = {
    "A0": {
        "mediaspeech": ROOT / "runs/a0_v2d_full/mediaspeech_paired/predictions.jsonl",
        "cv_scripted": ROOT / "runs/a0_v2d_full/cv_scripted/predictions.jsonl",
        "fleurs": ROOT / "runs/a0_v2d_full/fleurs/predictions.jsonl",
        "cv_spontaneous": ROOT / "runs/a0_v2d_smoke/cv_spontaneous/predictions.jsonl",
        "tsc_exploratory": ROOT / "runs/a0_v2d_full/tsc_exploratory/predictions.jsonl",
    },
    "A2": {
        "mediaspeech": ROOT / "runs/A2_v2d_eval/mediaspeech_paired/predictions.jsonl",
        "cv_scripted": ROOT / "runs/A2_v2d_eval/cv_scripted/predictions.jsonl",
        "fleurs": ROOT / "runs/A2_v2d_eval/fleurs/predictions.jsonl",
        "cv_spontaneous": ROOT / "runs/A2_v2d_eval/cv_spontaneous/predictions.jsonl",
        "tsc_exploratory": ROOT / "runs/A2_v2d_eval/tsc_exploratory/predictions.jsonl",
    },
}
SEED, REPLICATES = 20260730, 1000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rows_for(target: str) -> list[dict]:
    path, degradation = MANIFESTS[target]
    rows = list(read_jsonl(ROOT / path))
    return rows if degradation is None else [row for row in rows if row.get("degradation") == degradation]


def char_counts(rows: list[dict], predictions: dict[str, str]) -> tuple[np.ndarray, np.ndarray]:
    errors, chars = [], []
    for row in rows:
        value = pair_counts(normalize_turkish(str(row["reference"])), normalize_turkish(predictions[str(row["sample_id"])]))
        errors.append(value.char_errors)
        chars.append(value.reference_chars)
    return np.asarray(errors), np.asarray(chars)


def ci(reference: tuple[np.ndarray, np.ndarray], candidate: tuple[np.ndarray, np.ndarray], label: str) -> dict:
    baseline, words = reference
    value, candidate_words = candidate
    if not np.array_equal(words, candidate_words):
        raise ValueError("candidate reference counts do not align")
    rng = np.random.default_rng(SEED)
    draws = rng.integers(0, len(words), size=(REPLICATES, len(words)))
    samples = (value[draws].sum(axis=1) - baseline[draws].sum(axis=1)) / words[draws].sum(axis=1)
    point = float((value.sum() - baseline.sum()) / words.sum())
    return {"point": point, "lower": float(np.quantile(samples, .025)), "upper": float(np.quantile(samples, .975)), "width": float(np.quantile(samples, .975) - np.quantile(samples, .025)), "replicates": REPLICATES, "seed": SEED, "resampling": "paired_stable_id_with_replacement", "estimator": f"paired_corpus_normalized_{label}_delta"}


def check_target(checkpoint: str, target: str, rows: list[dict]) -> tuple[dict, dict[str, str]]:
    root = RUN / checkpoint / target
    required = ("predictions.jsonl", "metrics.json", "config.resolved.json", "artifact_lock.json")
    problems = [name for name in required if not (root / name).is_file()]
    lock = load(root / "artifact_lock.json") if not problems else {}
    for name in required[:-1]:
        if name in lock and sha(root / name) != lock[name]:
            problems.append(f"hash mismatch: {name}")
    predictions = _prediction_map(root / "predictions.jsonl") if not problems else {}
    expected = {str(row["sample_id"]) for row in rows}
    if set(predictions) != expected:
        problems.append("prediction sample_id coverage mismatch")
    metrics = load(root / "metrics.json") if not problems else {}
    if metrics.get("samples") != len(rows):
        problems.append("metrics sample count mismatch")
    if metrics.get("prediction_sha256") != sha(root / "predictions.jsonl"):
        problems.append("metrics prediction SHA-256 mismatch")
    config = load(root / "config.resolved.json") if not problems else {}
    if config.get("checkpoint") != checkpoint or config.get("dataset") != target:
        problems.append("resolved config identity mismatch")
    return {"checkpoint": checkpoint, "dataset": target, "samples": len(rows), "prediction_sha256": metrics.get("prediction_sha256"), "status": "PASSED" if not problems else "FAILED", "problems": problems}, predictions


def proxy(rows: dict[str, list[dict]], reference: dict[str, str], candidate: dict[str, dict[str, str]]) -> dict:
    weights = {"mediaspeech_clean": 0.50, "mediaspeech_phone": 0.25, "mediaspeech_g711": 0.25}
    point = 0.0
    samples = np.zeros(REPLICATES)
    rng = np.random.default_rng(SEED)
    for name, weight in weights.items():
        base, words = _counts(rows[name], reference)
        value, _ = _counts(rows[name], candidate[name])
        point += weight * (value.sum() - base.sum()) / words.sum()
        draws = rng.integers(0, len(words), size=(REPLICATES, len(words)))
        samples += weight * ((value[draws].sum(axis=1) - base[draws].sum(axis=1)) / words[draws].sum(axis=1))
    return {"point": float(point), "lower": float(np.quantile(samples, .025)), "upper": float(np.quantile(samples, .975)), "replicates": REPLICATES, "seed": SEED, "estimator": "weighted_media_normalized_wer_proxy_delta"}


def markdown_table(rows: list[list[str]]) -> str:
    return "\n".join("| " + " | ".join(row) + " |" for row in rows)


def main() -> int:
    progress = load(RUN / "evaluation_progress.json")
    integrity, all_predictions, manifests = [], {}, {target: rows_for(target) for target in TARGETS}
    for checkpoint in CHECKPOINTS:
        all_predictions[checkpoint] = {}
        for target in TARGETS:
            record, predictions = check_target(checkpoint, target, manifests[target])
            integrity.append(record)
            all_predictions[checkpoint][target] = predictions
    complete = progress.get("status") == "COMPLETED" and progress.get("completed_targets") == 28
    integrity_ok = complete and all(item["status"] == "PASSED" for item in integrity)
    comparisons, gate_results, paired = {}, {}, {}
    refs = {name: {key: _prediction_map(path) for key, path in paths.items()} for name, paths in REFERENCES.items()}
    for checkpoint in CHECKPOINTS:
        per_target, per_ci = {}, {}
        for target in TARGETS:
            reference_key = "mediaspeech" if target.startswith("mediaspeech") else target
            candidate = all_predictions[checkpoint][target]
            for baseline_name in ("A0", "A2"):
                baseline = refs[baseline_name][reference_key]
                if set(baseline) != set(candidate):
                    per_ci.setdefault(target, {})[baseline_name] = {"status": "UNAVAILABLE_SAMPLE_ID_MISMATCH"}
                    continue
                wer = ci(_counts(manifests[target], baseline), _counts(manifests[target], candidate), "wer")
                cer = ci(char_counts(manifests[target], baseline), char_counts(manifests[target], candidate), "cer")
                per_ci.setdefault(target, {})[baseline_name] = {"normalized_wer_delta": wer, "normalized_cer_delta": cer}
            metrics = load(RUN / checkpoint / target / "metrics.json")
            per_target[target] = {key: metrics[key] for key in ("samples", "normalized_wer", "normalized_cer", "raw_wer", "raw_cer", "prediction_sha256")}
        a0_proxy = proxy(manifests, refs["A0"]["mediaspeech"], {sample: all_predictions[checkpoint][sample] for sample in ("mediaspeech_clean", "mediaspeech_phone", "mediaspeech_g711")})
        gates = {
            "domain_robustness": a0_proxy["point"] <= -0.010 and a0_proxy["upper"] < 0,
            "fleurs_guardrail": per_ci["fleurs"]["A0"]["normalized_wer_delta"]["point"] <= .005,
            "cv_scripted_guardrail": per_ci["cv_scripted"]["A0"]["normalized_wer_delta"]["point"] <= .005,
            "hallucination": "MISSING_ARTIFACT",
            "repetition": "MISSING_ARTIFACT",
            "reproducibility": "FAILED_1_OF_3_SEEDS",
        }
        failures = [name for name, value in gates.items() if value is not True]
        status = "INELIGIBLE_GATE_FAILURE" if failures else "ELIGIBLE_FOR_PROMOTION_REVIEW"
        comparisons[checkpoint] = {"metrics": per_target, "robustness_proxy_vs_a0": a0_proxy, "paired_deltas": per_ci}
        gate_results[checkpoint] = {"status": status, "gates": gates, "failed_gates": failures, "report_only": ["cv_spontaneous", "tsc_exploratory"]}
        paired[checkpoint] = per_ci
    terminal = "BLOCKED_A3_V2_FROZEN_EVALUATION" if not integrity_ok else ("READY_FOR_A3_V2_PROMOTION_REVIEW" if any(result["status"] == "ELIGIBLE_FOR_PROMOTION_REVIEW" for result in gate_results.values()) else "A3_V2_NO_PROMOTABLE_CHECKPOINT")
    root_lock = {str(path.relative_to(RUN)).replace("\\", "/"): sha(path) for path in RUN.rglob("*.json") if path.name != "artifact_lock.json"}
    dump(RUN / "checkpoint_comparison.json", comparisons)
    dump(RUN / "artifact_lock.json", root_lock)
    dump(REPORTS / "a3_v2_frozen_evaluation_integrity.json", {"progress": progress, "integrity_ok": integrity_ok, "targets": integrity})
    table = [["Checkpoint", "Status", "Failed gates", "Proxy delta vs A0"]] + [[checkpoint, value["status"], ", ".join(value["failed_gates"]), f"{comparisons[checkpoint]['robustness_proxy_vs_a0']['point']:.5f}"] for checkpoint, value in gate_results.items()]
    summary = f"# A3_v2 frozen evaluation summary\n\nTerminal status: `{terminal}`. No production promotion was performed.\n\n" + markdown_table(table) + "\n\nCV Spontaneous is report-only; TSC is exploratory and neither was used as a promotion gate.\n"
    (REPORTS / "a3_v2_frozen_evaluation_summary.md").write_text(summary, encoding="utf-8")
    (REPORTS / "a3_v2_checkpoint_comparison.md").write_text("# A3_v2 checkpoint comparison\n\n" + json.dumps(comparisons, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (REPORTS / "a3_v2_promotion_gate_results.md").write_text("# A3_v2 promotion gates\n\n" + json.dumps(gate_results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (REPORTS / "a3_v2_paired_ci_results.md").write_text("# A3_v2 paired bootstrap 95% confidence intervals\n\n" + json.dumps(paired, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (REPORTS / "a3_v2_frozen_evaluation_integrity.md").write_text("# A3_v2 frozen evaluation integrity\n\n" + json.dumps({"progress": progress, "integrity_ok": integrity_ok, "targets": integrity}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (REPORTS / "next_executable_stage.md").write_text(f"# Next executable stage\n\n`{terminal}`\n\nNo checkpoint was promoted by this audit.\n", encoding="utf-8")
    return 0 if integrity_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
