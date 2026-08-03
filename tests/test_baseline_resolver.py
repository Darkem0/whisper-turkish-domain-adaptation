from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from whisper_arge.baseline_resolver import resolve_a0_baseline_predictions


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _baseline_tree(tmp_path: Path) -> dict[str, Path]:
    manifest = tmp_path / "manifest.jsonl"
    _jsonl(manifest, [{"sample_id": "cvsp-1"}])
    prediction = tmp_path / "runs/a0_v2d_smoke/cv_spontaneous/predictions.jsonl"
    _jsonl(prediction, [{"sample_id": "cvsp-1", "prediction": "test"}])
    report = tmp_path / "runs/a0_v2d_final/a0_baseline_report_v2d.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps({"integrity": {"cv_spontaneous": {"prediction_sha256": _sha(prediction)}}}),
        encoding="utf-8",
    )
    snapshot = tmp_path / "runs/a0_v2d_final/immutable_baseline_snapshot_v2d.json"
    snapshot.write_text(
        json.dumps(
            {
                "immutable": True,
                "hashes": {
                    "a0_report": {
                        "path": "runs/a0_v2d_final/a0_baseline_report_v2d.json",
                        "sha256": _sha(report),
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    return {"manifest": manifest, "prediction": prediction, "report": report, "snapshot": snapshot}


def test_resolves_smoke_baseline_without_a0_full_assumption(tmp_path: Path) -> None:
    tree = _baseline_tree(tmp_path)
    resolved = resolve_a0_baseline_predictions(
        {"cv_spontaneous": tree["manifest"]}, project_root=tmp_path
    )
    assert (
        Path(resolved["predictions"]["cv_spontaneous"]["path"])
        .as_posix()
        .endswith("a0_v2d_smoke/cv_spontaneous/predictions.jsonl")
    )


def test_resolves_domains_from_different_run_folders(tmp_path: Path) -> None:
    tree = _baseline_tree(tmp_path)
    scripted_manifest = tmp_path / "scripted_manifest.jsonl"
    _jsonl(scripted_manifest, [{"sample_id": "scripted-1"}])
    scripted_prediction = tmp_path / "runs/a0_archive/cv_scripted/predictions.jsonl"
    _jsonl(scripted_prediction, [{"sample_id": "scripted-1", "prediction": "test"}])
    report = json.loads(tree["report"].read_text(encoding="utf-8"))
    report["integrity"]["cv_scripted"] = {"prediction_sha256": _sha(scripted_prediction)}
    tree["report"].write_text(json.dumps(report), encoding="utf-8")
    snapshot = json.loads(tree["snapshot"].read_text(encoding="utf-8"))
    snapshot["hashes"]["a0_report"]["sha256"] = _sha(tree["report"])
    tree["snapshot"].write_text(json.dumps(snapshot), encoding="utf-8")
    resolved = resolve_a0_baseline_predictions(
        {"cv_spontaneous": tree["manifest"], "cv_scripted": scripted_manifest},
        project_root=tmp_path,
    )
    assert (
        Path(resolved["predictions"]["cv_scripted"]["path"])
        .as_posix()
        .endswith("a0_archive/cv_scripted/predictions.jsonl")
    )


def test_resolver_fails_for_missing_or_wrong_prediction_hash(tmp_path: Path) -> None:
    tree = _baseline_tree(tmp_path)
    tree["prediction"].write_text(
        '{"sample_id":"cvsp-1","prediction":"changed"}\n', encoding="utf-8"
    )
    with pytest.raises(ValueError, match="expected one SHA match"):
        resolve_a0_baseline_predictions({"cv_spontaneous": tree["manifest"]}, project_root=tmp_path)
