from __future__ import annotations

import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from .hashing import sha256_file
from .ledger import append_event, assert_not_run
from .lock import verify_lock
from .manifests import read_jsonl

TRACKED_PACKAGES = (
    "accelerate",
    "datasets",
    "jiwer",
    "librosa",
    "numpy",
    "peft",
    "safetensors",
    "scipy",
    "soundfile",
    "torch",
    "transformers",
)


def assert_recipe_allowed(
    recipe_id: str,
    denylist_path: str | Path = "configs/legacy_denylist.json",
) -> None:
    payload = json.loads(Path(denylist_path).read_text(encoding="utf-8"))
    if recipe_id in payload["blocked_recipe_ids"]:
        raise ValueError(f"recipe is blocked by legacy denylist: {recipe_id}")


def validate_registry_sources(manifest_path: str | Path, registry_path: str | Path) -> None:
    registry = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    sources = {str(item["id"]): item for item in registry["datasets"]}
    used = {
        (str(row["dataset_id"]), str(row["dataset_revision"]))
        for row in read_jsonl(manifest_path)
    }
    for dataset_id, revision in sorted(used):
        if dataset_id not in sources:
            raise ValueError(f"manifest dataset is absent from registry: {dataset_id}")
        source = sources[dataset_id]
        if str(source["revision"]) != revision:
            raise ValueError(
                f"registry revision mismatch for {dataset_id}: "
                f"manifest={revision}, registry={source['revision']}"
            )
        if source.get("archive_sha256") is None and "archive_sha256" in source:
            raise ValueError(f"source archive checksum is unresolved: {dataset_id}")
        if str(source.get("license", "")).startswith("verify_"):
            raise ValueError(f"source license is unresolved: {dataset_id}")


def _command_output(command: list[str]) -> str | None:
    try:
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        ).stdout.strip() or None
    except (OSError, subprocess.TimeoutExpired):
        return None


def capture_environment() -> dict:
    packages: dict[str, str | None] = {}
    for name in TRACKED_PACKAGES:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "python": sys.version,
        "python_executable": sys.executable,
        "packages": packages,
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "nvidia_smi": _command_output(
            [
                "nvidia-smi",
                "--query-gpu=name,driver_version,memory.total",
                "--format=csv,noheader",
            ]
        ),
        "git_commit": _command_output(["git", "rev-parse", "HEAD"]),
        "git_status_porcelain": _command_output(["git", "status", "--porcelain"]),
    }


def reserve_run(
    config_path: str | Path,
    ledger_path: str | Path,
    runs_root: str | Path,
) -> dict:
    config_path = Path(config_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("model") != "openai/whisper-large-v3-turbo":
        raise ValueError("project scope permits only openai/whisper-large-v3-turbo")
    if config.get("dataset_manifest_sha256") == "MATERIALIZE_BEFORE_RUN":
        raise ValueError("dataset manifest must be materialized and hashed before reserving a run")
    assert_recipe_allowed(str(config.get("recipe_id", "")))
    manifest_path = Path(config["dataset_manifest"])
    actual_manifest_hash = sha256_file(manifest_path)
    if actual_manifest_hash != config["dataset_manifest_sha256"]:
        raise ValueError("dataset manifest hash does not match config")
    validate_registry_sources(manifest_path, config.get("dataset_registry", "data/registry.json"))
    lock_errors = verify_lock(config["evaluation_lock"])
    if lock_errors:
        raise ValueError("evaluation lock invalid: " + "; ".join(lock_errors))
    actual_lock_hash = sha256_file(config["evaluation_lock"])
    if actual_lock_hash != config["evaluation_lock_sha256"]:
        raise ValueError("evaluation lock file hash does not match config")
    acceptance_lock_path = config.get("acceptance_lock")
    if not acceptance_lock_path:
        raise ValueError("v2 training requires an acceptance lock")
    acceptance_errors = verify_lock(acceptance_lock_path)
    if acceptance_errors:
        raise ValueError("acceptance lock invalid: " + "; ".join(acceptance_errors))
    acceptance_payload = json.loads(Path(acceptance_lock_path).read_text(encoding="utf-8"))
    if acceptance_payload.get("lock_status") != "finalized":
        raise ValueError("acceptance lock must be finalized before training")
    if sha256_file(acceptance_lock_path) != config.get("acceptance_lock_sha256"):
        raise ValueError("acceptance lock file hash does not match config")

    signature = assert_not_run(config, ledger_path)
    run_id = f"{config.get('experiment_id', 'EXP')}-{signature[:12]}"
    run_dir = Path(runs_root) / run_id
    if run_dir.exists():
        raise ValueError(f"run directory already exists: {run_dir}")
    run_dir.mkdir(parents=True)
    (run_dir / "config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    environment = capture_environment()
    (run_dir / "environment.json").write_text(
        json.dumps(environment, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    event = {
        "event": "reserved",
        "status": "reserved",
        "experiment_id": config.get("experiment_id"),
        "run_id": run_id,
        "signature": signature,
        "config_sha256": sha256_file(run_dir / "config.json"),
        "dataset_manifest_sha256": actual_manifest_hash,
        "evaluation_lock_sha256": actual_lock_hash,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    append_event(ledger_path, event)
    return event
