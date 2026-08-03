"""Read-only integrity audit for completed A5 frozen evaluation."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "A5_v2_frozen_evaluation"
TRAIN = ROOT / "runs" / "A5_v2_fresh_base_200" / "checkpoints"
REPORTS = ROOT / "reports"
CHECKPOINTS = ("step-050", "step-100", "step-150", "step-200")
TARGETS = (
    "mediaspeech_clean",
    "mediaspeech_phone",
    "mediaspeech_g711",
    "cv_scripted",
    "fleurs",
    "cv_spontaneous",
    "tsc_exploratory",
)
SOURCES = {
    "mediaspeech_clean": "data/materialized/mediaspeech_v2d/paired/mediaspeech_holdout_paired_v2d.jsonl",
    "mediaspeech_phone": "data/materialized/mediaspeech_v2d/paired/mediaspeech_holdout_paired_v2d.jsonl",
    "mediaspeech_g711": "data/materialized/mediaspeech_v2d/paired/mediaspeech_holdout_paired_v2d.jsonl",
    "cv_scripted": "data/materialized/hf_v2d/cv_scripted_test_v2d.jsonl",
    "fleurs": "data/materialized/fleurs_tr_v2d/fleurs_tr_test_v2d.jsonl",
    "cv_spontaneous": "data/materialized/cv_spontaneous_v2c/cv_spontaneous_holdout_v2c.jsonl",
    "tsc_exploratory": "data/materialized/tsc_v2a/tsc_full_v2a.jsonl",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    contract_sha = sha256(ROOT / "contracts" / "A5_v2_eval_contract.yaml")
    decode = {
        "language": "tr",
        "task": "transcribe",
        "num_beams": 5,
        "do_sample": False,
        "condition_on_prev_tokens": False,
        "max_new_tokens": 444,
    }
    eval_config_sha = hashlib.sha256(json.dumps(decode, sort_keys=True).encode("utf-8")).hexdigest()
    source_sha = {name: sha256(ROOT / path) for name, path in SOURCES.items()}
    rows, problems = [], []
    for checkpoint in CHECKPOINTS:
        checkpoint_lock = read_json(TRAIN / checkpoint / "checkpoint_lock.json")
        expected_adapter = checkpoint_lock["files_sha256"]["adapter/adapter_model.safetensors"]
        for target in TARGETS:
            directory = RUN / checkpoint / target
            required = [
                directory / name
                for name in (
                    "predictions.jsonl",
                    "metrics.json",
                    "config.resolved.json",
                    "artifact_lock.json",
                )
            ]
            missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
            if missing:
                problems.extend(missing)
                continue
            predictions, metrics, config, lock = required
            prediction_sha = sha256(predictions)
            metric = read_json(metrics)
            resolved = read_json(config)
            artifact_lock = read_json(lock)
            count = sum(1 for line in predictions.read_text(encoding="utf-8").splitlines() if line)
            checks = {
                "sample_count": metric.get("samples") == count,
                "metrics_prediction_hash": metric.get("prediction_sha256") == prediction_sha,
                "lock_prediction_hash": artifact_lock.get("predictions.jsonl") == prediction_sha,
                "checkpoint": resolved.get("checkpoint") == checkpoint,
                "target": resolved.get("dataset") == target,
                "adapter_hash": resolved.get("adapter_sha256") == expected_adapter,
                "locked_decode_hash": resolved.get("eval_config_sha256") == eval_config_sha,
                "source_manifest_hash": resolved.get("source_manifest_sha256")
                == source_sha[target],
            }
            failed = [name for name, passed in checks.items() if not passed]
            if failed:
                problems.append(f"{directory.relative_to(ROOT)}: {', '.join(failed)}")
            rows.append({"checkpoint": checkpoint, "dataset": target, **metric})
    status = "PASSED" if len(rows) == 28 and not problems else "FAILED"
    REPORTS.mkdir(exist_ok=True)
    with (REPORTS / "a5_v2_checkpoint_dataset_metrics.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "checkpoint",
                "dataset",
                "samples",
                "normalized_wer",
                "normalized_cer",
                "raw_wer",
                "raw_cer",
                "prediction_sha256",
            ],
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "status": status,
        "canonical_progress": "runs/A5_v2_frozen_evaluation/evaluation_progress.json",
        "planned_targets": 28,
        "verified_targets": len(rows),
        "eval_contract_sha256": contract_sha,
        "locked_decode_sha256": eval_config_sha,
        "checks": [
            "required files",
            "sample counts",
            "prediction hashes",
            "checkpoint adapter hashes",
            "locked decode hash",
            "source manifest hash",
        ],
        "problems": problems,
    }
    (REPORTS / "a5_v2_frozen_evaluation_integrity_audit.md").write_text(
        "# A5_v2 frozen-evaluation integrity audit\n\n```json\n"
        + json.dumps(report, indent=2)
        + "\n```\n",
        encoding="utf-8",
    )
    (REPORTS / "a5_v2_frozen_evaluation_final_report.md").write_text(
        "# A5_v2 frozen evaluation final report\n\n"
        f"Integrity: `{status}`. Canonical evaluation progress is `COMPLETED`, with {len(rows)}/28 targets verified. "
        "A5 remains diagnostic-only: no production promotion is implied. CV Spontaneous is report-only and TSC is exploratory.\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": status, "targets": len(rows), "problems": problems}))


if __name__ == "__main__":
    main()
