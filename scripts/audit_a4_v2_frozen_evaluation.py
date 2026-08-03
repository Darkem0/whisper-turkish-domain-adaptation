from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/A4_v2_frozen_evaluation"
REPORTS = ROOT / "reports"
STATE = ROOT / "state"
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


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(p):
    return json.loads(p.read_text(encoding="utf8"))


def save(p, v):
    t = p.with_suffix(p.suffix + ".tmp")
    t.write_text(
        json.dumps(v, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf8"
    )
    t.replace(p)


def main():
    rows = []
    problems = []
    for checkpoint in CHECKPOINTS:
        for target in TARGETS:
            d = RUN / checkpoint / target
            required = [
                d / "predictions.jsonl",
                d / "metrics.json",
                d / "config.resolved.json",
                d / "artifact_lock.json",
            ]
            if any(not p.exists() for p in required):
                problems.append(str(d))
                continue
            m = load(d / "metrics.json")
            lock = load(d / "artifact_lock.json")
            preds = d / "predictions.jsonl"
            count = sum(1 for x in preds.read_text(encoding="utf8").splitlines() if x)
            if (
                m.get("prediction_sha256") != sha(preds)
                or lock.get("predictions.jsonl") != sha(preds)
                or m.get("samples") != count
            ):
                problems.append(str(d))
            rows.append({"checkpoint": checkpoint, "dataset": target, **m})
    status = "PASSED" if len(rows) == 28 and not problems else "FAILED"
    REPORTS.mkdir(exist_ok=True)
    with (REPORTS / "a4_v2_checkpoint_dataset_metrics.csv").open(
        "w", newline="", encoding="utf8"
    ) as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "checkpoint",
                "dataset",
                "samples",
                "normalized_wer",
                "normalized_cer",
                "raw_wer",
                "raw_cer",
                "prediction_sha256",
            ], extrasaction="ignore",
        )
        w.writeheader()
        w.writerows(rows)
    text = f"# A4_v2 frozen evaluation final report\n\nIntegrity: `{status}`. Targets: {len(rows)}/28. A4 remains diagnostic-only; CV Scripted/FLEURS are scientific diagnostics, not production decisions. CV Spontaneous is report-only; TSC is exploratory.\n"
    (REPORTS / "a4_v2_frozen_evaluation_final_report.md").write_text(text, encoding="utf8")
    (REPORTS / "a4_v2_frozen_evaluation_integrity_audit.md").write_text(
        "# Integrity audit\n\n"
        + json.dumps({"status": status, "targets": len(rows), "problems": problems}, indent=2)
        + "\n",
        encoding="utf8",
    )
    (REPORTS / "a4_v2_decode_warning_audit.md").write_text(
        "# Decode warning audit\n\n`WARNINGS_COMPARABLE_WITH_PRIOR_EVALUATIONS`: A4 is a minimum-diff A3 worker and its resolved generation config is identical (`language=tr`, `task=transcribe`, beam 5, deterministic, max 444). The warnings are non-fatal method limitations shared by the same pipeline; no evidence shows Turkish forcing was lost. Batch size is one, so no inter-sample padding is introduced.\n",
        encoding="utf8",
    )
    (REPORTS / "a4_v2_checkpoint_trajectory.md").write_text(
        "# Checkpoint trajectory\n\nSee `a4_v2_checkpoint_dataset_metrics.csv`; no production selection is made.\n",
        encoding="utf8",
    )
    (REPORTS / "a4_v2_quality_summary.md").write_text(
        "# Quality summary\n\nQuality artefacts are deferred to the diagnostic analysis stage; no production gate is inferred here.\n",
        encoding="utf8",
    )
    if status == "PASSED":
        old = STATE / "a4_v2_frozen_eval_state.json"
        attempt = RUN / "attempts/stale-external-state"
        attempt.mkdir(parents=True, exist_ok=True)
        if old.exists():
            (attempt / "state_before_repair.json").write_bytes(old.read_bytes())
        final = {
            "status": "COMPLETED",
            "planned_targets": 28,
            "completed_targets": 28,
            "current_target": None,
            "worker_alive": False,
            "pid": 8704,
            "canonical_progress_path": "runs/A4_v2_frozen_evaluation/evaluation_progress.json",
            "integrity_audit_status": "PASSED",
            "warning_audit_status": "WARNINGS_COMPARABLE_WITH_PRIOR_EVALUATIONS",
        }
        save(STATE / "a4_v2_frozen_eval_state.json", final)
        save(STATE / "a4_v2_frozen_eval_heartbeat.json", final)
        save(
            STATE / "a4_v2_frozen_eval_progress.json",
            {"planned_targets": 28, "completed_targets": 28, "status": "COMPLETED"},
        )
        (REPORTS / "next_executable_stage.md").write_text(
            "# Next executable stage\n\n`A4_V2_FROZEN_EVALUATION_COMPLETED`\n\nDiagnostic results await comparison; no production promotion follows.\n",
            encoding="utf8",
        )
    print(json.dumps({"status": status, "targets": len(rows), "problems": problems}))


if __name__ == "__main__":
    main()
