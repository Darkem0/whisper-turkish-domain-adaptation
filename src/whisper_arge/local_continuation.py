"""Bounded local-continuation helpers; never download data or mutate evaluation."""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_inference_manifest(root: Path, limit: int = 32) -> dict:
    """Materialize a small, deduplicated immutable manifest only from local audio."""
    sources = [
        root / "data/materialized/mediaspeech_v2d/paired/mediaspeech_holdout_paired_v2d.jsonl",
        root / "data/materialized/cv_spontaneous_v2c/cv_spontaneous_holdout_v2c.jsonl",
        root / "data/materialized/fleurs_tr_v2d/fleurs_tr_test_v2d.jsonl",
        root / "data/materialized/hf_v2d/cv_scripted_test_v2d.jsonl",
    ]
    selected, seen, missing = [], set(), []
    for source in sources:
        if not source.exists():
            missing.append(str(source))
            continue
        for line in source.read_text(encoding="utf-8").splitlines():
            if len(selected) >= limit:
                break
            row = json.loads(line)
            audio = root / str(row["audio"])
            if not audio.is_file():
                missing.append(str(audio))
                continue
            audio_hash = sha256_file(audio)
            if audio_hash in seen:
                continue
            reference = row.get("reference")
            selected.append({
                "sample_id": str(row["sample_id"]), "audio_path": str(audio.resolve()),
                "audio_sha256": audio_hash, "reference_text": reference,
                "reference_sha256": hashlib.sha256(str(reference or "").encode("utf-8")).hexdigest() if reference else None,
                "duration_seconds": row.get("duration_seconds"), "dataset": row.get("dataset_id"),
                "split": row.get("split"), "condition": row.get("domain"),
                "group_id": row.get("speaker_id") or row.get("stable_source_id") or row["sample_id"],
                "no_gold_reference": reference is None,
            })
            seen.add(audio_hash)
        if len(selected) >= limit:
            break
    protocol = root / "protocols"
    protocol.mkdir(exist_ok=True)
    manifest = protocol / "inference_manifest.jsonl"
    manifest.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in selected), encoding="utf-8")
    digest = sha256_file(manifest)
    lock = {"schema_version": 1, "immutable": True, "created_at": datetime.now(UTC).isoformat(), "rows": len(selected), "manifest_sha256": digest, "missing_paths": sorted(set(missing))}
    (protocol / "inference_manifest.lock.json").write_text(json.dumps(lock, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"rows": len(selected), "gold_rows": sum(not r["no_gold_reference"] for r in selected), "manifest": str(manifest), "manifest_sha256": digest, "missing_paths": sorted(set(missing))}


def reconcile_queue(root: Path) -> dict:
    """Separate implementation/test evidence from actual experiment execution."""
    path = root / "state/experiment_queue.json"
    queue = json.loads(path.read_text(encoding="utf-8"))
    changed = []
    for item in queue:
        ident = item["id"]
        if ident in {"P3_quality", "P4_second_pass", "P5_itn", "P6_nbest", "P7_memory"}:
            item.update({"implementation_status": "PASSED", "test_status": "PASSED", "execution_status": "BLOCKED", "status": "BLOCKED", "verdict": "BLOCKED", "error": "BLOCKED_INFERENCE_OUTPUT: implementation and unit tests are not execution evidence."})
            changed.append(ident)
        elif ident in {"A3_v2", "A4_v2", "A5_v2", "A6_v2"}:
            item.update({"implementation_status": item.get("implementation_status", "MISSING"), "test_status": item.get("test_status", "MISSING"), "execution_status": "BLOCKED", "status": "BLOCKED", "verdict": "BLOCKED", "error": "BLOCKED_TRAINING_CONTRACT: RTX 4070 SUPER is available; the independently valid training contract is not."})
            changed.append(ident)
        else:
            item.setdefault("implementation_status", "MISSING")
            item.setdefault("test_status", "MISSING")
            item["execution_status"] = item.get("status", "PENDING")
    path.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    progress = round(100 * sum(x.get("execution_status") == "PASSED" for x in queue) / len(queue))
    event = {"timestamp": datetime.now(UTC).isoformat(), "kind": "state_reconciled", "changed": changed, "progress_basis": "execution_status_only", "full_roadmap_percent": progress}
    with (root / "state/events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return {"changed": changed, "progress": progress}
