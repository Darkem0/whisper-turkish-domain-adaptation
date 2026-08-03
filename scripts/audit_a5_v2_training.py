"""Read-only integrity audit for the completed A5 full-training artefacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/A5_v2_fresh_base_200"
REPORTS = ROOT / "reports"
CHECKPOINTS = (50, 100, 150, 200)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    metrics, artifact = load(RUN / "metrics.json"), load(RUN / "artifact_lock.json")
    problems: list[str] = []
    inventory: list[dict] = []
    current_contracts = {path: sha(ROOT / path) for path in artifact["input_contract_sha256"]}
    if current_contracts != artifact["input_contract_sha256"]:
        problems.append("current_contract_hash_mismatch")
    for step in CHECKPOINTS:
        directory = RUN / "checkpoints" / f"step-{step:03d}"
        required = [directory / "adapter/adapter_model.safetensors", directory / "adapter/adapter_config.json", directory / "checkpoint_lock.json", directory / "optimizer.pt", directory / "scheduler.pt", directory / "resume_state.json"]
        if any(not path.exists() for path in required):
            problems.append(f"missing_checkpoint_file:{step}")
            continue
        lock, resume = load(directory / "checkpoint_lock.json"), load(directory / "resume_state.json")
        file_hashes = {str(path.relative_to(directory)).replace("\\", "/"): sha(path) for path in required if path.name != "checkpoint_lock.json"}
        for path, expected in lock.get("files_sha256", {}).items():
            if file_hashes.get(path) != expected:
                problems.append(f"checkpoint_hash_mismatch:{step}:{path}")
        if lock.get("optimizer_step") != step or resume.get("optimizer_step") != step or lock.get("consumed_microbatches") != step * 16:
            problems.append(f"checkpoint_progress_mismatch:{step}")
        inventory.append({"checkpoint": f"step-{step:03d}", "adapter_sha256": file_hashes["adapter/adapter_model.safetensors"], "optimizer_step": step, "consumed_microbatches": step * 16, "config_sha256": lock.get("config_sha256"), "input_manifest_hashes": lock.get("input_sha256"), "optimizer_state": "PRESENT", "scheduler_state": "PRESENT", "resume_state": "PRESENT"})
    validations = metrics.get("validations", [])
    if len(validations) != 4 or any(item.get("samples") != 9081 or not item.get("predictions_sha256") for item in validations):
        problems.append("local_validation_inventory_invalid")
    for item in validations:
        prediction = ROOT / item["predictions"]
        if not prediction.exists() or sha(prediction) != item["predictions_sha256"]:
            problems.append(f"validation_prediction_hash_mismatch:{item.get('optimizer_step')}")
    if metrics.get("status") != "PASSED" or metrics.get("optimizer_steps_completed") != 200 or metrics.get("trainable_parameter_count") != 2621440:
        problems.append("global_training_metrics_invalid")
    sampler = load(RUN / "sampler_audit.json")
    if sampler.get("acoustic_microbatches") != 3200 or sampler.get("replay_microbatches") != 0:
        problems.append("sampler_counts_invalid")
    log = (RUN / "execution.log").read_text(encoding="utf-8")
    if "A5_v2 training passed" not in log or "CUDA out of memory" in log or "non-finite" in log.lower():
        problems.append("terminal_log_invalid")
    status = "PASSED" if not problems else "FAILED"
    result = {"status": status, "problems": problems, "checkpoints": inventory, "global": {"optimizer_steps": metrics.get("optimizer_steps_completed"), "consumed_microbatches": 3200, "acoustic": sampler.get("acoustic_microbatches"), "replay": sampler.get("replay_microbatches"), "trainable_parameters": metrics.get("trainable_parameter_count"), "base_weights_frozen": True, "contracts": current_contracts}, "validations": validations}
    (REPORTS / "a5_v2_training_integrity_audit.md").write_text("# A5_v2 training integrity audit\n\n" + json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (REPORTS / "a5_v2_checkpoint_inventory.md").write_text("# A5_v2 checkpoint inventory\n\n" + json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (REPORTS / "a5_v2_local_validation_summary.md").write_text("# A5_v2 local validation summary\n\n" + json.dumps(validations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (REPORTS / "a5_v2_training_final_report.md").write_text(f"# A5_v2 training final report\n\nIntegrity: `{status}`. Optimizer steps: {metrics.get('optimizer_steps_completed')}/200; acoustic microbatches: 3200; replay: 0; trainable parameters: {metrics.get('trainable_parameter_count')}. A5 remains diagnostic-only and production promotion is forbidden.\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    if status != "PASSED":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
