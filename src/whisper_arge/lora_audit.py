from __future__ import annotations

import json
import math
from pathlib import Path

from .hashing import sha256_file


def audit_lora_run(run_root: str | Path) -> dict:
    """Write an immutable, post-run integrity attestation for a LoRA run."""
    root = Path(run_root)
    result_path = root / "training_result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    lock = json.loads(
        Path("data/materialized/training_v2d/TRAINING_LOCK_v2d.json").read_text(encoding="utf-8")
    )
    contract = json.loads(
        Path("data/materialized/training_v2d/training_contract_v2d.json").read_text(
            encoding="utf-8"
        )
    )
    losses = [float(value) for value in result["loss"]]
    gradients = [float(value) for value in result["gradient_norm"]]
    adapter = root / "adapter" / "adapter_model.safetensors"
    checks = {
        "optimizer_steps_exactly_200": result["steps"] == 200 and len(losses) == 200,
        "schedule_matches_training_lock": (
            result["schedule_sha256"]
            == lock["files"]["training_v2d/sample_schedule_v2d_200.jsonl"]
            == contract["schedule"]["sha256"]
        ),
        "finite_loss": all(math.isfinite(value) for value in losses),
        "finite_gradient_norm": all(math.isfinite(value) for value in gradients),
        "adapter_exists": adapter.exists(),
    }
    report = {
        "schema_version": 1,
        "status": "pass" if all(checks.values()) else "fail",
        "condition": result["condition"],
        "checks": checks,
        "starting_checkpoint": {
            "kind": "base_model_only",
            "model": lock["model"],
            "revision": lock["model_revision"],
            "evidence": "The locked run entrypoint has no resume/checkpoint input and loads WhisperForConditionalGeneration.from_pretrained(model, revision).",
        },
        "steps": result["steps"],
        "schedule_sha256": result["schedule_sha256"],
        "training_wall_seconds": result["wall_seconds"],
        "peak_vram": {
            "pytorch_allocator_bytes": result["peak_vram_bytes"],
            "process_level_gpu_bytes": None,
            "process_level_gpu_status": "not_captured: NVIDIA process query returned insufficient-permissions/N_A during this run",
        },
        "sha256": {
            "adapter_checkpoint": sha256_file(adapter),
            "adapter_config": sha256_file(root / "adapter" / "adapter_config.json"),
            "training_metrics": sha256_file(result_path),
            "training_contract": sha256_file(
                "data/materialized/training_v2d/training_contract_v2d.json"
            ),
            "training_lock": sha256_file("data/materialized/training_v2d/TRAINING_LOCK_v2d.json"),
        },
    }
    output = root / "run_integrity_v2d.json"
    if output.exists():
        existing = json.loads(output.read_text(encoding="utf-8"))
        if existing != report:
            raise ValueError("immutable integrity report already exists with different content")
    else:
        output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return {**report, "report": str(output), "report_sha256": sha256_file(output)}
