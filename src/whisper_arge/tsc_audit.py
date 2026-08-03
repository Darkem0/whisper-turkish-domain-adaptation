from __future__ import annotations

import hashlib
import json
import tarfile
from collections import Counter
from pathlib import Path

from .manifests import read_jsonl
from .normalization import normalize_turkish
from .selection import stable_selection_key


def audit_tsc_leakage(archive: str | Path, index: str | Path, output: str | Path, *, limit: int = 10000, seed: int = 20260730) -> dict:
    if not 1 <= limit <= 10000:
        raise ValueError("limit must be between 1 and 10000")
    rows = sorted(read_jsonl(index), key=lambda row: stable_selection_key(str(row["dataset_id"]), str(row["dataset_revision"]), "tsc_leakage_audit", str(row["stable_source_id"]), seed))[:limit]
    selected_audio = {str(row["archive_member"]).replace("\\", "/") for row in rows}
    selected_text = {str(row["reference_archive_member"]).replace("\\", "/") for row in rows}
    texts_by_member: dict[str, str] = {}
    audio_hashes_by_member: dict[str, str] = {}
    adjacency = Counter()
    with tarfile.open(archive, "r:gz") as handle:
        for member in handle:
            if not member.isfile():
                continue
            extracted = handle.extractfile(member)
            if extracted is None:
                continue
            if member.name in selected_text:
                texts_by_member[member.name] = normalize_turkish(extracted.read().decode("utf-8").strip())
            elif member.name in selected_audio:
                audio_hashes_by_member[member.name] = hashlib.sha256(extracted.read()).hexdigest()
    texts, audio_hashes = [], []
    for row in rows:
        audio_name = str(row["archive_member"]).replace("\\", "/")
        text_name = str(row["reference_archive_member"]).replace("\\", "/")
        if audio_name not in audio_hashes_by_member or text_name not in texts_by_member:
            raise ValueError("index/archive coverage mismatch")
        texts.append(texts_by_member[text_name])
        audio_hashes.append(audio_hashes_by_member[audio_name])
        numeric = str(row["stable_source_id"])
        if numeric.isdigit():
            adjacency[int(numeric) // 10] += 1
    exact_dupes = sum(count - 1 for count in Counter(texts).values() if count > 1)
    audio_exact_dupes = sum(count - 1 for count in Counter(audio_hashes).values() if count > 1)
    report = {"sample_limit": limit, "sampled_rows": len(rows), "transcript_exact_duplicate_pairs": exact_dupes, "transcript_near_duplicate_method": "normalized exact match only; lexical near-duplicate model not run", "audio_near_duplicate_method": "SHA-256 exact-audio collision scan only; acoustic embedding unavailable", "audio_exact_duplicate_pairs": audio_exact_dupes, "speaker_embedding_cluster_method": "not inferred; no source/speaker metadata or embedding backend", "derived_acoustic_cluster_id": None, "utterance_id_adjacency": {"bucket_size": 10, "nonempty_buckets": len(adjacency), "max_bucket_count": max(adjacency.values(), default=0)}, "conclusion": "feasibility audit only; it does not establish source or speaker disjointness"}
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
