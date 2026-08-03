# ruff: noqa
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"
REPORTS = ROOT / "reports"
RUNS = ROOT / "runs"
EVAL_FILES = [ROOT / "evaluation" / "suite_v2d.json", ROOT / "evaluation" / "EVAL_LOCK_v2d.json"]
TERMINAL = {"PASSED", "FAILED", "BLOCKED"}


def now() -> str:
    return datetime.now(UTC).isoformat()


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def read(path: Path, default: Any) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def event(kind: str, **data: Any) -> None:
    STATE.mkdir(exist_ok=True)
    with (STATE / "events.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"timestamp": now(), "kind": kind, **data}, ensure_ascii=False) + "\n")


def git_commit() -> str | None:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True)
    return result.stdout.strip() if result.returncode == 0 else None


def gpu() -> dict[str, Any]:
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"], text=True, capture_output=True, timeout=10)
        vals = [x.strip() for x in r.stdout.splitlines()[0].split(",")]
        return {"utilization_percent": int(vals[0]), "vram_used_mb": int(vals[1]), "vram_total_mb": int(vals[2])}
    except Exception:
        return {"utilization_percent": None, "vram_used_mb": None, "vram_total_mb": None}


def environment() -> dict[str, Any]:
    torch_info: dict[str, Any] = {"available": False}
    try:
        import torch
        torch_info = {"available": True, "version": torch.__version__, "cuda": torch.cuda.is_available(), "cuda_version": torch.version.cuda, "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}
    except Exception as exc:
        torch_info["error"] = str(exc)
    return {"timestamp": now(), "python": sys.version, "platform": platform.platform(), "torch": torch_info, "gpu": gpu(), "git_commit": git_commit()}


def default_queue() -> list[dict[str, Any]]:
    profiles = ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7"]
    q = [{"id": "P0_artifact_audit", "phase": "P0", "main_variable": "inventory", "status": "PENDING"}, {"id": "P1_immutable_lock", "phase": "P1", "main_variable": "evaluation_integrity", "status": "PENDING"}]
    q += [{"id": p, "phase": "P2", "parent": "D0", "main_variable": "decode_profile", "status": "PENDING"} for p in profiles]
    q += [{"id": x, "phase": p, "main_variable": "prototype", "status": "PENDING"} for x, p in [("P3_quality", "P3"), ("P4_second_pass", "P4"), ("P5_itn", "P5"), ("P6_nbest", "P6"), ("P7_memory", "P7"), ("A3_v2", "P8"), ("A4_v2", "P9"), ("A5_v2", "P10"), ("A6_v2", "P11")]]
    return q


def status(current: dict[str, Any] | None = None, error: str | None = None) -> None:
    queue = read(STATE / "experiment_queue.json", [])
    completed = sum(x.get("status") == "PASSED" for x in queue)
    available = [x for x in queue if x["id"] not in {"A3_v2", "A4_v2", "A5_v2", "A6_v2"}]
    adone = sum(x.get("status") == "PASSED" for x in available)
    latest_error = error or next((x.get("error") for x in reversed(queue) if x.get("error")), None)
    body = {"timestamp": now(), "current_experiment": current, "completed": completed, "total": len(queue), "available_scope_percent": round(100 * adone / max(1, len(available))), "full_roadmap_percent": round(100 * completed / max(1, len(queue))), "gpu": gpu(), "last_error": latest_error, "heartbeat_seconds": 0}
    write(STATE / "latest_status.json", body)
    (STATE / "latest_status.txt").write_text(f"[{body['available_scope_percent']}% available | {body['full_roadmap_percent']}% full]\n{(current or {}).get('id', 'IDLE')}\nGPU {body['gpu']['utilization_percent']}% VRAM {body['gpu']['vram_used_mb']}/{body['gpu']['vram_total_mb']} MB\n", encoding="utf-8")
    write(STATE / "heartbeat.json", {"timestamp": now(), "pid": os.getpid(), "current": current})


def immutable_registry() -> dict[str, Any]:
    entries = []
    for path in EVAL_FILES + [ROOT / "src" / "whisper_arge" / "normalization.py", ROOT / "src" / "whisper_arge" / "metrics_v2.py"]:
        entries.append({"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(path) if path.exists() else "MISSING"})
    return {"schema_version": 1, "created_at": now(), "entries": entries, "rule": "Supervisor verifies these before every experiment; experiments do not write evaluation inputs."}


def profile(name: str) -> dict[str, Any]:
    base = read(ROOT / "evaluation" / "suite_v2d.json", {})["decode_contract"].copy()
    variants = {"D0": {}, "D1": {"num_beams": 1, "do_sample": False}, "D2": {"num_beams": 3, "do_sample": False}, "D3": {"num_beams": 5, "do_sample": False}, "D4": {"condition_on_prev_tokens": False}, "D5": {"condition_on_prev_tokens": True}, "D6": {"temperature": [0.0, 0.2, 0.4, 0.6], "compression_ratio_threshold": 1.35, "logprob_threshold": -1.0}, "D7": {"no_speech_profile": "alternative_must_be_calibrated_from_quality_data"}}
    base.update(variants[name]); return base


def gate_registry() -> str:
    return """domain_robustness:\n  delta_vs_a0_max: -0.010\n  bootstrap_ci_upper_must_be_below_zero: true\nfleurs:\n  maximum_absolute_regression: 0.005\ncommon_voice_scripted:\n  maximum_absolute_regression: 0.005\nhallucination:\n  maximum_relative_increase: 0.20\nrepetition:\n  maximum_relative_increase: 0.20\nreproducibility:\n  minimum_passing_seeds: 2\n  total_seeds: 3\n"""
