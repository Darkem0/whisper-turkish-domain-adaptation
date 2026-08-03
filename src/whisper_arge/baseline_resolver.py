from __future__ import annotations

import json
from pathlib import Path

from .hashing import sha256_file
from .manifests import read_jsonl


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _prediction_ids(path: Path) -> list[str]:
    return [str(row["sample_id"]) for row in read_jsonl(path)]


def resolve_a0_baseline_predictions(
    manifests: dict[str, Path],
    *,
    project_root: str | Path = ".",
    snapshot_path: str | Path = "runs/a0_v2d_final/immutable_baseline_snapshot_v2d.json",
) -> dict[str, dict]:
    """Resolve A0 predictions by immutable report hashes, never run-folder convention."""
    root = Path(project_root)
    snapshot_file = root / snapshot_path
    snapshot = _load(snapshot_file)
    if not snapshot.get("immutable"):
        raise ValueError("A0 baseline snapshot is not immutable")
    report_ref = snapshot["hashes"]["a0_report"]
    report_path = root / str(report_ref["path"])
    if not report_path.exists() or sha256_file(report_path) != report_ref["sha256"]:
        raise ValueError("immutable A0 report path or SHA-256 mismatch")
    report = _load(report_path)
    expected_hashes = {
        name: str(report["integrity"][name]["prediction_sha256"]) for name in manifests
    }
    candidates: dict[str, list[Path]] = {name: [] for name in manifests}
    for prediction in (root / "runs").rglob("predictions.jsonl"):
        digest = sha256_file(prediction)
        for name, expected in expected_hashes.items():
            if digest == expected:
                candidates[name].append(prediction)
    resolved = {}
    for name, manifest in manifests.items():
        matches = candidates[name]
        if len(matches) != 1:
            raise ValueError(
                f"A0 prediction resolution for {name} expected one SHA match, got {len(matches)}"
            )
        prediction = matches[0]
        expected_ids = {str(row["sample_id"]) for row in read_jsonl(manifest)}
        actual_ids = _prediction_ids(prediction)
        actual_set = set(actual_ids)
        missing = expected_ids - actual_set
        unexpected = actual_set - expected_ids
        duplicates = len(actual_ids) - len(actual_set)
        if missing or unexpected or duplicates:
            raise ValueError(
                f"A0 prediction coverage mismatch for {name}: "
                f"missing={len(missing)} duplicate={duplicates} unexpected={len(unexpected)}"
            )
        resolved[name] = {
            "path": str(prediction),
            "sha256": expected_hashes[name],
            "samples": len(actual_ids),
            "status": "pass",
        }
    return {
        "snapshot": str(snapshot_file),
        "snapshot_sha256": sha256_file(snapshot_file),
        "report": str(report_path),
        "report_sha256": sha256_file(report_path),
        "predictions": resolved,
    }
