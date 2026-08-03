from __future__ import annotations

import hashlib
import json
import shutil
import tarfile
import urllib.request
import wave
from pathlib import Path

from .hashing import sha256_file


TSC_ID = "issai/Turkish_Speech_Corpus"
MEDIA_EXTENSIONS = {".flac", ".mp3", ".opus", ".wav"}


def assert_tsc_use_mode(mode: str, clearance_evidence: str | None = None) -> None:
    if mode not in {"research_provisional", "commercial_cleared"}:
        raise ValueError("TSC mode must be research_provisional or commercial_cleared")
    if mode == "commercial_cleared" and (not clearance_evidence or not Path(clearance_evidence).is_file()):
        raise ValueError("commercial_cleared requires an existing clearance-evidence file")


def fetch_tsc(url: str, destination: str | Path, *, mode: str, clearance_evidence: str | None = None) -> dict:
    assert_tsc_use_mode(mode, clearance_evidence)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(request, timeout=30) as response:
        archive_bytes = int(response.headers.get("Content-Length", "0"))
    required = int(archive_bytes * 2.2)
    free = shutil.disk_usage(destination.parent).free
    if not archive_bytes or free < required:
        raise ValueError(f"insufficient or unresolved disk preflight: archive={archive_bytes}, required={required}, free={free}")
    partial = destination.with_suffix(destination.suffix + ".part")
    completed = partial.stat().st_size if partial.exists() else 0
    headers = {"Range": f"bytes={completed}-"} if completed else {}
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        # Some mirrors ignore Range. Restart instead of appending a full archive
        # to the partial file, which would make the resume state unrecoverable.
        append = completed and getattr(response, "status", None) == 206
        with partial.open("ab" if append else "wb") as handle:
            shutil.copyfileobj(response, handle, length=1024 * 1024)
    if partial.stat().st_size != archive_bytes:
        raise ValueError(f"incomplete download retained for resume: {partial.stat().st_size}/{archive_bytes}")
    partial.replace(destination)
    return {"archive": str(destination), "archive_bytes": archive_bytes, "archive_sha256": sha256_file(destination), "mode": mode, "publication_allowed": mode == "commercial_cleared", "company_use_allowed": mode == "commercial_cleared"}


def _source_id(member_name: str) -> str:
    source_key = str(Path(member_name).parent).replace("\\", "/")
    return "tsc-src-" + hashlib.sha256(source_key.encode("utf-8")).hexdigest()[:16]


def _duration_seconds(handle: tarfile.TarFile, member: tarfile.TarInfo) -> float | None:
    if Path(member.name).suffix.lower() != ".wav":
        return None
    extracted = handle.extractfile(member)
    if extracted is None:
        return None
    try:
        with wave.open(extracted) as audio:
            return audio.getnframes() / audio.getframerate()
    except (EOFError, wave.Error):
        return None


def index_tsc(archive: str | Path, output: str | Path, leakage_report: str | Path, *, revision: str) -> dict:
    archive = Path(archive)
    if not archive.is_file():
        raise ValueError(f"archive is missing: {archive}")
    members: list[tarfile.TarInfo] = []
    transcript_members: set[str] = set()
    with tarfile.open(archive, "r:gz") as handle:
        for member in handle:
            if not member.isfile():
                continue
            suffix = Path(member.name).suffix.lower()
            if suffix in MEDIA_EXTENSIONS:
                members.append(member)
            elif suffix == ".txt":
                transcript_members.add(str(Path(member.name).with_suffix("")))
        parent_keys = {str(Path(member.name).parent).replace("\\", "/") for member in members}
        numeric_stems = sum(Path(member.name).stem.isdigit() for member in members)
        grouping_quality = "source_group_verified" if len(parent_keys) > 20 and numeric_stems / len(members) < 0.5 else "utterance_only"
        leakage_risk = "low" if grouping_quality == "source_group_verified" else "high"
        rows = []
        for member in members:
            stable_id = Path(member.name).stem
            source_id = _source_id(member.name) if grouping_quality == "source_group_verified" else f"utterance-{stable_id}"
            transcript_key = str(Path(member.name).with_suffix(""))
            rows.append({"dataset_id": TSC_ID, "dataset_revision": revision, "archive_member": member.name, "reference_archive_member": str(Path(member.name).with_suffix(".txt")), "audio": member.name, "source_id": source_id, "stable_source_id": stable_id, "grouping_quality": grouping_quality, "duration_seconds": _duration_seconds(handle, member), "has_transcript": transcript_key in transcript_members})
    if not members:
        raise ValueError("no supported audio members found in TSC archive")
    output, leakage_report = Path(output), Path(leakage_report)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    sources = sorted({row["source_id"] for row in rows})
    report = {"archive": str(archive), "archive_sha256": sha256_file(archive), "audio_rows": len(rows), "transcript_rows": len(transcript_members), "audio_transcript_pairs": sum(bool(row["has_transcript"]) for row in rows), "audio_transcript_coverage": sum(bool(row["has_transcript"]) for row in rows) / len(rows), "duration_seconds": sum(float(row["duration_seconds"] or 0) for row in rows), "distinct_source_ids": len(sources), "parent_path_groups": len(parent_keys), "numeric_utterance_id_fraction": numeric_stems / len(members), "inspection_sample_count": min(200, len(rows)), "inspection": [{"archive_member": row["archive_member"], "reference_archive_member": row["reference_archive_member"], "source_id": row["source_id"], "has_transcript": row["has_transcript"]} for row in rows[:200]], "grouping_quality": grouping_quality, "leakage_risk": leakage_risk, "source_id_derivation": "parent archive path hash" if grouping_quality == "source_group_verified" else "utterance id only; not a source group", "leakage_status": "source-disjoint blocked" if grouping_quality == "utterance_only" else "pending_split_materialization"}
    leakage_report.parent.mkdir(parents=True, exist_ok=True)
    leakage_report.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {**report, "index": str(output), "index_sha256": sha256_file(output), "leakage_report": str(leakage_report)}
