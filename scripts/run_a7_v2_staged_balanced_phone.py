"""A7 parent-adapter continuation with registered on-the-fly augmentation."""

from __future__ import annotations
import argparse
import hashlib
import json
import os
import random
import shutil
import time
from pathlib import Path
import librosa
import numpy as np
import psutil
import torch
from peft import PeftModel
from transformers import WhisperForConditionalGeneration, WhisperProcessor, get_scheduler
from whisper_arge.a7_augmentation import apply

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "runs/A7_v2_resource_smoke_peak_guard_v3"
RUN = ROOT / "runs/A7_v2_staged_balanced_phone_200"
TP = ROOT / "contracts/A7_v2_training_contract.yaml"
DP = ROOT / "contracts/A7_v2_data_manifest.lock.json"
EP = ROOT / "contracts/A7_v2_eval_contract.yaml"
STATE_PATH = ROOT / "state/a7_v2_training_state.json"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def resolve_adapter_model_file(adapter_dir: Path) -> Path:
    candidates = [
        adapter_dir / "adapter_model.safetensors",
        adapter_dir / "adapter_model.bin",
    ]
    existing = [path for path in candidates if path.is_file()]
    if len(existing) != 1:
        raise RuntimeError(
            f"Expected exactly one adapter model file in {adapter_dir}, found: {existing}"
        )
    return existing[0]


def load(p):
    return json.loads(Path(p).read_text(encoding="utf8"))


def save(p, v):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(v, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


def lines(p):
    return [json.loads(x) for x in Path(p).read_text(encoding="utf8").splitlines() if x]


def checkpoint_is_complete(cp, step):
    """Accept only a checkpoint with explicit global schedule provenance."""
    lock_path = cp / "checkpoint_lock.json"
    adapter = cp / "adapter" / "adapter_model.safetensors"
    if not lock_path.is_file() or not adapter.is_file() or adapter.stat().st_size == 0:
        return False
    try:
        lock = load(lock_path)
    except (OSError, json.JSONDecodeError):
        return False
    return (
        lock.get("global_optimizer_step", lock.get("optimizer_step", lock.get("step")))
        == step
        and lock.get("completed_microbatches") == step * 16
        and lock.get("next_schedule_index") == step * 16
        and lock.get("adapter_sha256") == sha(adapter)
    )


def setstate(s, **x):
    save(STATE_PATH, {"status": s, "pid": os.getpid(), **x})


def preflight():
    t, d = load(TP), load(DP)
    load(EP)
    sl = load(ROOT / t["data"]["schedule_lock"])
    sch = ROOT / t["data"]["schedule"]
    parent = ROOT / t["initialization"]["parent_adapter"] / "adapter_model.safetensors"
    checks = {
        "training": sha(TP),
        "data": sha(DP),
        "evaluation": sha(EP),
        "schedule": sha(sch),
        "implementation": sha(ROOT / "src/whisper_arge/a7_augmentation.py"),
        "parent": sha(parent),
    }
    if checks["parent"] != t["initialization"]["parent_adapter_sha256"]:
        raise ValueError("BLOCKED_A7_PARENT_ADAPTER")
    if (
        checks["schedule"] != d["schedule"]["sha256"]
        or checks["schedule"] != sl["schedule_sha256"]
        or sl["schedule_rows"] != 3200
    ):
        raise ValueError("BLOCKED_A7_CONTRACT_MATERIALIZATION")
    if sl["bucket_counts"] != {
        "tsc_anchor_unchanged": 1067,
        "phone_like_unchanged": 640,
        "phone_band": 640,
        "speed_075": 320,
        "noise_gain": 267,
        "phone_band_noise_gain": 266,
    }:
        raise ValueError("BLOCKED_A7_CONTRACT_MATERIALIZATION bucket counts")
    return t, checks


def build(t, resume_adapter=None):
    pr = WhisperProcessor.from_pretrained(
        t["identity"]["base_model"],
        revision=t["identity"]["tokenizer_processor_revision"],
        local_files_only=True,
    )
    base = WhisperForConditionalGeneration.from_pretrained(
        t["identity"]["base_model"],
        revision=t["identity"]["base_model_revision"],
        torch_dtype=torch.float16,
        local_files_only=True,
    ).to("cuda")
    base.config.use_cache = False
    base.gradient_checkpointing_enable()
    adapter = resume_adapter or (ROOT / t["initialization"]["parent_adapter"])
    m = PeftModel.from_pretrained(base, str(adapter), is_trainable=True)
    names = []
    for n, p in m.named_parameters():
        p.requires_grad_("lora_" in n)
        names += [n] if p.requires_grad else []
    if len(names) != 160 or any(
        "lora_" not in n
        or not ("encoder" in n or "decoder" in n)
        or not ("q_proj" in n or "v_proj" in n)
        for n in names
    ):
        raise ValueError("A7 LoRA scope")
    return pr, m, names


def batch(pr, entry, data):
    audio, _ = librosa.load(ROOT / data["audio_path"], sr=16000, mono=True)
    audio, params = apply(audio, entry["augmentation_bucket"], entry["deterministic_seed"])
    f = pr(audio, sampling_rate=16000, return_tensors="pt").input_features.to(
        "cuda", dtype=torch.float16
    )
    f.requires_grad_(True)
    y = pr.tokenizer(data["transcript"], return_tensors="pt").input_ids.to("cuda")
    return f, y, params


def execute(
    smoke, resume_step=0, schedule_resume_step=0, run_root=RUN, source_adapter=None
):
    print("A7_CONFIG_LOADED", flush=True)
    t, checks = preflight()
    out = SMOKE if smoke else run_root
    out.mkdir(parents=True, exist_ok=True)
    schedule = lines(ROOT / t["data"]["schedule"])
    data = {x["sample_id"]: x for x in lines(ROOT / t["data"]["train_manifest"])}
    selected = schedule
    if smoke:
        chosen = {}
        for x in schedule:
            chosen.setdefault(x["augmentation_bucket"], x)
        selected = (
            list(chosen.values())
            + [x for x in schedule if x not in chosen.values()][: 32 - len(chosen)]
        )
        resume_step = 0
        schedule_resume_step = 0
    elif schedule_resume_step:
        selected = schedule[schedule_resume_step * 16 :]
        if len(selected) != (200 - schedule_resume_step) * 16:
            raise ValueError("A7 resume schedule position is invalid")
    random.seed(20260730)
    np.random.seed(20260730)
    torch.manual_seed(20260730)
    torch.cuda.manual_seed_all(20260730)
    print("A7_PARENT_LOADING", flush=True)
    resume_adapter = None
    resume_adapter_model = None
    source_adapter_config_sha256 = None
    if not smoke and resume_step:
        resume_adapter = source_adapter or (
            RUN / "checkpoints" / f"step-{resume_step:03d}" / "adapter"
        )
        resume_adapter_model = resolve_adapter_model_file(resume_adapter)
        config = resume_adapter / "adapter_config.json"
        if not config.is_file():
            raise RuntimeError(f"A7 resume adapter config missing: {config}")
        source_adapter_config_sha256 = sha(config)
        source_lock = resume_adapter.parent / "checkpoint_lock.json"
        if not source_lock.is_file():
            raise RuntimeError(f"A7 source checkpoint lock missing: {source_lock}")
        source_lock_data = load(source_lock)
        if source_lock_data.get("adapter_sha256") != sha(resume_adapter_model):
            raise RuntimeError("A7 source checkpoint adapter SHA-256 mismatch")
    pr, m, names = build(t, resume_adapter=resume_adapter)
    print("A7_PARENT_LOADED", flush=True)
    print("A7_DATASET_LOADING", flush=True)
    train = [p for p in m.parameters() if p.requires_grad]
    count = sum(p.numel() for p in train)
    if count != 3276800:
        raise ValueError(f"A7 trainable count={count}")
    print("A7_DATALOADER_READY", flush=True)
    opt = torch.optim.AdamW(train, lr=5e-6)
    remaining_steps = len(selected) // 16
    # Adapter-only continuation has no optimizer/scheduler state, but its LR
    # must remain on the original 200-step global linear schedule.
    sched = get_scheduler(
        "linear", opt, num_warmup_steps=20, num_training_steps=200
    )
    if resume_step:
        sched.step(schedule_resume_step)
    m.train()
    torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    progress_path = out / "training_progress.jsonl"
    progress = [] if smoke or resume_step else lines(progress_path)
    losses = []
    grads = {"encoder": 0.0, "decoder": 0.0}
    for step in range(remaining_steps):
        global_step = schedule_resume_step + step + 1
        opt.zero_grad(set_to_none=True)
        total = 0.0
        for entry in selected[step * 16 : (step + 1) * 16]:
            if not progress:
                print("A7_FIRST_MICROBATCH_START", flush=True)
            f, y, _ = batch(pr, entry, data[entry["sample_id"]])
            loss = m(input_features=f, labels=y).loss
            if not torch.isfinite(loss):
                raise ValueError("NaN/Inf")
            (loss / 16).backward()
            if not progress:
                print("A7_FIRST_BACKWARD_COMPLETE", flush=True)
                if os.environ.get("A7_STOP_AFTER_FIRST_BACKWARD") == "1":
                    raise RuntimeError("A7_CONTROLLED_STOP_AFTER_FIRST_BACKWARD")
            total += float(loss.detach().cpu())
            progress.append(
                {
                    "optimizer_step": global_step,
                    "schedule_index": entry["schedule_index"] + 1,
                    "sample_id": entry["sample_id"],
                    "source": entry["source"],
                    "augmentation_bucket": entry["augmentation_bucket"],
                    "loss": float(loss.detach().cpu()),
                    "resumed_from_checkpoint": resume_step or None,
                    "remaining_steps_at_start": remaining_steps,
                }
            )
        for n, p in m.named_parameters():
            if p.requires_grad and p.grad is not None:
                grads["encoder" if "encoder" in n else "decoder"] += float(
                    p.grad.abs().sum().detach().cpu()
                )
        if not all(grads.values()):
            raise ValueError("missing encoder/decoder gradient")
        opt.step()
        sched.step()
        losses.append(total / 16)
        if not smoke and global_step in (175, 200):
            checkpoint_name = (
                "recovery-step-175" if global_step == 175 else "step-200"
            )
            cp = out / "checkpoints" / checkpoint_name
            write_checkpoint = True
            if cp.exists():
                if not checkpoint_is_complete(cp, global_step):
                    stale = cp.parent / (
                        f"stale_step-{global_step:03d}_preexisting_{int(time.time())}"
                    )
                    shutil.move(str(cp), str(stale))
                else:
                    write_checkpoint = False
            if write_checkpoint:
                tmp = cp.parent / f".step-{global_step:03d}.tmp-{os.getpid()}"
                if tmp.exists():
                    raise ValueError(f"A7 checkpoint temp path already exists: {tmp}")
                m.save_pretrained(tmp / "adapter")
                save(
                    tmp / "checkpoint_lock.json",
                    {
                        "step": global_step,
                        "global_optimizer_step": global_step,
                        "optimizer_step": global_step,
                        "completed_microbatches": global_step * 16,
                        "schedule_index": global_step * 16,
                        "next_schedule_index": global_step * 16,
                        "last_schedule_index": global_step * 16 - 1,
                        "resumed_from_checkpoint": resume_step or None,
                        "resume_mode": (
                            "ADAPTER_CONTINUATION_WITH_OPTIMIZER_RESET"
                            if resume_step else "FRESH"
                        ),
                        "gradient_scaler_state": "RESET",
                        "source_adapter_sha256": sha(resume_adapter_model)
                        if resume_adapter_model
                        else None,
                        "source_adapter_config_sha256": source_adapter_config_sha256,
                        "adapter_sha256": sha(tmp / "adapter/adapter_model.safetensors"),
                        "inputs": checks,
                    },
                )
                if not checkpoint_is_complete(tmp, global_step):
                    raise ValueError(f"A7 incomplete temporary checkpoint: {tmp}")
                tmp.replace(cp)
        if not smoke:
            progress_path.write_text(
                "".join(json.dumps(x) + "\n" for x in progress), encoding="utf8"
            )
            setstate(
                "RUNNING",
                mode="full",
                worker_alive=True,
                resumed_from_step=resume_step,
                resume_mode="ADAPTER_CONTINUATION_WITH_OPTIMIZER_RESET",
                optimizer_steps_completed=global_step,
                microbatches_completed=global_step * 16,
                next_schedule_index=global_step * 16,
                training_started=True,
                checkpoint_created=global_step >= 175,
            )
    progress_path.write_text(
        "".join(json.dumps(x) + "\n" for x in progress), encoding="utf8"
    )
    m.save_pretrained(out / "adapter")
    ah = sha(out / "adapter/adapter_model.safetensors")
    metrics = {
        "status": "PASSED",
        "exit_code": 0,
        "optimizer_steps_completed": schedule_resume_step + remaining_steps,
        "consumed_microbatches": (schedule_resume_step + remaining_steps) * 16,
        "losses": losses,
        "trainable_parameter_count": count,
        "gradient_scope_l1": grads,
        "peak_cuda_reserved_mib": torch.cuda.max_memory_reserved() / 1024**2,
        "peak_cuda_allocated_mib": torch.cuda.max_memory_allocated() / 1024**2,
        "process_rss_mib": psutil.Process().memory_info().rss / 1024**2,
        "adapter_sha256": ah,
        "parent_adapter_sha256": checks["parent"],
        "wall_seconds": time.perf_counter() - started,
    }
    if metrics["peak_cuda_reserved_mib"] >= 10000:
        raise ValueError("VRAM gate")
    save(out / "metrics.json", metrics)
    save(
        out / "config.resolved.json",
        {
            "contract": t,
            "input_hashes": checks,
            "parent_adapter_loaded": True,
            "new_random_adapter": False,
            "resume_mode": (
                "ADAPTER_CONTINUATION_WITH_OPTIMIZER_RESET" if resume_step else "FRESH"
            ),
            "resumed_from_step": resume_step,
            "schedule_resume_step": schedule_resume_step,
        },
    )
    save(
        out / "artifact_lock.json",
        {"inputs": checks, "adapter_sha256": ah, "metrics_sha256": sha(out / "metrics.json")},
    )


def main():
    global STATE_PATH
    print("A7_BOOT", flush=True)
    a = argparse.ArgumentParser()
    a.add_argument("--mode", choices=("preflight", "smoke", "full"), default="smoke")
    a.add_argument("--resume-step", type=int, default=0)
    a.add_argument("--schedule-resume-step", type=int, default=0)
    a.add_argument("--run-root", type=Path, default=RUN)
    a.add_argument("--source-adapter", type=Path)
    a.add_argument("--state-path", type=Path, default=STATE_PATH)
    args = a.parse_args()
    STATE_PATH = args.state_path
    mode = args.mode
    if mode == "preflight":
        print(json.dumps({"status": "PASSED", "inputs": preflight()[1]}))
        return
    if mode == "full" and args.resume_step:
        if args.resume_step not in (50, 100, 150):
            raise SystemExit("--resume-step must name an existing A7 checkpoint")
        if not (args.resume_step <= args.schedule_resume_step < 200):
            raise SystemExit("--schedule-resume-step must be >= --resume-step and < 200")
        resume_mode = "ADAPTER_CONTINUATION_WITH_OPTIMIZER_RESET"
    else:
        resume_mode = "FRESH"
    setstate(
        "RUNNING", mode=mode, worker_alive=True,
        resumed_from_step=args.resume_step,
        schedule_resume_step=args.schedule_resume_step,
        resume_mode=resume_mode,
        optimizer_steps_completed=args.schedule_resume_step,
        microbatches_completed=args.schedule_resume_step * 16,
        training_started=mode == "full", checkpoint_created=bool(args.resume_step),
    )
    try:
        execute(
            mode == "smoke",
            args.resume_step,
            args.schedule_resume_step,
            args.run_root,
            args.source_adapter,
        )
        setstate(
            "READY_FOR_A7_V2_FULL_TRAINING" if mode == "smoke" else "COMPLETED",
            mode=mode,
            worker_alive=False,
            resumed_from_step=args.resume_step,
            resume_mode=resume_mode,
            optimizer_steps_completed=200 if mode == "full" else 2,
            microbatches_completed=3200 if mode == "full" else 32,
            next_schedule_index=3200 if mode == "full" else 32,
            training_started=True,
            checkpoint_created=True,
        )
    except BaseException as e:
        import traceback
        traceback.print_exc()
        before_first = not (RUN / "training_progress.jsonl").exists()
        setstate(
            "EXITED_BEFORE_FIRST_MICROBATCH" if before_first else ("BLOCKED_A7_RESOURCE_SMOKE" if mode == "smoke" else "BLOCKED_A7_CONTRACT_MATERIALIZATION"),
            error=str(e),
            worker_alive=False,
            optimizer_steps_completed=0,
            microbatches_completed=0,
            training_started=False,
            checkpoint_created=False,
        )
        raise SystemExit(2 if before_first else 1)


if __name__ == "__main__":
    main()
