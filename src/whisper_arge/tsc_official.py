from __future__ import annotations

import json
import shutil
import tarfile
from pathlib import Path

from .hashing import sha256_file
from .manifests import read_jsonl
from .selection import stable_selection_key


def _read_member(handle: tarfile.TarFile, name: str) -> bytes:
    member = handle.extractfile(name.replace("\\", "/"))
    if member is None:
        raise ValueError(f"archive member missing: {name}")
    return member.read()


def _tier_rows(rows: list[dict], hours: float, seed: int) -> list[dict]:
    ranked = sorted(rows, key=lambda row: stable_selection_key(str(row["dataset_id"]), str(row["dataset_revision"]), "tsc_official_test", str(row["stable_source_id"]), seed))
    selected: list[dict] = []
    duration = 0.0
    for row in ranked:
        selected.append(row)
        duration += float(row.get("duration_seconds") or 0)
        if duration >= hours * 3600:
            break
    return selected


def materialize_tsc_official(archive: str | Path, index: str | Path, output_root: str | Path, *, seed: int = 20260730, include_train: bool = False) -> dict:
    rows = list(read_jsonl(index))
    tests = [row for row in rows if "/Test/" in str(row["archive_member"])]
    trains = [row for row in rows if "/Train/" in str(row["archive_member"])]
    if not tests or not trains:
        raise ValueError("TSC index does not expose both official Train and Test members")
    tier_rows = {"smoke": _tier_rows(tests, 1, seed), "selection": _tier_rows(tests, 5, seed), "full": _tier_rows(tests, 10, seed)}
    root = Path(output_root)
    audio_root = root / "audio"
    manifests: dict[str, list[dict]] = {name: [] for name in tier_rows}
    selected_by_audio = {str(row["archive_member"]).replace("\\", "/"): row for values in tier_rows.values() for row in values}
    selected_by_text = {str(row["reference_archive_member"]).replace("\\", "/"): row for values in tier_rows.values() for row in values}
    extracted: dict[str, dict] = {}
    train_by_audio = {str(row["archive_member"]).replace("\\", "/"): row for row in trains} if include_train else {}
    train_by_text = {str(row["reference_archive_member"]).replace("\\", "/"): row for row in trains} if include_train else {}
    train_extracted: dict[str, dict] = {}
    with tarfile.open(archive, "r:gz") as handle:
        for member in handle:
            if not member.isfile():
                continue
            member_name = member.name.replace("\\", "/")
            row = selected_by_audio.get(member_name) or train_by_audio.get(member_name)
            if row:
                sample_id = ("tsc-test-" if member_name in selected_by_audio else "tsc-train-") + str(row["stable_source_id"])
                destination = audio_root / f"{sample_id}.wav"
                destination.parent.mkdir(parents=True, exist_ok=True)
                extracted_member = handle.extractfile(member)
                if extracted_member is None:
                    raise ValueError(f"archive member missing: {member.name}")
                with destination.open("wb") as output:
                    shutil.copyfileobj(extracted_member, output, length=1024 * 1024)
                target = extracted if member_name in selected_by_audio else train_extracted
                target.setdefault(sample_id, {}).update({"audio": str(destination), "audio_sha256": sha256_file(destination)})
            row = selected_by_text.get(member_name) or train_by_text.get(member_name)
            if row:
                sample_id = ("tsc-test-" if member_name in selected_by_text else "tsc-train-") + str(row["stable_source_id"])
                extracted_member = handle.extractfile(member)
                if extracted_member is None:
                    raise ValueError(f"archive member missing: {member.name}")
                target = extracted if member_name in selected_by_text else train_extracted
                target.setdefault(sample_id, {})["reference"] = extracted_member.read().decode("utf-8").strip()
    for tier, selected in tier_rows.items():
        for row in selected:
            sample_id = f"tsc-test-{row['stable_source_id']}"
            item = extracted.get(sample_id)
            if not item or {"audio", "audio_sha256", "reference"} - item.keys():
                raise ValueError(f"TSC Test audio/transcript coverage missing: {sample_id}")
            manifests[tier].append({"sample_id": sample_id, "domain": "tsc_official_test_exploratory", "domain_group": "exploratory", "audio": item["audio"], "audio_sha256": item["audio_sha256"], "reference": item["reference"], "dataset_id": row["dataset_id"], "dataset_revision": row["dataset_revision"], "split": "official_test", "stable_source_id": row["stable_source_id"], "source_disjoint": False, "speaker_disjoint": False, "use_for_acceptance": False, "evaluation_tier": tier, "duration_seconds": row.get("duration_seconds")})
    if include_train:
        manifests["train"] = []
        for row in trains:
            sample_id = f"tsc-train-{row['stable_source_id']}"
            item = train_extracted.get(sample_id)
            if not item or {"audio", "audio_sha256", "reference"} - item.keys():
                raise ValueError(f"TSC Train audio/transcript coverage missing: {sample_id}")
            manifests["train"].append({"sample_id": sample_id, "domain": "tsc_training_pool", "audio": item["audio"], "audio_sha256": item["audio_sha256"], "reference": item["reference"], "dataset_id": row["dataset_id"], "dataset_revision": row["dataset_revision"], "split": "official_train", "stable_source_id": row["stable_source_id"], "source_disjoint": False, "speaker_disjoint": False, "use_for_acceptance": False, "duration_seconds": row.get("duration_seconds")})
    result: dict[str, dict] = {}
    for name, values in manifests.items():
        path = root / f"tsc_{name}_v2a.jsonl"
        path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in values), encoding="utf-8")
        result[name] = {"rows": len(values), "hours": sum(float(row.get("duration_seconds") or 0) for row in values) / 3600, "manifest": str(path), "manifest_sha256": sha256_file(path)}
    return {"archive": str(archive), "tiers": result, "train_included": include_train, "train_excludes_official_test": True}
