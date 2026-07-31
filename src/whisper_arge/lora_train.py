from __future__ import annotations

import json
import random
import subprocess
import threading
import time
from pathlib import Path

import librosa
import numpy as np
import torch
from peft import LoraConfig, get_peft_model
from transformers import WhisperForConditionalGeneration, WhisperProcessor, get_scheduler

from .hashing import sha256_file
from .manifests import read_jsonl


MODEL = "openai/whisper-large-v3-turbo"
REVISION = "41f01f3fe87f28c78e2fbf8b568835947dd65ed9"


def _set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def _targets(model: torch.nn.Module, condition: str) -> list[str]:
    names = [name for name, module in model.named_modules() if isinstance(module, torch.nn.Linear)]
    qv = [name for name in names if name.endswith(("q_proj", "v_proj"))]
    if condition in {"A1", "A2"}:
        return qv
    if condition == "A3":
        return [name for name in qv if ".encoder." in name]
    if condition == "A6":
        chosen = []
        for name in qv:
            if ".decoder." in name:
                chosen.append(name)
            elif ".encoder.layers." in name:
                layer = int(name.split(".encoder.layers.", 1)[1].split(".", 1)[0])
                if layer >= 26:
                    chosen.append(name)
        return chosen
    raise ValueError(f"unsupported condition: {condition}")


def run_lora_steps(
    condition: str,
    output_root: str | Path,
    *,
    steps: int,
    technical_smoke: bool = False,
    gpu_telemetry: bool = False,
    seed: int = 20260730,
) -> dict:
    if condition not in {"A1", "A2", "A3", "A6"}:
        raise ValueError("condition must be A1, A2, A3, or A6")
    if technical_smoke and steps != 2:
        raise ValueError("technical smoke is exactly two optimizer steps")
    contract_path = Path("data/materialized/training_v2d/training_contract_v2d.json")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    schedule = list(read_jsonl(contract["schedule"]["path"]))
    needed = steps * int(contract["gradient_accumulation_steps"])
    if needed > len(schedule):
        raise ValueError("schedule is shorter than requested training steps")
    rows = {row["stable_id"]: row for row in read_jsonl(contract["target_manifest"])}
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    progress_path = root / "training_progress.json"
    _set_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    processor = WhisperProcessor.from_pretrained(MODEL, revision=REVISION)
    model = WhisperForConditionalGeneration.from_pretrained(
        MODEL, revision=REVISION, torch_dtype=torch.float16
    ).to(device)
    model.config.use_cache = False
    model.gradient_checkpointing_enable()
    rank = 8 if condition == "A1" else 16
    targets = _targets(model, condition)
    if not targets:
        raise ValueError("no LoRA target modules resolved")
    model = get_peft_model(
        model,
        LoraConfig(
            r=rank,
            lora_alpha=32,
            target_modules=targets,
            lora_dropout=0.05,
            bias="none",
        ),
    )
    optimizer = torch.optim.AdamW(
        (parameter for parameter in model.parameters() if parameter.requires_grad),
        lr=1e-5,
        betas=(0.9, 0.999),
        weight_decay=0.01,
    )
    scheduler = get_scheduler("linear", optimizer, num_warmup_steps=20, num_training_steps=steps)
    accumulation = int(contract["gradient_accumulation_steps"])
    model.train()
    torch.cuda.reset_peak_memory_stats()
    losses, grad_norms = [], []
    telemetry_samples: list[dict] = []
    telemetry_stop = threading.Event()

    def collect_gpu_telemetry() -> None:
        """Passive driver polling; failure never affects training."""
        while not telemetry_stop.is_set():
            try:
                result = subprocess.run(
                    [
                        "nvidia-smi",
                        "--query-gpu=timestamp,memory.used",
                        "--format=csv,noheader,nounits",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                fields = [value.strip() for value in result.stdout.strip().split(",")]
                if len(fields) == 2 and fields[1].isdigit():
                    telemetry_samples.append(
                        {"timestamp": fields[0], "memory_used_mib": int(fields[1])}
                    )
            except (OSError, subprocess.SubprocessError):
                telemetry_samples.append({"status": "nvidia_smi_unavailable_or_permission_denied"})
            telemetry_stop.wait(1.0)

    telemetry_thread = (
        threading.Thread(target=collect_gpu_telemetry, daemon=True) if gpu_telemetry else None
    )
    if telemetry_thread:
        telemetry_thread.start()
    begin = time.monotonic()
    try:
        for step in range(steps):
            optimizer.zero_grad(set_to_none=True)
            running_loss = 0.0
            for offset in range(accumulation):
                item = rows[schedule[step * accumulation + offset]["stable_id"]]
                audio, _ = librosa.load(item["audio_path"], sr=16000, mono=True)
                features = processor(
                    audio, sampling_rate=16000, return_tensors="pt"
                ).input_features.to(device=device, dtype=torch.float16)
                features.requires_grad_(True)
                labels = processor.tokenizer(item["transcript"], return_tensors="pt").input_ids.to(
                    device
                )
                loss = model(input_features=features, labels=labels).loss
                if not torch.isfinite(loss):
                    raise FloatingPointError(f"non-finite loss at step {step}")
                (loss / accumulation).backward()
                running_loss += float(loss.detach().cpu())
            grad_norm = float(
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0).detach().cpu()
            )
            optimizer.step()
            scheduler.step()
            losses.append(running_loss / accumulation)
            grad_norms.append(grad_norm)
            progress_path.write_text(
                json.dumps(
                    {
                        "condition": condition,
                        "completed": False,
                        "optimizer_steps_completed": step + 1,
                        "optimizer_steps_total": steps,
                        "schedule_sha256": contract["schedule"]["sha256"],
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
    finally:
        telemetry_stop.set()
        if telemetry_thread:
            telemetry_thread.join(timeout=6)
    adapter = root / "adapter"
    model.save_pretrained(adapter)
    result = {
        "condition": condition,
        "technical_smoke": technical_smoke,
        "steps": steps,
        "loss": losses,
        "gradient_norm": grad_norms,
        "wall_seconds": time.monotonic() - begin,
        "peak_vram_bytes": int(torch.cuda.max_memory_allocated()),
        "peak_vram_reserved_bytes": int(torch.cuda.max_memory_reserved()),
        "gpu_telemetry": {
            "enabled": gpu_telemetry,
            "interval_seconds": 1.0 if gpu_telemetry else None,
            "samples": telemetry_samples,
            "peak_memory_used_mib": max(
                (
                    sample["memory_used_mib"]
                    for sample in telemetry_samples
                    if "memory_used_mib" in sample
                ),
                default=None,
            ),
            "process_level_gpu_memory": "not_available_when_nvidia_smi_process_query_returns_N_A",
        },
        "adapter": str(adapter),
        "adapter_sha256": sha256_file(adapter / "adapter_model.safetensors"),
        "target_modules": targets,
        "rank": rank,
        "schedule_sha256": contract["schedule"]["sha256"],
    }
    progress_path.write_text(
        json.dumps(
            {
                "condition": condition,
                "completed": True,
                "optimizer_steps_completed": steps,
                "optimizer_steps_total": steps,
                "schedule_sha256": contract["schedule"]["sha256"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "training_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result
