"""Authorized fresh-base A3_v2 200-step training with locked local validation."""

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
OUT = ROOT / "runs" / "A3_v2_fresh_base_200"


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
    if training["status"] != "READY_FOR_A3_V2_RESOURCE_SMOKE":
        raise ValueError("training contract not smoke-passed authorization state")
    init = training["initialization"]
    if (
        init["initialization_mode"] != "fresh_base"
        or init["parent_adapter"] is not None
        or init["parent_weights_loaded"]
    ):
        raise ValueError("fresh-base initialization contract mismatch")
    if init["legacy_resume"] != "FORBIDDEN: A3_legacy_aborted_step34_invalid":
        raise ValueError("legacy-resume prohibition mismatch")
    checked = {}
    for name, key in (
        ("train_manifest", "train_manifest_sha256"),
        ("validation_manifest", "validation_manifest_sha256"),
        ("replay_manifest", "replay_manifest_sha256"),
        ("sampler_schedule", "sampler_schedule_sha256"),
    ):
        p = ROOT / training["data"][name]
        if digest(p) != training["data"][key]:
            raise ValueError(f"input hash mismatch: {p}")
        checked[str(p.relative_to(ROOT)).replace("\\", "/")] = digest(p)
    for item in lock["a3_manifests"].values():
        if digest(ROOT / item["path"]) != item["sha256"]:
            raise ValueError(f"manifest lock mismatch: {item['path']}")
    if (
        digest(ROOT / lock["deterministic_sampler"]["path"])
        != lock["deterministic_sampler"]["sha256"]
    ):
        raise ValueError("sampler lock mismatch")
    for rel, expected in lock["peer_contract_sha256"].items():
        if digest(ROOT / rel) != expected:
            raise ValueError(f"peer contract hash mismatch: {rel}")
    for item in (
        evaluation["evaluation_lock"],
        evaluation["acceptance_lock"],
        evaluation["immutable_registry"],
    ):
        if digest(ROOT / item["path"]) != item["sha256"]:
            raise ValueError(f"frozen input hash mismatch: {item['path']}")
    env = training["environment_lock"]
    for package in ("transformers", "peft", "accelerate"):
        if importlib.metadata.version(package) != env[package]:
            raise ValueError(f"package mismatch: {package}")
    if torch.__version__ != env["torch"] or torch.version.cuda != env["cuda"]:
        raise ValueError("torch/CUDA mismatch")
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
        "resume_policy": "only this verified A3_v2 run; never legacy A3 step 34",
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
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError(f"refusing to overwrite existing run: {OUT}")
    OUT.mkdir(parents=True)
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
        training = load(ROOT / "contracts/A3_v2_training_contract.yaml")
        lock = load(ROOT / "contracts/A3_v2_data_manifest.lock.json")
        evaluation = load(ROOT / "contracts/A3_v2_eval_contract.yaml")
        inputs = preflight(training, lock, evaluation)
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA unavailable")
        random.seed(42)
        np.random.seed(42)
        torch.manual_seed(42)
        torch.cuda.manual_seed_all(42)
        schedule = load(ROOT / training["data"]["sampler_schedule"])
        if (
            len(schedule) != 3200
            or sum(x["role"] == "acoustic" for x in schedule) != 2880
            or sum(x["role"] == "clean_replay" for x in schedule) != 320
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
            "condition": "A3_v2_fresh_base_200",
            "initialization_mode": "fresh_base",
            "parent_adapter": None,
            "parent_weights_loaded": False,
            "legacy_resume_attempted": False,
            "steps": 200,
            "microbatches": 3200,
            "seed": 42,
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
            and ".encoder." in n
            and n.endswith(("q_proj", "v_proj"))
        ]
        if len(targets) != 64:
            raise ValueError(f"unexpected target count {len(targets)}")
        model = get_peft_model(
            model,
            LoraConfig(r=16, lora_alpha=32, target_modules=targets, lora_dropout=0.05, bias="none"),
        )
        trainable = [(n, p) for n, p in model.named_parameters() if p.requires_grad]
        names = {n for n, _ in trainable}
        count = sum(p.numel() for _, p in trainable)
        if count != 2621440 or any("lora_" not in n or ".encoder." not in n for n in names):
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
        if counts != {"acoustic": 2880, "clean_replay": 320}:
            raise ValueError(f"final sampler counts mismatch {counts}")
        sampler = {
            "status": "PASSED",
            "total_microbatches": 3200,
            "acoustic_microbatches": counts["acoustic"],
            "replay_microbatches": counts["clean_replay"],
            "ratio_acoustic": counts["acoustic"] / 3200,
            "ratio_clean_replay": counts["clean_replay"] / 3200,
            "schedule_sha256": digest(ROOT / training["data"]["sampler_schedule"]),
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
                    "contracts/A3_v2_training_contract.yaml",
                    "contracts/A3_v2_data_manifest.lock.json",
                    "contracts/A3_v2_eval_contract.yaml",
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
        logging.info("A3_v2 training passed")
        return 0
    except Exception:
        error = traceback.format_exc()
        logging.exception("A3_v2 training blocked")
        save(OUT / "metrics.json", {"status": "BLOCKED_A3_V2_TRAINING", "traceback": error})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
