"""A6 minimum-diff A5/A4 runner with an authorized two-step smoke mode only."""

from __future__ import annotations

import importlib.metadata
import json
import logging
import os
import random
import sys
import time
from pathlib import Path

import librosa
import numpy as np
import psutil
import torch
from peft import LoraConfig, get_peft_model
from transformers import WhisperForConditionalGeneration, WhisperProcessor, get_scheduler


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(__file__).with_name("run_a4_v2_fresh_base_200.py")
SMOKE_ROOT = ROOT / "runs" / "A6_v2_resource_smoke"


def a6_base() -> dict:
    """Load A4's proven helpers after only A6 path/identity substitutions."""
    code = SOURCE.read_text(encoding="utf-8")
    for before, after in (
        ("A4_v2", "A6_v2"),
        ("A4_V2", "A6_V2"),
        ("a4_v2", "a6_v2"),
        ("training_a4_v2", "training_a5_v2"),
        ("a4_", "a5_"),
    ):
        code = code.replace(before, after)
    code = code.replace(
        'and ".decoder." in n\n            and n.endswith(("q_proj", "v_proj"))',
        'and (".encoder." in n or ".decoder." in n)\n            and n.endswith(("q_proj", "v_proj"))',
    )
    code = code.replace("if len(targets) != 16:", "if len(targets) != 80:")
    code = code.replace(
        'if count != 655360 or any("lora_" not in n or ".decoder." not in n for n in names):',
        'if count != 3276800 or any("lora_" not in n or not (".encoder." in n or ".decoder." in n) for n in names):',
    )
    code = code.replace(
        "        optimizer = torch.optim.AdamW(\n            (p for _, p in trainable)",
        '        save(OUT / "trainable_parameter_inventory.json", {"status": "PASSED", "trainable_parameter_count": count, "trainable_parameters": [{"name": n, "numel": p.numel()} for n, p in trainable], "base_weights_frozen": all(not p.requires_grad for n, p in model.named_parameters() if "lora_" not in n)})\n        optimizer = torch.optim.AdamW(\n            (p for _, p in trainable)',
    )
    code = code.replace(
        '                    OUT / "sampler_audit.json",\n                    resource,',
        '                    OUT / "sampler_audit.json",\n                    OUT / "trainable_parameter_inventory.json",\n                    resource,',
    )
    namespace = {"__name__": "a6_base", "__file__": str(Path(__file__).resolve())}
    exec(compile(code, str(Path(__file__).resolve()), "exec"), namespace)
    return namespace


BASE = a6_base()
digest = BASE["digest"]
load = BASE["load"]
save = BASE["save"]
preflight = BASE["preflight"]
gpu_mib = BASE["gpu_mib"]


def target_modules(model: torch.nn.Module) -> list[str]:
    targets = [
        name
        for name, module in model.named_modules()
        if isinstance(module, torch.nn.Linear)
        and (".encoder." in name or ".decoder." in name)
        and name.endswith(("q_proj", "v_proj"))
    ]
    if not targets:
        raise ValueError("A6 no encoder/decoder Q/V LoRA targets found")
    return targets


def trainability_inventory(model: torch.nn.Module) -> tuple[list[dict], int]:
    inventory = [
        {"name": name, "numel": parameter.numel()}
        for name, parameter in model.named_parameters()
        if parameter.requires_grad
    ]
    invalid = [
        entry["name"]
        for entry in inventory
        if "lora_" not in entry["name"]
        or not (".encoder." in entry["name"] or ".decoder." in entry["name"])
        or not ("q_proj" in entry["name"] or "v_proj" in entry["name"])
    ]
    base_trainable = [
        name
        for name, parameter in model.named_parameters()
        if parameter.requires_grad and "lora_" not in name
    ]
    if invalid or base_trainable:
        raise ValueError(f"A6 smoke trainability mismatch: {invalid or base_trainable}")
    scopes = {"encoder": 0, "decoder": 0}
    for entry in inventory:
        scopes["encoder" if ".encoder." in entry["name"] else "decoder"] += entry["numel"]
    if not all(scopes.values()):
        raise ValueError(f"A6 missing trainable scope: {scopes}")
    return inventory, sum(item["numel"] for item in inventory)


def smoke() -> int:
    if SMOKE_ROOT.exists() and any(path.name != "attempts" for path in SMOKE_ROOT.iterdir()):
        raise FileExistsError(f"refusing to overwrite existing smoke: {SMOKE_ROOT}")
    SMOKE_ROOT.mkdir(parents=True, exist_ok=True)
    log_path = SMOKE_ROOT / "execution.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )
    started = time.perf_counter()
    try:
        training = load(ROOT / "contracts/A6_v2_training_contract.yaml")
        lock = load(ROOT / "contracts/A6_v2_data_manifest.lock.json")
        evaluation = load(ROOT / "contracts/A6_v2_eval_contract.yaml")
        inputs = preflight(training, lock, evaluation)
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA unavailable")
        if training["status"] != "READY_FOR_A6_V2_RESOURCE_SMOKE":
            raise ValueError("A6 contract is not authorized for resource smoke")
        random.seed(training["optimization"]["seed"])
        np.random.seed(training["optimization"]["seed"])
        torch.manual_seed(training["optimization"]["seed"])
        torch.cuda.manual_seed_all(training["optimization"]["seed"])
        schedule = load(ROOT / training["data"]["schedule"])
        rows = {row["sample_id"]: row for row in load(ROOT / training["data"]["train_manifest"])}
        smoke_schedule = schedule[:32]
        if (
            len(schedule) != 3200
            or len(smoke_schedule) != 32
            or any(row["role"] != "acoustic" for row in smoke_schedule)
        ):
            raise ValueError("A6 smoke schedule counts/roles mismatch")
        if any(row["sample_id"] not in rows for row in smoke_schedule):
            raise ValueError("A6 smoke schedule contains missing sample ID")
        resolved = {
            "condition": "A6_v2_resource_smoke",
            "initialization_mode": "fresh_base",
            "parent_adapter": None,
            "parent_weights_loaded": False,
            "adapter_loading": "FORBIDDEN_A2_A3_A4_A5",
            "legacy_resume_attempted": False,
            "optimizer_steps": 2,
            "consumed_microbatches": 32,
            "input_sha256": inputs,
            "contract": training,
        }
        save(SMOKE_ROOT / "config.resolved.json", resolved)
        environment = {
            "python": sys.version,
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "transformers": importlib.metadata.version("transformers"),
            "peft": importlib.metadata.version("peft"),
            "gpu": torch.cuda.get_device_name(0),
            "gpu_total_mib": torch.cuda.get_device_properties(0).total_memory / 1024**2,
            "base_model_revision": training["identity"]["base_model_revision"],
            "tokenizer_processor_revision": training["identity"]["tokenizer_processor_revision"],
        }
        save(SMOKE_ROOT / "environment.json", environment)
        processor = WhisperProcessor.from_pretrained(
            training["identity"]["base_model"],
            revision=training["identity"]["tokenizer_processor_revision"],
            local_files_only=True,
        )
        base = WhisperForConditionalGeneration.from_pretrained(
            training["identity"]["base_model"],
            revision=training["identity"]["base_model_revision"],
            torch_dtype=torch.float16,
            local_files_only=True,
        ).to("cuda")
        base.config.use_cache = False
        base.gradient_checkpointing_enable()
        targets = target_modules(base)
        model = get_peft_model(
            base,
            LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, target_modules=targets, bias="none"),
        )
        inventory, trainable_count = trainability_inventory(model)
        save(
            SMOKE_ROOT / "trainable_parameter_inventory.json",
            {
                "status": "PASSED",
                "target_modules": targets,
                "trainable_parameter_count": trainable_count,
                "trainable_parameters": inventory,
                "base_weights_frozen": True,
            },
        )
        optimizer = torch.optim.AdamW(
            (parameter for _, parameter in model.named_parameters() if parameter.requires_grad),
            lr=1e-5,
            betas=(0.9, 0.999),
            weight_decay=0.01,
        )
        scheduler = get_scheduler("linear", optimizer, num_warmup_steps=20, num_training_steps=200)
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        process = psutil.Process(os.getpid())
        losses, step_times, progress = [], [], []
        gradient_scope_l1 = {"encoder": 0.0, "decoder": 0.0}
        model.train()
        for step in range(2):
            step_started = time.perf_counter()
            optimizer.zero_grad(set_to_none=True)
            total = 0.0
            for micro in smoke_schedule[step * 16 : (step + 1) * 16]:
                row = rows[micro["sample_id"]]
                audio, _ = librosa.load(ROOT / row["audio_path"], sr=16000, mono=True)
                features = processor(
                    audio, sampling_rate=16000, return_tensors="pt"
                ).input_features.to("cuda", dtype=torch.float16)
                features.requires_grad_(True)
                labels = processor.tokenizer(row["transcript"], return_tensors="pt").input_ids.to(
                    "cuda"
                )
                loss = model(input_features=features, labels=labels).loss
                if not torch.isfinite(loss):
                    raise FloatingPointError(f"non-finite A6 smoke loss at step {step + 1}")
                (loss / 16).backward()
                total += float(loss.detach().cpu())
                progress.append(
                    {
                        "optimizer_step": step + 1,
                        "microbatch_index": micro["microstep"],
                        "sample_id": micro["sample_id"],
                        "role": "acoustic",
                        "loss": float(loss.detach().cpu()),
                    }
                )
            for name, parameter in model.named_parameters():
                if parameter.requires_grad and parameter.grad is not None:
                    scope = "encoder" if ".encoder." in name else "decoder"
                    gradient_scope_l1[scope] += float(parameter.grad.detach().abs().sum().cpu())
            if not all(value > 0.0 for value in gradient_scope_l1.values()):
                raise FloatingPointError(
                    f"A6 smoke missing nonzero gradient scope at step {step + 1}: {gradient_scope_l1}"
                )
            optimizer.step()
            scheduler.step()
            torch.cuda.synchronize()
            losses.append(total / 16)
            step_times.append(time.perf_counter() - step_started)
        adapter = SMOKE_ROOT / "adapter"
        model.save_pretrained(adapter)
        adapter_sha = digest(adapter / "adapter_model.safetensors")
        (SMOKE_ROOT / "training_progress.jsonl").write_text(
            "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in progress),
            encoding="utf-8",
        )
        metrics = {
            "status": "PASSED",
            "exit_code": 0,
            "optimizer_steps_completed": 2,
            "consumed_microbatches": 32,
            "acoustic_microbatches": 32,
            "replay_microbatches": 0,
            "losses": losses,
            "optimizer_step_seconds": step_times,
            "training_loop_seconds": sum(step_times),
            "total_wall_seconds": time.perf_counter() - started,
            "trainable_parameter_count": trainable_count,
            "peak_cuda_allocated_mib": torch.cuda.max_memory_allocated() / 1024**2,
            "peak_cuda_reserved_mib": torch.cuda.max_memory_reserved() / 1024**2,
            "peak_driver_vram_mib": gpu_mib(),
            "process_rss_mib": process.memory_info().rss / 1024**2,
            "adapter_sha256": adapter_sha,
            "gradient_scope_l1": gradient_scope_l1,
            "fresh_base": True,
            "parent_adapter_loaded": False,
            "legacy_resume_attempted": False,
        }
        if metrics["peak_cuda_reserved_mib"] >= 10000:
            raise RuntimeError(f"A6 reserved VRAM gate failed: {metrics['peak_cuda_reserved_mib']}")
        save(SMOKE_ROOT / "metrics.json", metrics)
        save(
            SMOKE_ROOT / "artifact_lock.json",
            {
                "status": "PASSED",
                "input_contract_sha256": {
                    path: digest(ROOT / path)
                    for path in (
                        "contracts/A6_v2_training_contract.yaml",
                        "contracts/A6_v2_data_manifest.lock.json",
                        "contracts/A6_v2_eval_contract.yaml",
                    )
                },
                "input_sha256": inputs,
                "adapter_sha256": adapter_sha,
                "outputs_sha256": {
                    str(path.relative_to(SMOKE_ROOT)).replace("\\", "/"): digest(path)
                    for path in (
                        SMOKE_ROOT / "config.resolved.json",
                        SMOKE_ROOT / "environment.json",
                        SMOKE_ROOT / "training_progress.jsonl",
                        SMOKE_ROOT / "trainable_parameter_inventory.json",
                        SMOKE_ROOT / "metrics.json",
                    )
                },
            },
        )
        logging.info("A6_v2 resource smoke passed")
        return 0
    except Exception:
        error = __import__("traceback").format_exc()
        logging.exception("A6_v2 resource smoke blocked")
        save(
            SMOKE_ROOT / "metrics.json",
            {"status": "BLOCKED_A6_V2_RESOURCE_SMOKE", "traceback": error},
        )
        return 1


def save_state(status: str, **extra: object) -> None:
    path = ROOT / "state" / "a6_v2_training_state.json"
    payload = {
        "status": status,
        "pid": os.getpid(),
        "run_directory": "runs/A6_v2_fresh_base_200",
        **extra,
    }
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def full() -> int:
    save_state("RUNNING", started_at_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    result = BASE["main"]()
    save_state(
        "COMPLETED" if result == 0 else "BLOCKED_A6_V2_TECHNICAL",
        exit_code=result,
        completed_at_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
    return result


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("preflight", "smoke", "full"), default="smoke")
    mode = parser.parse_args().mode
    if mode == "preflight":
        training = load(ROOT / "contracts/A6_v2_training_contract.yaml")
        lock = load(ROOT / "contracts/A6_v2_data_manifest.lock.json")
        evaluation = load(ROOT / "contracts/A6_v2_eval_contract.yaml")
        print(json.dumps({"status": "PASSED", "inputs": preflight(training, lock, evaluation)}))
        return
    elif mode == "smoke":
        raise SystemExit(smoke())
    raise SystemExit(full())


if __name__ == "__main__":
    main()
