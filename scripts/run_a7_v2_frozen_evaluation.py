"""A7 frozen evaluation using the established A4 implementation and A7 mapping."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(__file__).with_name("run_a4_v2_frozen_evaluation.py")
CHECKPOINT_PATHS = {
    "step-050": ROOT / "runs/A7_v2_staged_balanced_phone_200/checkpoints/step-050",
    "step-100": ROOT / "runs/A7_v2_staged_balanced_phone_200/checkpoints/step-100",
    "step-150": ROOT / "runs/A7_v2_staged_balanced_phone_200/checkpoints/step-150",
    "step-200": ROOT / "runs/A7_v2_resume150_final_200_retry1/checkpoints/step-200",
}


def main() -> int:
    code = SOURCE.read_text(encoding="utf-8").replace("A4_v2", "A7_v2").replace(
        "a4_v2", "a7_v2"
    )
    namespace = {"__name__": "a7_frozen_eval_base", "__file__": str(Path(__file__).resolve())}
    exec(compile(code, str(Path(__file__).resolve()), "exec"), namespace)
    run = namespace["RUN"]
    contract_path = namespace["CONTRACT"]
    digest = namespace["digest"]
    load_json = namespace["load_json"]
    save_json = namespace["save_json"]

    def preflight(contract: dict) -> dict:
        frozen_source = load_json(ROOT / "contracts/A6_v2_eval_contract.yaml")
        contract["frozen_sets"] = frozen_source["frozen_sets"]
        checks = []
        for block in ("evaluation_lock", "acceptance_lock", "immutable_registry"):
            entry = contract[block]
            path = ROOT / entry["path"]
            checks.append({"name": block, "expected": entry["sha256"], "actual": digest(path) if path.exists() else None})
        for entry in contract["frozen_sets"]:
            path = ROOT / entry["path"]
            checks.append({"name": entry["name"], "expected": entry["sha256"], "actual": digest(path) if path.exists() else None})
        for checkpoint, directory in CHECKPOINT_PATHS.items():
            lock = load_json(directory / "checkpoint_lock.json")
            model = directory / "adapter/adapter_model.safetensors"
            config = directory / "adapter/adapter_config.json"
            adapter = load_json(config)
            expected_step = int(checkpoint[-3:])
            valid = (
                model.is_file()
                and model.stat().st_size > 0
                and config.is_file()
                and lock.get("adapter_sha256") == digest(model)
                and lock.get("step") == expected_step
                and adapter.get("base_model_name_or_path") == namespace["MODEL"]
                and adapter.get("r") == 16
                and adapter.get("lora_alpha") == 32
            )
            if checkpoint == "step-200":
                valid = valid and lock.get("global_optimizer_step") == 200 and lock.get("schedule_index") == 3200 and lock.get("resumed_from_checkpoint") == 150 and lock.get("resume_mode") == "ADAPTER_CONTINUATION_WITH_OPTIMIZER_RESET"
            checks.append({"name": checkpoint, "expected": "valid", "actual": "valid" if valid else "invalid"})
        passed = all(item["actual"] == item["expected"] for item in checks)
        return {"status": "PASSED" if passed else "BLOCKED", "contract_sha256": digest(contract_path), "checks": checks}

    run.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=run / "execution.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    contract = load_json(contract_path)
    result = preflight(contract)
    save_json(run / "preflight.json", result)
    if result["status"] != "PASSED":
        save_json(run / "evaluation_progress.json", {"status": "BLOCKED_A7_V2_FROZEN_EVALUATION", "preflight": result["status"]})
        return 2

    import torch
    from peft import PeftModel
    from transformers import WhisperForConditionalGeneration, WhisperProcessor

    targets = namespace["target_rows"](contract)
    if len(targets) != 7:
        raise RuntimeError(f"Expected seven frozen datasets, got {len(targets)}")
    config_sha = __import__("hashlib").sha256(json.dumps(namespace["DECODE"], sort_keys=True).encode()).hexdigest()
    state_root = ROOT / "state"
    progress_path = run / "evaluation_progress.json"
    if progress_path.exists():
        progress = load_json(progress_path)
        completed = {(row["checkpoint"], row["dataset"]) for row in progress.get("completed_targets", []) if isinstance(row, dict)}
    else:
        completed = set()
        progress = {"status": "RUNNING", "preflight": "PASSED", "completed_targets": []}
    save_json(state_root / "a7_v2_frozen_eval_state.json", {"status": "RUNNING", "planned_targets": 28, "completed_targets": len(completed)})
    save_json(state_root / "a7_v2_frozen_eval_heartbeat.json", {"status": "RUNNING", "pid": os.getpid()})
    save_json(state_root / "a7_v2_frozen_eval_progress.json", {"planned_targets": 28, "completed_targets": len(completed)})
    save_json(progress_path, progress)

    for checkpoint, directory in CHECKPOINT_PATHS.items():
        adapter_path = directory / "adapter"
        adapter_sha = digest(adapter_path / "adapter_model.safetensors")
        base = WhisperForConditionalGeneration.from_pretrained(namespace["MODEL"], revision=namespace["REVISION"], local_files_only=True, torch_dtype=torch.float16).to("cuda").eval()
        model = PeftModel.from_pretrained(base, str(adapter_path)).eval()
        processor = WhisperProcessor.from_pretrained(namespace["MODEL"], revision=namespace["REVISION"], local_files_only=True)
        for name, source, rows in targets:
            key = (checkpoint, name)
            if key in completed:
                continue
            progress["current_target"] = {"checkpoint": checkpoint, "dataset": name}
            progress["status"] = "RUNNING"
            save_json(progress_path, progress)
            save_json(state_root / "a7_v2_frozen_eval_state.json", {"status": "RUNNING", "planned_targets": 28, "completed_targets": len(completed), "current_target": progress["current_target"]})
            namespace["evaluate_target"](model, processor, checkpoint, name, source, rows, adapter_sha, config_sha)
            completed.add(key)
            progress["completed_targets"].append({"checkpoint": checkpoint, "dataset": name})
            save_json(progress_path, progress)
            save_json(state_root / "a7_v2_frozen_eval_progress.json", {"planned_targets": 28, "completed_targets": len(completed)})
        del model, base
        torch.cuda.empty_cache()
    save_json(progress_path, {"status": "COMPLETED", "preflight": "PASSED", "completed_targets": 28})
    save_json(state_root / "a7_v2_frozen_eval_state.json", {"status": "COMPLETED", "planned_targets": 28, "completed_targets": 28})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
