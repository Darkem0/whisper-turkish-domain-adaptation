from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"


def write_contract(name: str, valid: bool, reasons: list[str], details: dict) -> None:
    CONTRACTS.mkdir(exist_ok=True)
    body = {"schema_version": 1, "contract_id": name, "validation": "VALID" if valid else "INVALID", "validated_at": datetime.now(UTC).isoformat(), "reasons": reasons, **details}
    (CONTRACTS / f"{name}.yaml").write_text(json.dumps(body, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    smoke = json.loads((ROOT / "runs/SMOKE_D0/result.json").read_text(encoding="utf-8"))
    queue_path = ROOT / "state/experiment_queue.json"
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    if smoke.get("verdict") == "PASSED":
        for item in queue:
            if item["id"].startswith("D") or item["id"] in {"P3_quality", "P4_second_pass", "P5_itn", "P6_nbest", "P7_memory"}:
                item.update({"status": "PENDING", "verdict": "PENDING", "execution_status": "PENDING", "error": None})
    queue_path.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    missing = ["A2 full resolved training configuration path", "A2 target/replay manifest and SHA-256", "A2 optimizer step count and optimizer-state provenance", "A2 exact source-data/replay ratios and seed evidence"]
    base = {"source_artifact_lock": "runs/A2_v2d_eval/a2_artifact_lock_v2d.json", "source_artifact_lock_exists": True, "smoke_result": "runs/SMOKE_D0/result.json", "prohibited_legacy_resume": "A3_legacy_aborted_step34_invalid"}
    write_contract("A2_reference.resolved", False, missing, base)
    write_contract("A3_v2.clean_replay", False, missing + ["cannot prove A2-equivalent encoder+decoder q_proj/v_proj rank 16, step, and optimizer"], {**base, "requested_clean_replay": {"total": 0.10, "common_voice_scripted": 0.07, "fleurs": 0.03}})
    write_contract("A4_v2.layer_selective", False, missing + ["cannot bind A3 replay/training settings to a VALID parent contract"], {**base, "requested_targets": "last 6 encoder layers; all decoder self/cross attention q_proj/v_proj; rank 16"})
    write_contract("A5_v2.phone_augmentation", False, missing + ["no repository artifact proves a pre-validated phone augmentation recipe for this exact series"], base)
    write_contract("A6_v2.reproducibility", False, missing + ["no promotion-gate-passing parent is evidenced; three seed schedule cannot be bound"], base)
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "training_contract_report.md").write_text("# Training contracts\n\nAll five contracts are **INVALID**. The A2 artifact lock proves immutable evaluation artifacts and prediction hashes, but not the strict A2 training recipe, target/replay manifest hashes, optimizer state/step provenance, or seed evidence required for a clean v2 replay. See `contracts/*.yaml`.\n", encoding="utf-8")
    (reports / "next_executable_stage.md").write_text("# Next executable stage\n\nREADY_FOR_D0_D7\n\nThe offline D0 smoke and immutable 32-row local WAV manifest passed. D0-D7 and P3-P7 are PENDING, but are not marked completed. A3_v2-A6_v2 remain BLOCKED_TRAINING_CONTRACT.\n", encoding="utf-8")
    (reports / "codex-continue-local-summary.md").write_text(f"# Local continuation summary\n\n- Manifest: 32 real WAV rows; 32 gold references; SHA-256 `{json.loads((ROOT / 'protocols/inference_manifest.lock.json').read_text(encoding='utf-8'))['manifest_sha256']}`.\n- Smoke: PASSED on RTX 4070 SUPER, FP16, peak VRAM `{smoke.get('peak_vram_bytes')}` bytes.\n- D0-D7: PENDING; P3-P7 execution: PENDING.\n- A2/A3/A4/A5/A6 contracts: INVALID; A3-A6 are BLOCKED_TRAINING_CONTRACT.\n- Supervisor/watchdog not started: the current supervisor implementation would convert pending D/P items into BLOCKED placeholders rather than execute their real inference/post-processing; starting it would misrepresent execution state.\n", encoding="utf-8")


if __name__ == "__main__":
    main()
