from __future__ import annotations

import csv
import io
import json
import tarfile
from pathlib import Path

from .hashing import sha256_file
from .selection import stable_selection_key


def materialize_cv_spontaneous(archive: str | Path, output_root: str | Path, *, revision: str, seed: int = 20260730) -> dict:
    archive, root = Path(archive), Path(output_root)
    if not archive.is_file():
        raise ValueError(f"archive missing: {archive}")
    with tarfile.open(archive, "r:gz") as handle:
        tsv_member = next((member for member in handle if member.name.endswith("/ss-corpus-tr.tsv")), None)
        if tsv_member is None:
            raise ValueError("ss-corpus-tr.tsv not found")
        data = handle.extractfile(tsv_member)
        if data is None:
            raise ValueError("cannot read corpus TSV")
        rows = list(csv.DictReader(io.TextIOWrapper(data, encoding="utf-8"), delimiter="\t"))
        speakers = sorted({row["client_id"] for row in rows if row.get("client_id")})
        if len(speakers) < 2:
            raise ValueError("speaker-disjoint split requires at least two anonymous client IDs")
        ranked = sorted(speakers, key=lambda value: stable_selection_key("mozilla/common_voice_spontaneous_tr", revision, "speaker_holdout", value, seed))
        holdout_speakers = set(ranked[:max(1, round(len(speakers) * 0.2))])
        audio_by_name = {member.name.rsplit("/", 1)[-1]: member for member in handle if member.isfile() and member.name.endswith(".mp3")}
        output_audio = root / "audio"
        manifests: dict[str, list[dict]] = {"train": [], "holdout": []}
        missing_audio: list[str] = []
        for row in rows:
            audio_name = row.get("audio_file", "")
            member = audio_by_name.get(audio_name)
            if member is None:
                missing_audio.append(audio_name)
                continue
            extracted = handle.extractfile(member)
            if extracted is None:
                missing_audio.append(audio_name)
                continue
            destination = output_audio / audio_name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(extracted.read())
            split = "holdout" if row["client_id"] in holdout_speakers else "train"
            original = row.get("transcription", "").strip()
            scoring = original.replace("<disfluency>", " ")
            manifests[split].append({"sample_id": f"cvsp-{row['audio_id']}", "domain": "cv_spontaneous_holdout" if split == "holdout" else "cv_spontaneous_train", "domain_group": "style_probe" if split == "holdout" else "training", "audio": str(destination), "audio_sha256": sha256_file(destination), "reference": scoring, "original_annotated_transcript": original, "asr_scoring_transcript": scoring, "dataset_id": "mozilla/common_voice_spontaneous_tr", "dataset_revision": revision, "split": split, "speaker_id": row["client_id"], "stable_source_id": row["audio_id"], "duration_seconds": float(row.get("duration_ms") or 0) / 1000, "disfluency_marker": "<disfluency>"})
    result: dict[str, dict] = {}
    for split, values in manifests.items():
        path = root / f"cv_spontaneous_{split}_v2c.jsonl"
        path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in values), encoding="utf-8")
        result[split] = {"rows": len(values), "hours": sum(row["duration_seconds"] for row in values) / 3600, "manifest": str(path), "manifest_sha256": sha256_file(path)}
    marker_rows = sum("<disfluency>" in row.get("transcription", "").lower() for row in rows)
    report = {"archive": str(archive), "archive_bytes": archive.stat().st_size, "archive_sha256": sha256_file(archive), "license": "CC0-1.0", "rows": len(rows), "audio_members": len(audio_by_name), "orphan_audio_members": sorted(set(audio_by_name) - {row.get("audio_file", "") for row in rows}), "transcript_audio_coverage": (len(rows) - len(missing_audio)) / len(rows) if rows else 0.0, "missing_audio": missing_audio, "anonymous_speaker_ids": len(speakers), "holdout_speakers": len(holdout_speakers), "speaker_disjoint": True, "holdout_excluded_from_train": True, "style_probe": {"hard_acceptance_gate": False, "reason": "only two anonymous speaker blocks and eleven holdout clips", "reporting": ["per_speaker", "aggregate"]}, "disfluency": {"marker": "<disfluency>", "datasheet_semantics": "annotation placeholder; it does not provide lexical filler content", "literal_training_target": False, "scoring_supported": False, "reason": "placeholder does not identify the spoken filler words", "rows_with_marker": marker_rows, "marker_occurrences": sum(row.get("transcription", "").lower().count("<disfluency>") for row in rows)}, "manifests": result}
    report_path = root / "cv_spontaneous_report_v2c.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {**report, "report": str(report_path)}
