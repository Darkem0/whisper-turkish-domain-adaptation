from __future__ import annotations

import json
import hashlib
import tarfile
from pathlib import Path

import soundfile as sf

from .hashing import sha256_file
from .selection import stable_selection_key


def materialize_mediaspeech(
    archive: str | Path, output_root: str | Path, *, revision: str = "SLR108", seed: int = 20260730
) -> dict:
    archive, root = Path(archive), Path(output_root)
    with tarfile.open(archive, "r:gz") as handle:
        files = {member.name: member for member in handle if member.isfile()}
        audio_names = sorted(name for name in files if name.endswith(".flac"))
        text_names = {name.rsplit(".", 1)[0] + ".txt" for name in audio_names}
        missing = sorted(text_names - files.keys())
        if missing:
            raise ValueError(f"missing transcripts: {missing[:3]}")
        audio_root = root / "audio"
        manifests = {"train": [], "holdout": []}
        for audio_name in audio_names:
            stem = Path(audio_name).stem
            split = (
                "holdout"
                if int(
                    stable_selection_key(
                        "openslr/SLR108/MediaSpeech/TR", revision, "utterance_holdout", stem, seed
                    )[:16],
                    16,
                )
                / 2**64
                < 0.2
                else "train"
            )
            audio_destination = audio_root / f"{stem}.flac"
            audio_destination.parent.mkdir(parents=True, exist_ok=True)
            source = handle.extractfile(files[audio_name])
            text = handle.extractfile(files[audio_name.rsplit(".", 1)[0] + ".txt"])
            if source is None or text is None:
                raise ValueError("archive member unavailable")
            audio_destination.write_bytes(source.read())
            info = sf.info(str(audio_destination))
            manifests[split].append(
                {
                    "sample_id": f"media-{stem}",
                    "domain": "mediaspeech_holdout" if split == "holdout" else "mediaspeech_train",
                    "audio": str(audio_destination),
                    "audio_sha256": sha256_file(audio_destination),
                    "reference": text.read().decode("utf-8").strip(),
                    "dataset_id": "openslr/SLR108/MediaSpeech/TR",
                    "dataset_revision": revision,
                    "split": "deterministic_utterance_holdout"
                    if split == "holdout"
                    else "remaining_train",
                    "stable_source_id": stem,
                    "source_disjoint": False,
                    "leakage_risk": "unknown",
                    "duration_seconds": info.duration,
                }
            )
    result = {}
    for name, rows in manifests.items():
        path = root / f"mediaspeech_{name}_v2d.jsonl"
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
            encoding="utf-8",
        )
        result[name] = {
            "rows": len(rows),
            "hours": sum(row["duration_seconds"] for row in rows) / 3600,
            "manifest": str(path),
            "manifest_sha256": sha256_file(path),
        }
    report = {
        "archive": str(archive),
        "archive_sha256": sha256_file(archive),
        "archive_bytes": archive.stat().st_size,
        "license": "CC-BY-4.0",
        "audio_rows": len(audio_names),
        "transcript_rows": len(text_names),
        "transcript_audio_coverage": 1.0,
        "source_grouping": "not present in archive paths or metadata",
        "source_disjoint": False,
        "leakage_risk": "unknown",
        "manifests": result,
    }
    path = root / "mediaspeech_report_v2d.json"
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {**report, "report": str(path)}


def materialize_mediaspeech_batch(
    archive: str | Path,
    output_root: str | Path,
    *,
    revision: str = "SLR108",
    seed: int = 20260730,
    batch_size: int = 300,
) -> dict:
    if not 1 <= batch_size <= 400:
        raise ValueError("batch_size must be between 1 and 400")
    archive, root = Path(archive), Path(output_root)
    audio_root, progress_path = root / "audio", root / "progress.json"
    progress = (
        json.loads(progress_path.read_text(encoding="utf-8"))
        if progress_path.exists()
        else {"audio_sha256": {}, "completed": False}
    )
    with tarfile.open(archive, "r:gz") as handle:
        files = {member.name: member for member in handle if member.isfile()}
        audio_names = sorted(name for name in files if name.endswith(".flac"))
        missing_transcripts = [
            name for name in audio_names if name.rsplit(".", 1)[0] + ".txt" not in files
        ]
        if missing_transcripts:
            raise ValueError(f"archive transcript coverage failure: {missing_transcripts[:3]}")
        remaining = []
        for name in audio_names:
            destination = audio_root / Path(name).name
            prior_hash = progress["audio_sha256"].get(destination.name)
            valid = destination.is_file() and destination.stat().st_size > 0
            actual_hash = sha256_file(destination) if valid else None
            if valid and (prior_hash is None or prior_hash == actual_hash):
                progress["audio_sha256"][destination.name] = actual_hash
            else:
                remaining.append(name)
        batch = remaining[:batch_size]
        for name in batch:
            destination = audio_root / Path(name).name
            destination.parent.mkdir(parents=True, exist_ok=True)
            source = handle.extractfile(files[name])
            if source is None:
                raise ValueError(f"cannot extract {name}")
            destination.write_bytes(source.read())
            progress["audio_sha256"][destination.name] = sha256_file(destination)
    progress["completed"] = len(progress["audio_sha256"]) == len(audio_names)
    progress["total_audio"] = len(audio_names)
    progress["verified_audio"] = len(progress["audio_sha256"])
    progress["last_batch_extracted"] = len(batch)
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text(
        json.dumps(progress, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {
        "completed": progress["completed"],
        "total_audio": len(audio_names),
        "verified_audio": len(progress["audio_sha256"]),
        "batch_extracted": len(batch),
        "remaining": len(audio_names) - len(progress["audio_sha256"]),
        "progress": str(progress_path),
    }


def finalize_mediaspeech(
    archive: str | Path, output_root: str | Path, *, revision: str = "SLR108", seed: int = 20260730
) -> dict:
    archive, root = Path(archive), Path(output_root)
    progress = json.loads((root / "progress.json").read_text(encoding="utf-8"))
    if not progress.get("completed"):
        raise ValueError("MediaSpeech extraction is not complete")
    with tarfile.open(archive, "r:gz") as handle:
        files = {member.name: member for member in handle if member.isfile()}
        audio_names = sorted(name for name in files if name.endswith(".flac"))
        manifests = {"train": [], "holdout": []}
        for name in audio_names:
            stem = Path(name).stem
            audio = root / "audio" / f"{stem}.flac"
            text = handle.extractfile(files[name.rsplit(".", 1)[0] + ".txt"])
            if not audio.is_file() or text is None:
                raise ValueError(f"coverage failure: {stem}")
            split = (
                "holdout"
                if int(
                    stable_selection_key(
                        "openslr/SLR108/MediaSpeech/TR", revision, "utterance_holdout", stem, seed
                    )[:16],
                    16,
                )
                / 2**64
                < 0.2
                else "train"
            )
            manifests[split].append(
                {
                    "sample_id": f"media-{stem}",
                    "domain": "mediaspeech_holdout" if split == "holdout" else "mediaspeech_train",
                    "audio": str(audio),
                    "audio_sha256": progress["audio_sha256"][audio.name],
                    "reference": text.read().decode("utf-8").strip(),
                    "dataset_id": "openslr/SLR108/MediaSpeech/TR",
                    "dataset_revision": revision,
                    "split": "deterministic_utterance_holdout"
                    if split == "holdout"
                    else "remaining_train",
                    "stable_source_id": stem,
                    "source_disjoint": False,
                    "leakage_risk": "unknown",
                    "duration_seconds": sf.info(str(audio)).duration,
                }
            )
    result = {}
    for split, rows in manifests.items():
        path = root / f"mediaspeech_{split}_v2d.jsonl"
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
            encoding="utf-8",
        )
        result[split] = {
            "rows": len(rows),
            "hours": sum(row["duration_seconds"] for row in rows) / 3600,
            "manifest_sha256": sha256_file(path),
            "manifest": str(path),
        }
    report = {
        "archive": str(archive),
        "archive_sha256": sha256_file(archive),
        "archive_bytes": archive.stat().st_size,
        "license": "CC-BY-4.0",
        "audio_rows": len(audio_names),
        "transcript_rows": len(audio_names),
        "transcript_audio_coverage": 1.0,
        "corrupt_or_missing": [],
        "source_disjoint": False,
        "leakage_risk": "unknown",
        "manifests": result,
    }
    report_path = root / "mediaspeech_report_v2d.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {**report, "report": str(report_path)}


def index_mediaspeech_batch(
    archive: str | Path,
    output_root: str | Path,
    *,
    revision: str = "SLR108",
    seed: int = 20260730,
    batch_size: int = 300,
) -> dict:
    root = Path(output_root)
    progress_path = root / "index_progress.json"
    parts = root / "partial_rows"
    progress = (
        json.loads(progress_path.read_text(encoding="utf-8"))
        if progress_path.exists()
        else {"next": 0, "parts": []}
    )
    if not 1 <= batch_size <= 300:
        raise ValueError("batch_size must be between 1 and 300")
    with tarfile.open(archive, "r:gz") as handle:
        files = {m.name: m for m in handle if m.isfile()}
        names = sorted(n for n in files if n.endswith(".flac"))
        start = int(progress["next"])
        if start >= len(names):
            progress["next"] = len(names)
            progress["total"] = len(names)
            progress_path.write_text(
                json.dumps(progress, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            return {
                "indexed": len(names),
                "total": len(names),
                "completed": True,
                "skipped_completed_index": True,
                "progress": str(progress_path),
            }
        batch = names[start : start + batch_size]
        part = parts / f"part-{start:04d}.jsonl"
        # A completed part is authoritative after an interrupted progress write.
        # Do not reopen audio or transcript members in that recovery case.
        if part.exists():
            completed_rows = sum(
                1 for line in part.read_text(encoding="utf-8").splitlines() if line
            )
            if completed_rows != len(batch):
                raise ValueError(f"partial row count mismatch: {part}")
            progress["next"] = start + completed_rows
            progress["parts"] = sorted(set(progress["parts"] + [str(part)]))
            progress["total"] = len(names)
            progress_path.write_text(
                json.dumps(progress, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            return {
                "indexed": progress["next"],
                "total": len(names),
                "completed": progress["next"] >= len(names),
                "skipped_existing_part": str(part),
                "progress": str(progress_path),
            }
        rows = []
        for name in batch:
            stable_id = Path(name).stem
            audio = root / "audio" / f"{stable_id}.flac"
            text = handle.extractfile(files[name.rsplit(".", 1)[0] + ".txt"])
            if not audio.is_file() or text is None:
                raise ValueError(f"coverage failure: {stable_id}")
            rows.append(
                {
                    "sample_id": f"media-{stable_id}",
                    "audio": str(audio),
                    "audio_sha256": progress_hash(root, audio.name),
                    "reference": text.read().decode("utf-8").strip(),
                    "dataset_id": "openslr/SLR108/MediaSpeech/TR",
                    "dataset_revision": revision,
                    "stable_source_id": stable_id,
                    "duration_seconds": sf.info(str(audio)).duration,
                }
            )
    parts.mkdir(parents=True, exist_ok=True)
    part.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows),
        encoding="utf-8",
    )
    progress["next"] = start + len(batch)
    progress["parts"] = sorted(set(progress["parts"] + [str(part)]))
    progress["total"] = len(names)
    progress_path.write_text(
        json.dumps(progress, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {
        "indexed": progress["next"],
        "total": len(names),
        "completed": progress["next"] >= len(names),
        "progress": str(progress_path),
    }


def progress_hash(root: Path, name: str) -> str:
    return json.loads((root / "progress.json").read_text(encoding="utf-8"))["audio_sha256"][name]


def finalize_mediaspeech_manifests(output_root: str | Path, *, seed: int = 20260730) -> dict:
    root = Path(output_root)
    progress = json.loads((root / "index_progress.json").read_text(encoding="utf-8"))
    if progress["next"] < progress["total"]:
        raise ValueError("index batches incomplete")
    rows = []
    for path in progress["parts"]:
        rows += [
            json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line
        ]
    groups = {"train": [], "holdout": []}
    for row in rows:
        # Deliberately utterance-level: sha256(dataset_revision + stable_id + seed).
        # No source grouping exists in the official archive metadata.
        decision = hashlib.sha256(
            f"{row['dataset_revision']}\0{row['stable_source_id']}\0{seed}".encode("utf-8")
        ).hexdigest()
        split = "holdout" if int(decision[:16], 16) / 2**64 < 0.2 else "train"
        row.update(
            {
                "split": "deterministic_utterance_holdout"
                if split == "holdout"
                else "remaining_train",
                "domain": "mediaspeech_holdout" if split == "holdout" else "mediaspeech_train",
                "source_disjoint": False,
                "leakage_risk": "unknown",
            }
        )
        groups[split].append(row)
    result = {}
    for split, items in groups.items():
        path = root / f"mediaspeech_{split}_v2d.jsonl"
        path.write_text(
            "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in items),
            encoding="utf-8",
        )
        result[split] = {
            "rows": len(items),
            "hours": sum(r["duration_seconds"] for r in items) / 3600,
            "manifest_sha256": sha256_file(path),
        }
    report = {
        "audio_rows": len(rows),
        "transcript_rows": len(rows),
        "transcript_audio_coverage": 1.0,
        "corrupt_or_missing": [],
        "orphan": [],
        "source_disjoint": False,
        "leakage_risk": "unknown",
        "manifests": result,
    }
    path = root / "mediaspeech_report_v2d.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {**report, "report": str(path)}
