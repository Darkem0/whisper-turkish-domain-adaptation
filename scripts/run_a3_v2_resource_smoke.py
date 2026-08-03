"""Execute the authorized A3_v2 two-step resource smoke only."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import logging
import math
import os
import random
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

import librosa
import numpy as np
import psutil
import torch
from peft import LoraConfig, get_peft_model
from transformers import WhisperForConditionalGeneration, WhisperProcessor, get_scheduler


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "A3_v2_resource_smoke"
CONTRACTS = ROOT / "contracts"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def validate_preflight(training: dict, lock: dict, evaluation: dict) -> dict:
    if training["status"] != "READY_FOR_A3_V2_RESOURCE_SMOKE":
        raise ValueError(f"unexpected training status: {training['status']}")
    if training["initialization"]["initialization_mode"] != "fresh_base":
        raise ValueError("initialization_mode is not fresh_base")
    if training["initialization"]["parent_adapter"] is not None:
        raise ValueError("parent_adapter must be null")
    if training["initialization"]["parent_weights_loaded"] is not False:
        raise ValueError("parent_weights_loaded must be false")
    if training["initialization"]["legacy_resume"] != "FORBIDDEN: A3_legacy_aborted_step34_invalid":
        raise ValueError("legacy resume prohibition missing")
    if evaluation["status"] != "FROZEN_READY_FOR_RESOURCE_SMOKE":
        raise ValueError(f"unexpected evaluation status: {evaluation['status']}")
    checked: dict[str, str] = {}
    for key, hash_key in (
        ("train_manifest", "train_manifest_sha256"),
        ("validation_manifest", "validation_manifest_sha256"),
        ("replay_manifest", "replay_manifest_sha256"),
        ("sampler_schedule", "sampler_schedule_sha256"),
    ):
        path = ROOT / training["data"][key]
        actual = sha256_file(path)
        if actual != training["data"][hash_key]:
            raise ValueError(f"hash mismatch: {path}")
        checked[str(path.relative_to(ROOT)).replace("\\", "/")] = actual
    for name, item in lock["a3_manifests"].items():
        actual = sha256_file(ROOT / item["path"])
        if actual != item["sha256"]:
            raise ValueError(f"manifest lock mismatch: {name}")
    sampler = lock["deterministic_sampler"]
    if sha256_file(ROOT / sampler["path"]) != sampler["sha256"]:
        raise ValueError("sampler lock mismatch")
    for relpath, expected in lock["peer_contract_sha256"].items():
        if sha256_file(ROOT / relpath) != expected:
            raise ValueError(f"peer contract mismatch: {relpath}")
    for item in (evaluation["evaluation_lock"], evaluation["acceptance_lock"], evaluation["immutable_registry"]):
        path = ROOT / item["path"]
        if sha256_file(path) != item["sha256"]:
            raise ValueError(f"frozen contract input mismatch: {path}")
    return checked


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(OUT / "execution.log", encoding="utf-8"), logging.StreamHandler(sys.stdout)],
    )
    started = time.time()
    progress_path = OUT / "training_progress.json"
    try:
        training_path = CONTRACTS / "A3_v2_training_contract.yaml"
        lock_path = CONTRACTS / "A3_v2_data_manifest.lock.json"
        eval_path = CONTRACTS / "A3_v2_eval_contract.yaml"
        training, lock, evaluation = map(read_json, (training_path, lock_path, eval_path))
        input_hashes = validate_preflight(training, lock, evaluation)
        if training["resources"]["preflight_smoke"]["steps"] != 2:
            raise ValueError("resource smoke is not exactly two steps")
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA unavailable")

        schedule = read_jsonl(ROOT / training["data"]["sampler_schedule"])[:32]
        if len(schedule) != 32:
            raise ValueError("smoke schedule must contain exactly 32 microbatches")
        allowed_roles = {"acoustic", "clean_replay"}
        if any(row["role"] not in allowed_roles for row in schedule):
            raise ValueError("invalid schedule role")
        role_counts = {role: sum(row["role"] == role for row in schedule) for role in allowed_roles}
        if role_counts["clean_replay"] == 0:
            raise ValueError("smoke schedule loses clean replay policy")

        resolved = {
            "condition": "A3_v2_resource_smoke",
            "steps": 2,
            "microbatches": 32,
            "seed": 42,
            "initialization_mode": "fresh_base",
            "parent_adapter": None,
            "parent_weights_loaded": False,
            "legacy_resume_attempted": False,
            "model": training["identity"],
            "lora": training["lora"],
            "optimization": training["optimization"],
            "smoke_schedule_role_counts": role_counts,
            "input_sha256": input_hashes,
        }
        (OUT / "config.resolved.json").write_text(json.dumps(resolved, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        environment = {
            "python": sys.version,
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "transformers": importlib.metadata.version("transformers"),
            "peft": importlib.metadata.version("peft"),
            "accelerate": importlib.metadata.version("accelerate"),
            "cuda_available": True,
            "device_name": torch.cuda.get_device_name(0),
            "device_total_mib": round(torch.cuda.get_device_properties(0).total_memory / 1024**2, 2),
        }
        (OUT / "environment.json").write_text(json.dumps(environment, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        set_seed(42)
        device = torch.device("cuda")
        # local_files_only is deliberate: this smoke must not download model/data.
        processor = WhisperProcessor.from_pretrained(
            training["identity"]["base_model"], revision=training["identity"]["tokenizer_processor_revision"], local_files_only=True
        )
        model = WhisperForConditionalGeneration.from_pretrained(
            training["identity"]["base_model"], revision=training["identity"]["base_model_revision"], torch_dtype=torch.float16, local_files_only=True
        ).to(device)
        model.config.use_cache = False
        model.gradient_checkpointing_enable()
        targets = [
            name for name, module in model.named_modules()
            if isinstance(module, torch.nn.Linear) and ".encoder." in name and name.endswith(("q_proj", "v_proj"))
        ]
        if len(targets) != training["lora"]["resolved_module_count"]:
            raise ValueError(f"resolved encoder target count {len(targets)} is unexpected")
        model = get_peft_model(
            model,
            LoraConfig(r=16, lora_alpha=32, target_modules=targets, lora_dropout=0.05, bias="none"),
        )
        trainable = [(name, parameter) for name, parameter in model.named_parameters() if parameter.requires_grad]
        trainable_count = sum(parameter.numel() for _, parameter in trainable)
        non_lora_trainable = [name for name, _ in trainable if "lora_" not in name or ".encoder." not in name]
        base_trainable = [name for name, parameter in model.named_parameters() if parameter.requires_grad and "lora_" not in name]
        if trainable_count != training["lora"]["trainable_parameter_count"]:
            raise ValueError(f"trainable parameter mismatch: {trainable_count}")
        if non_lora_trainable or base_trainable:
            raise ValueError("non-encoder-LoRA or base parameters are trainable")

        optimizer = torch.optim.AdamW(
            (parameter for _, parameter in trainable), lr=1e-5, betas=(0.9, 0.999), weight_decay=0.01
        )
        scheduler = get_scheduler("linear", optimizer, num_warmup_steps=20, num_training_steps=200)
        manifests = {
            "acoustic": {row["sample_id"]: row for row in read_jsonl(ROOT / training["data"]["train_manifest"])},
            "clean_replay": {row["sample_id"]: row for row in read_jsonl(ROOT / training["data"]["replay_manifest"])},
        }
        process = psutil.Process(os.getpid())
        driver_samples: list[int] = []
        stop = threading.Event()

        def poll_driver() -> None:
            while not stop.is_set():
                try:
                    result = subprocess.run(
                        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                        capture_output=True, text=True, check=True, timeout=3,
                    )
                    driver_samples.append(int(result.stdout.strip().splitlines()[0]))
                except (OSError, subprocess.SubprocessError, ValueError, IndexError):
                    pass
                stop.wait(0.2)

        thread = threading.Thread(target=poll_driver, daemon=True)
        torch.cuda.reset_peak_memory_stats()
        thread.start()
        losses: list[float] = []
        step_times: list[float] = []
        model.train()
        total_begin = time.perf_counter()
        try:
            for step in range(2):
                step_begin = time.perf_counter()
                optimizer.zero_grad(set_to_none=True)
                running_loss = 0.0
                for micro in schedule[step * 16 : (step + 1) * 16]:
                    item = manifests[micro["role"]][micro["sample_id"]]
                    audio, _ = librosa.load(ROOT / item["audio_path"], sr=16000, mono=True)
                    features = processor(audio, sampling_rate=16000, return_tensors="pt").input_features.to(device=device, dtype=torch.float16)
                    features.requires_grad_(True)
                    labels = processor.tokenizer(item["transcript"], return_tensors="pt").input_ids.to(device)
                    loss = model(input_features=features, labels=labels).loss
                    if not torch.isfinite(loss):
                        raise FloatingPointError(f"non-finite loss at optimizer step {step + 1}")
                    (loss / 16).backward()
                    running_loss += float(loss.detach().cpu())
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                torch.cuda.synchronize()
                losses.append(running_loss / 16)
                step_times.append(time.perf_counter() - step_begin)
                progress_path.write_text(json.dumps({"condition": "A3_v2_resource_smoke", "completed": False, "optimizer_steps_completed": step + 1, "optimizer_steps_total": 2, "legacy_resume_attempted": False}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        finally:
            stop.set()
            thread.join(timeout=5)
        total_wall = time.perf_counter() - total_begin
        adapter = OUT / "adapter"
        model.save_pretrained(adapter)
        checkpoint = adapter / "adapter_model.safetensors"
        if not checkpoint.is_file():
            raise FileNotFoundError(f"adapter checkpoint missing: {checkpoint}")
        progress_path.write_text(json.dumps({"condition": "A3_v2_resource_smoke", "completed": True, "optimizer_steps_completed": 2, "optimizer_steps_total": 2, "legacy_resume_attempted": False}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        peak_allocated = torch.cuda.max_memory_allocated()
        peak_reserved = torch.cuda.max_memory_reserved()
        metrics = {
            "status": "PASSED",
            "exit_code": 0,
            "optimizer_steps_completed": 2,
            "losses": losses,
            "step_wall_seconds": step_times,
            "median_step_wall_seconds": float(np.median(step_times)),
            "total_wall_seconds": total_wall,
            "peak_cuda_allocated_bytes": peak_allocated,
            "peak_cuda_reserved_bytes": peak_reserved,
            "peak_cuda_allocated_mib": peak_allocated / 1024**2,
            "peak_cuda_reserved_mib": peak_reserved / 1024**2,
            "peak_driver_vram_mib": max(driver_samples, default=None),
            "driver_vram_samples_mib": driver_samples,
            "process_rss_bytes": process.memory_info().rss,
            "process_rss_mib": process.memory_info().rss / 1024**2,
            "trainable_parameter_count": trainable_count,
            "trainable_parameter_names": [name for name, _ in trainable],
            "base_model_trainable_parameter_names": base_trainable,
            "adapter_checkpoint": str(checkpoint.relative_to(ROOT)).replace("\\", "/"),
            "adapter_checkpoint_sha256": sha256_file(checkpoint),
            "smoke_schedule_role_counts": role_counts,
            "acceptance": {
                "cuda_oom_observed": False,
                "no_cuda_oom": True,
                "finite_losses": all(math.isfinite(value) for value in losses),
                "two_optimizer_steps": len(losses) == 2,
                "peak_reserved_under_10000_mib": peak_reserved / 1024**2 < 10000,
                "adapter_checkpoint_written": checkpoint.is_file(),
                "encoder_qv_lora_only_trainable": not non_lora_trainable,
                "base_model_frozen": not base_trainable,
                "trainable_parameter_count_matches": trainable_count == 2621440,
            },
        }
        metrics["acceptance"]["all_passed"] = all(
            value for key, value in metrics["acceptance"].items() if key != "cuda_oom_observed"
        )
        (OUT / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        lock_out = {
            "status": "PASSED" if metrics["acceptance"]["all_passed"] else "BLOCKED_A3_V2_RESOURCE_SMOKE",
            "input_contract_sha256": {str(path.relative_to(ROOT)).replace("\\", "/"): sha256_file(path) for path in (training_path, lock_path, eval_path)},
            "output_sha256": {"config.resolved.json": sha256_file(OUT / "config.resolved.json"), "environment.json": sha256_file(OUT / "environment.json"), "metrics.json": sha256_file(OUT / "metrics.json"), "training_progress.json": sha256_file(progress_path), "adapter/adapter_model.safetensors": sha256_file(checkpoint)},
        }
        (OUT / "artifact_lock.json").write_text(json.dumps(lock_out, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        logging.info("smoke passed=%s", metrics["acceptance"]["all_passed"])
        return 0 if metrics["acceptance"]["all_passed"] else 2
    except Exception:
        error = traceback.format_exc()
        logging.exception("A3_v2 resource smoke failed")
        progress_path.write_text(json.dumps({"condition": "A3_v2_resource_smoke", "completed": False, "status": "BLOCKED_A3_V2_RESOURCE_SMOKE", "traceback": error}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 1
    finally:
        logging.info("elapsed_seconds=%.6f", time.time() - started)


if __name__ == "__main__":
    raise SystemExit(main())
