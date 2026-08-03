from __future__ import annotations

import json
import shutil
import urllib.request
from pathlib import Path

from .hashing import sha256_file
from .manifests import read_jsonl
from .selection import stable_selection_key


def disk_preflight(url: str, destination: str | Path, expansion_factor: float = 2.2) -> dict:
    request = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            archive_bytes = int(response.headers.get("Content-Length", "0"))
    except Exception as exc:  # network metadata must not stop a dry run
        return {"url": url, "archive_bytes": None, "estimated_required_bytes": None, "free_bytes": shutil.disk_usage(destination).free, "sufficient": False, "error": str(exc)}
    required = int(archive_bytes * expansion_factor)
    free = shutil.disk_usage(destination).free
    return {"url": url, "archive_bytes": archive_bytes, "estimated_required_bytes": required, "free_bytes": free, "sufficient": free >= required}


def assign_disjoint_split(row: dict, holdout_fraction: float, seed: int, group_field: str) -> str:
    group = row.get(group_field) or row.get("stable_source_id")
    if not group:
        raise ValueError(f"row lacks {group_field} and stable_source_id")
    key = stable_selection_key(str(row["dataset_id"]), str(row["dataset_revision"]), "v2_holdout", str(group), seed)
    return "holdout" if int(key[:16], 16) / 2**64 < holdout_fraction else "train"


def materialize_rows(source_path: str | Path, output_path: str | Path, *, holdout_fraction: float, seed: int, group_field: str, dry_run: bool) -> dict:
    rows = list(read_jsonl(source_path))
    materialized: list[dict] = []
    for row in rows:
        item = dict(row)
        item["split_v2"] = assign_disjoint_split(item, holdout_fraction, seed, group_field)
        audio = Path(str(item["audio"]))
        if not dry_run:
            if not audio.is_file():
                raise ValueError(f"audio is missing: {audio}")
            item["audio_sha256"] = sha256_file(audio)
        materialized.append(item)
    report = {"rows": len(materialized), "holdout_rows": sum(row["split_v2"] == "holdout" for row in materialized), "train_rows": sum(row["split_v2"] == "train" for row in materialized), "group_field": group_field, "dry_run": dry_run}
    if not dry_run:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in materialized), encoding="utf-8")
        report["manifest_sha256"] = sha256_file(destination)
    return report


def leakage_report(source_path: str | Path, *, group_field: str, holdout_hours: float, seed: int) -> dict:
    rows = list(read_jsonl(source_path))
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        group = str(row.get(group_field) or row.get("stable_source_id") or "")
        if not group:
            raise ValueError(f"row lacks {group_field} and stable_source_id")
        grouped.setdefault(group, []).append(row)
    ranked = sorted(grouped, key=lambda group: stable_selection_key(str(grouped[group][0]["dataset_id"]), str(grouped[group][0]["dataset_revision"]), "v2_tsc_holdout", group, seed))
    target = holdout_hours * 3600
    selected: set[str] = set()
    duration = 0.0
    for group in ranked:
        group_duration = sum(float(row.get("duration_seconds", 0.0)) for row in grouped[group])
        selected.add(group)
        duration += group_duration
        if duration >= target:
            break
    train = set(grouped) - selected
    return {"group_field": group_field, "holdout_target_hours": holdout_hours, "holdout_estimated_hours": duration / 3600, "holdout_groups": len(selected), "train_groups": len(train), "source_group_overlap": sorted(selected & train), "leakage_free": not bool(selected & train)}


def materialize_tsc_rows(source_path: str | Path, output_path: str | Path, *, seed: int, dry_run: bool, holdout_hours: float = 10) -> dict:
    rows = list(read_jsonl(source_path))
    groups: dict[str, list[dict]] = {}
    for row in rows:
        if row.get("grouping_quality") and row["grouping_quality"] != "source_group_verified":
            raise ValueError("TSC source-disjoint materialization is blocked: grouping_quality is not source_group_verified")
        source_id = str(row.get("source_id") or "")
        if not source_id:
            raise ValueError("TSC index row lacks source_id")
        groups.setdefault(source_id, []).append(row)
    ranked = sorted(groups, key=lambda source_id: stable_selection_key(str(groups[source_id][0]["dataset_id"]), str(groups[source_id][0]["dataset_revision"]), "v2_tsc_holdout", source_id, seed))
    selected: set[str] = set()
    duration = 0.0
    tier_thresholds = {"smoke": 3600.0, "selection": 18000.0, "full": holdout_hours * 3600}
    source_tiers: dict[str, list[str]] = {}
    for source_id in ranked:
        source_duration = sum(float(row.get("duration_seconds") or 0) for row in groups[source_id])
        selected.add(source_id)
        duration += source_duration
        source_tiers[source_id] = [name for name, threshold in tier_thresholds.items() if duration <= threshold or duration - source_duration < threshold]
        if duration >= tier_thresholds["full"]:
            break
    materialized: list[dict] = []
    for row in rows:
        item = dict(row)
        item["split_v2"] = "holdout" if item["source_id"] in selected else "train"
        item["evaluation_tiers"] = source_tiers.get(item["source_id"], [])
        if not dry_run:
            audio = Path(str(item["audio"]))
            if not audio.is_file():
                raise ValueError(f"audio is missing: {audio}")
            item["audio_sha256"] = sha256_file(audio)
        materialized.append(item)
    report = {"rows": len(materialized), "holdout_rows": sum(row["split_v2"] == "holdout" for row in materialized), "holdout_estimated_hours": duration / 3600, "holdout_target_hours": holdout_hours, "source_group_overlap": [], "leakage_free": True, "dry_run": dry_run}
    if not dry_run:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in materialized), encoding="utf-8")
        report["manifest_sha256"] = sha256_file(destination)
    return report
