"""Authorized fresh-base A4_v2 200-step training with locked local validation."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import logging
import os
import random
import subprocess
import sys
import time
import traceback
from pathlib import Path

import librosa
import numpy as np
import psutil
import torch
from peft import LoraConfig, get_peft_model
from transformers import WhisperForConditionalGeneration, WhisperProcessor, get_scheduler

from whisper_arge.metrics import corpus_metrics

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "A4_v2_fresh_base_200"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def load(path: Path):
    if path.suffix == ".jsonl":
        return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x]
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def gpu_mib() -> int | None:
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            check=True,
            timeout=4,
        )
        return int(r.stdout.strip().splitlines()[0])
    except (OSError, subprocess.SubprocessError, ValueError, IndexError):
        return None


def preflight(training, lock, evaluation) -> dict[str, str]:
    required = ("status", "identity.base_model", "identity.base_model_revision", "identity.tokenizer_processor_revision", "initialization.mode", "initialization.parent_adapter", "initialization.legacy_resume", "data.train_manifest", "data.validation_manifest", "data.replay_manifest", "data.schedule")
    missing = []
    for path in required:
        value = training
        for key in path.split("."):
            if not isinstance(value, dict) or key not in value:
                missing.append(path)
                break
            value = value[key]
    for path in ("evaluation_lock.path", "evaluation_lock.sha256", "acceptance_lock.path", "acceptance_lock.sha256", "immutable_registry.path", "immutable_registry.sha256"):
        value = evaluation
        for key in path.split("."):
            if not isinstance(value, dict) or key not in value:
                missing.append(path)
                break
            value = value[key]
    if missing:
        raise ValueError("BLOCKED_A4_V2_CONTRACT_SCHEMA missing_paths: " + ", ".join(missing))
    if training["status"] != "READY_FOR_A4_V2_RESOURCE_SMOKE":
        raise ValueError("training contract not smoke-passed authorization state")
    init = training["initialization"]
    if (
        init["mode"] != "fresh_base"
        or init["parent_adapter"] is not None
        or init.get("parent_weights_loaded", False)
    ):
        raise ValueError("fresh-base initialization contract mismatch")
    if init["legacy_resume"] != "FORBIDDEN: A3_legacy_aborted_step34_invalid":
        raise ValueError("legacy-resume prohibition mismatch")
    checked = {}
    for name in ("train_manifest", "validation_manifest", "replay_manifest", "schedule"):
        p = ROOT / training["data"][name]
        checked[str(p.relative_to(ROOT)).replace("\\", "/")] = digest(p)
    materialized = lock.get("materialized", {})
    for name, path in (
        ("train", training["data"]["train_manifest"]),
        ("validation", training["data"]["validation_manifest"]),
        ("replay", training["data"]["replay_manifest"]),
        ("schedule", training["data"]["schedule"]),
    ):
        if name in materialized and digest(ROOT / path) != materialized[name]["sha256"]:
            raise ValueError(f"manifest lock mismatch: {path}")
    for item in (
        evaluation["evaluation_lock"],
        evaluation["acceptance_lock"],
        evaluation["immutable_registry"],
    ):
        if digest(ROOT / item["path"]) != item["sha256"]:
            raise ValueError(f"frozen input hash mismatch: {item['path']}")
    return checked


def checkpoint(model, optimizer, scheduler, step, consumed, counts, config_hash, inputs) -> dict:
    root = OUT / "checkpoints" / f"step-{step:03d}"
    root.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(root / "adapter")
    torch.save(optimizer.state_dict(), root / "optimizer.pt")
    torch.save(scheduler.state_dict(), root / "scheduler.pt")
    state = {
        "optimizer_step": step,
        "consumed_microbatches": consumed,
        "acoustic_microbatches": counts["acoustic"],
        "replay_microbatches": counts["clean_replay"],
        "config_sha256": config_hash,
        "input_sha256": inputs,
        "resume_policy": "only this verified A4_v2 run; never legacy A4 step 34",
    }
    save(root / "resume_state.json", state)
    files = [
        root / "adapter" / "adapter_model.safetensors",
        root / "adapter" / "adapter_config.json",
        root / "optimizer.pt",
        root / "scheduler.pt",
        root / "resume_state.json",
    ]
    state["files_sha256"] = {str(p.relative_to(root)).replace("\\", "/"): digest(p) for p in files}
    save(root / "checkpoint_lock.json", state)
    return {
        "step": step,
        "path": str(root.relative_to(ROOT)).replace("\\", "/"),
        "adapter_sha256": state["files_sha256"]["adapter/adapter_model.safetensors"],
        "consumed_microbatches": consumed,
        "acoustic_microbatches": counts["acoustic"],
        "replay_microbatches": counts["clean_replay"],
    }


def validate(model, processor, rows, step) -> dict:
    root = OUT / "validations" / f"step-{step:03d}"
    root.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    losses = []
    pairs = []
    predictions = root / "predictions.jsonl"
    model.eval()
    with predictions.open("w", encoding="utf-8") as out, torch.no_grad():
        for index, row in enumerate(rows, start=1):
            audio, _ = librosa.load(ROOT / row["audio_path"], sr=16000, mono=True)
            feats = processor(audio, sampling_rate=16000, return_tensors="pt").input_features.to(
                device="cuda", dtype=torch.float16
            )
            labels = processor.tokenizer(row["transcript"], return_tensors="pt").input_ids.to(
                "cuda"
            )
            loss = model(input_features=feats, labels=labels).loss
            if not torch.isfinite(loss):
                raise FloatingPointError(
                    f"non-finite validation loss step={step} sample={row['sample_id']}"
                )
            generated = model.generate(
                feats,
                language="tr",
                task="transcribe",
                num_beams=5,
                do_sample=False,
                condition_on_prev_tokens=False,
                max_new_tokens=444,
            )
            prediction = processor.batch_decode(generated, skip_special_tokens=True)[0]
            losses.append(float(loss.detach().cpu()))
            pairs.append((row["transcript"], prediction))
            out.write(
                json.dumps(
                    {"sample_id": row["sample_id"], "prediction": prediction}, ensure_ascii=False
                )
                + "\n"
            )
            if index % 100 == 0:
                logging.info("validation step=%s sample=%s/%s", step, index, len(rows))
    metric = corpus_metrics(pairs)
    result = {
        "optimizer_step": step,
        "validation_loss": float(np.mean(losses)),
        "sample_count": len(rows),
        "evaluation_wall_seconds": time.perf_counter() - start,
        "predictions": str(predictions.relative_to(ROOT)).replace("\\", "/"),
        "predictions_sha256": digest(predictions),
        **metric,
    }
    save(root / "metrics.json", result)
    model.train()
    return result


def main() -> int:
    if OUT.exists() and any(path.name != "attempts" for path in OUT.iterdir()):
        raise FileExistsError(f"refusing to overwrite existing run: {OUT}")
    OUT.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(OUT / "execution.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    progress = OUT / "training_progress.jsonl"
    resource = OUT / "resource_usage.jsonl"
    started = time.perf_counter()
    try:
        training = load(ROOT / "contracts/A4_v2_training_contract.yaml")
        lock = load(ROOT / "contracts/A4_v2_data_manifest.lock.json")
        evaluation = load(ROOT / "contracts/A4_v2_eval_contract.yaml")
        inputs = preflight(training, lock, evaluation)
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA unavailable")
        random.seed(20260730)
        np.random.seed(20260730)
        torch.manual_seed(20260730)
        torch.cuda.manual_seed_all(20260730)
        schedule = load(ROOT / training["data"]["schedule"])
        if (
            len(schedule) != 3200
            or sum(x["role"] == "acoustic" for x in schedule) != 3200
            or any(x["role"] != "acoustic" for x in schedule)
        ):
            raise ValueError("locked sampler counts mismatch")
        acoustic = {x["sample_id"]: x for x in load(ROOT / training["data"]["train_manifest"])}
        replay = {x["sample_id"]: x for x in load(ROOT / training["data"]["replay_manifest"])}
        validation = load(ROOT / training["data"]["validation_manifest"])
        if any(
            x["sample_id"] not in (acoustic if x["role"] == "acoustic" else replay)
            for x in schedule
        ):
            raise ValueError("schedule sample not in role manifest")
        resolved = {
            "condition": "A4_v2_fresh_base_200",
            "initialization_mode": "fresh_base",
            "parent_adapter": None,
            "parent_weights_loaded": False,
            "legacy_resume_attempted": False,
            "steps": 200,
            "microbatches": 3200,
            "seed": 20260730,
            "input_sha256": inputs,
            "contract": training,
        }
        save(OUT / "config.resolved.json", resolved)
        config_hash = digest(OUT / "config.resolved.json")
        env = {
            "python": sys.version,
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "transformers": importlib.metadata.version("transformers"),
            "peft": importlib.metadata.version("peft"),
            "accelerate": importlib.metadata.version("accelerate"),
            "gpu": torch.cuda.get_device_name(0),
            "gpu_total_mib": torch.cuda.get_device_properties(0).total_memory / 1024**2,
        }
        save(OUT / "environment.json", env)
        processor = WhisperProcessor.from_pretrained(
            training["identity"]["base_model"],
            revision=training["identity"]["tokenizer_processor_revision"],
            local_files_only=True,
        )
        model = WhisperForConditionalGeneration.from_pretrained(
            training["identity"]["base_model"],
            revision=training["identity"]["base_model_revision"],
            torch_dtype=torch.float16,
            local_files_only=True,
        ).to("cuda")
        model.config.use_cache = False
        model.gradient_checkpointing_enable()
        targets = [
            n
            for n, m in model.named_modules()
            if isinstance(m, torch.nn.Linear)
            and ".decoder." in n
            and n.endswith(("q_proj", "v_proj"))
        ]
        if len(targets) != 16:
            raise ValueError(f"unexpected target count {len(targets)}")
        model = get_peft_model(
            model,
            LoraConfig(r=16, lora_alpha=32, target_modules=targets, lora_dropout=0.05, bias="none"),
        )
        trainable = [(n, p) for n, p in model.named_parameters() if p.requires_grad]
        names = {n for n, _ in trainable}
        count = sum(p.numel() for _, p in trainable)
        if count != 655360 or any("lora_" not in n or ".decoder." not in n for n in names):
            raise ValueError("trainability mismatch")
        optimizer = torch.optim.AdamW(
            (p for _, p in trainable), lr=1e-5, betas=(0.9, 0.999), weight_decay=0.01
        )
        scheduler = get_scheduler("linear", optimizer, num_warmup_steps=20, num_training_steps=200)
        torch.cuda.reset_peak_memory_stats()
        proc = psutil.Process(os.getpid())
        counts = {"acoustic": 0, "clean_replay": 0}
        losses = []
        checkpoints = []
        validations = []
        model.train()
        for step in range(1, 201):
            step_start = time.perf_counter()
            optimizer.zero_grad(set_to_none=True)
            total_loss = 0.0
            for micro in schedule[(step - 1) * 16 : step * 16]:
                role = micro["role"]
                item = (acoustic if role == "acoustic" else replay)[micro["sample_id"]]
                counts[role] += 1
                audio, _ = librosa.load(ROOT / item["audio_path"], sr=16000, mono=True)
                feats = processor(
                    audio, sampling_rate=16000, return_tensors="pt"
                ).input_features.to(device="cuda", dtype=torch.float16)
                feats.requires_grad_(True)
                labels = processor.tokenizer(item["transcript"], return_tensors="pt").input_ids.to(
                    "cuda"
                )
                loss = model(input_features=feats, labels=labels).loss
                if not torch.isfinite(loss):
                    raise FloatingPointError(
                        f"non-finite loss step={step} microbatch={micro['microstep']}"
                    )
                (loss / 16).backward()
                total_loss += float(loss.detach().cpu())
                with progress.open("a", encoding="utf-8") as out:
                    out.write(
                        json.dumps(
                            {
                                "optimizer_step": step,
                                "microbatch_index": micro["microstep"],
                                "sample_id": micro["sample_id"],
                                "source_type": role,
                                "loss": float(loss.detach().cpu()),
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
            grad = float(torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0).detach().cpu())
            optimizer.step()
            scheduler.step()
            torch.cuda.synchronize()
            if {n for n, p in model.named_parameters() if p.requires_grad} != names or any(
                p.requires_grad for n, p in model.named_parameters() if "lora_" not in n
            ):
                raise ValueError(f"trainability changed at step {step}")
            value = total_loss / 16
            losses.append(value)
            driver = gpu_mib()
            item = {
                "optimizer_step": step,
                "loss": value,
                "learning_rate": scheduler.get_last_lr()[0],
                "gradient_norm": grad,
                "step_wall_seconds": time.perf_counter() - step_start,
                "cumulative_wall_seconds": time.perf_counter() - started,
                "peak_cuda_allocated_mib": torch.cuda.max_memory_allocated() / 1024**2,
                "peak_cuda_reserved_mib": torch.cuda.max_memory_reserved() / 1024**2,
                "driver_vram_mib": driver,
                "process_rss_mib": proc.memory_info().rss / 1024**2,
                "acoustic_microbatches": counts["acoustic"],
                "replay_microbatches": counts["clean_replay"],
            }
            with resource.open("a", encoding="utf-8") as out:
                out.write(json.dumps(item) + "\n")
            if item["peak_cuda_reserved_mib"] >= 10000:
                raise RuntimeError(f"reserved VRAM gate failed at step {step}")
            if step % 5 == 0:
                logging.info(
                    "step=%s loss=%.6f acoustic=%s replay=%s",
                    step,
                    value,
                    counts["acoustic"],
                    counts["clean_replay"],
                )
            if step in (50, 100, 150, 200):
                checkpoints.append(
                    checkpoint(
                        model, optimizer, scheduler, step, step * 16, counts, config_hash, inputs
                    )
                )
                validations.append(validate(model, processor, validation, step))
        if counts != {"acoustic": 3200, "clean_replay": 0}:
            raise ValueError(f"final sampler counts mismatch {counts}")
        sampler = {
            "status": "PASSED",
            "total_microbatches": 3200,
            "acoustic_microbatches": counts["acoustic"],
            "replay_microbatches": counts["clean_replay"],
            "ratio_acoustic": counts["acoustic"] / 3200,
            "ratio_clean_replay": counts["clean_replay"] / 3200,
            "schedule_sha256": digest(ROOT / training["data"]["schedule"]),
        }
        save(OUT / "sampler_audit.json", sampler)
        metrics = {
            "status": "PASSED",
            "exit_code": 0,
            "optimizer_steps_completed": 200,
            "total_wall_seconds": time.perf_counter() - started,
            "loss_first": losses[0],
            "loss_last": losses[-1],
            "losses": losses,
            "trainable_parameter_count": count,
            "checkpoint_count": len(checkpoints),
            "checkpoints": checkpoints,
            "validations": validations,
            "peak_cuda_allocated_mib": torch.cuda.max_memory_allocated() / 1024**2,
            "peak_cuda_reserved_mib": torch.cuda.max_memory_reserved() / 1024**2,
            "peak_driver_vram_mib": max(
                (
                    json.loads(x).get("driver_vram_mib") or 0
                    for x in resource.read_text().splitlines()
                ),
                default=None,
            ),
            "process_rss_mib": proc.memory_info().rss / 1024**2,
            "legacy_resume_attempted": False,
        }
        save(OUT / "metrics.json", metrics)
        lockout = {
            "status": "PASSED",
            "input_contract_sha256": {
                p: digest(ROOT / p)
                for p in (
                    "contracts/A4_v2_training_contract.yaml",
                    "contracts/A4_v2_data_manifest.lock.json",
                    "contracts/A4_v2_eval_contract.yaml",
                )
            },
            "outputs_sha256": {
                str(p.relative_to(OUT)).replace("\\", "/"): digest(p)
                for p in [
                    OUT / "config.resolved.json",
                    OUT / "environment.json",
                    progress,
                    OUT / "metrics.json",
                    OUT / "sampler_audit.json",
                    resource,
                ]
            },
            "checkpoints": checkpoints,
        }
        save(OUT / "artifact_lock.json", lockout)
        logging.info("A4_v2 training passed")
        return 0
    except Exception:
        error = traceback.format_exc()
        logging.exception("A4_v2 training blocked")
        save(OUT / "metrics.json", {"status": "BLOCKED_A4_V2_TRAINING", "traceback": error})
        return 1


def smoke() -> int:
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import WhisperForConditionalGeneration, WhisperProcessor, get_scheduler

    smoke_root = ROOT / "runs/A4_v2_resource_smoke"
    training = load(ROOT / "contracts/A4_v2_training_contract.yaml")
    lock = load(ROOT / "contracts/A4_v2_data_manifest.lock.json")
    evaluation = load(ROOT / "contracts/A4_v2_eval_contract.yaml")
    inputs = preflight(training, lock, evaluation)
    rows = {row["sample_id"]: row for row in load(ROOT / training["data"]["train_manifest"])}
    schedule = load(ROOT / training["data"]["schedule"])[:32]
    processor = WhisperProcessor.from_pretrained(
        training["identity"]["base_model"],
        revision=training["identity"]["processor_tokenizer_revision"],
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
    targets = [
        n
        for n, m in base.named_modules()
        if isinstance(m, torch.nn.Linear) and ".decoder." in n and n.endswith(("q_proj", "v_proj"))
    ]
    model = get_peft_model(
        base,
        LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, target_modules=targets, bias="none"),
    )
    trainable = [(n, p) for n, p in model.named_parameters() if p.requires_grad]
    if (
        len(targets) != 16
        or sum(p.numel() for _, p in trainable) != 655360
        or any(".decoder." not in n or "lora_" not in n for n, _ in trainable)
    ):
        raise ValueError("A4 smoke trainability mismatch")
    optimizer = torch.optim.AdamW(
        (p for _, p in trainable), lr=1e-5, betas=(0.9, 0.999), weight_decay=0.01
    )
    scheduler = get_scheduler("linear", optimizer, num_warmup_steps=20, num_training_steps=200)
    torch.cuda.reset_peak_memory_stats()
    losses = []
    progress = []
    import librosa

    for step in range(2):
        optimizer.zero_grad(set_to_none=True)
        total = 0.0
        for micro in schedule[step * 16 : (step + 1) * 16]:
            row = rows[micro["sample_id"]]
            audio, _ = librosa.load(ROOT / row["audio_path"], sr=16000, mono=True)
            f = processor(audio, sampling_rate=16000, return_tensors="pt").input_features.to(
                "cuda", dtype=torch.float16
            )
            labels = processor.tokenizer(row["transcript"], return_tensors="pt").input_ids.to(
                "cuda"
            )
            loss = model(input_features=f, labels=labels).loss
            if not torch.isfinite(loss):
                raise FloatingPointError("non-finite smoke loss")
            (loss / 16).backward()
            total += float(loss.detach().cpu())
            progress.append({"step": step + 1, "microstep": micro["microstep"], "role": "acoustic"})
        optimizer.step()
        scheduler.step()
        losses.append(total / 16)
    adapter = smoke_root / "adapter"
    adapter.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(adapter)
    save(smoke_root / "training_progress.jsonl", progress)
    metrics = {
        "status": "PASSED",
        "exit_code": 0,
        "optimizer_steps_completed": 2,
        "consumed_microbatches": 32,
        "acoustic_microbatches": 32,
        "replay_microbatches": 0,
        "losses": losses,
        "trainable_parameter_count": 655360,
        "peak_cuda_reserved_mib": torch.cuda.max_memory_reserved() / 1024**2,
        "adapter_sha256": digest(adapter / "adapter_model.safetensors"),
    }
    save(smoke_root / "metrics.json", metrics)
    save(
        smoke_root / "artifact_lock.json",
        {
            "inputs": inputs,
            "eval_contract_sha256": digest(ROOT / "contracts/A4_v2_eval_contract.yaml"),
            "adapter_sha256": metrics["adapter_sha256"],
        },
    )
    return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("preflight", "smoke", "full"), default="full")
    mode = parser.parse_args().mode
    if mode == "preflight":
        training = load(ROOT / "contracts/A4_v2_training_contract.yaml")
        lock = load(ROOT / "contracts/A4_v2_data_manifest.lock.json")
        evaluation = load(ROOT / "contracts/A4_v2_eval_contract.yaml")
        print(json.dumps({"status": "PASSED", "inputs": preflight(training, lock, evaluation)}))
    elif mode == "smoke":
        raise SystemExit(smoke())
    else:
        raise SystemExit(main())
