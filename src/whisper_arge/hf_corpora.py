from __future__ import annotations

import json
import itertools
from pathlib import Path

import soundfile as sf

from .hashing import sha256_bytes, sha256_file


CORPORA = {
    "cv_scripted": {
        "dataset_id": "ysdede/commonvoice_17_tr_fixed",
        "config": "default",
        "revision": "9d8a025f1ae7c5a2f5c43298c7c4910b03995a4b",
        "license": "CC0-1.0",
        "transcript_field": "transcription",
        "id_field": "path",
        "speaker_field": "client_id",
    },
    "fleurs_tr": {
        "dataset_id": "google/fleurs",
        "config": "tr_tr",
        "revision": "70bb2e84b976b7e960aa89f1c648e09c59f894dd",
        "license": "CC-BY-4.0",
        "transcript_field": "transcription",
        "id_field": "id",
        "speaker_field": None,
        "split_sizes": {"test": 743},
    },
}


def materialize_hf_corpus_batch(
    corpus: str, split: str, output_root: str | Path, *, batch_size: int = 100
) -> dict:
    """Materialize at most one small batch; completed JSONL parts are never rewritten."""
    if corpus not in CORPORA:
        raise ValueError(f"unknown corpus: {corpus}")
    if not 1 <= batch_size <= 300:
        raise ValueError("batch_size must be between 1 and 300")
    spec, root = CORPORA[corpus], Path(output_root)
    progress_path = root / f"{corpus}_{split}_progress.json"
    progress = (
        json.loads(progress_path.read_text(encoding="utf-8"))
        if progress_path.exists()
        else {"next": 0, "parts": []}
    )
    start = int(progress["next"])
    part_root = root / "partial_rows" / corpus / split
    part = part_root / f"part-{start:06d}.jsonl"
    if part.exists():
        count = sum(1 for line in part.read_text(encoding="utf-8").splitlines() if line)
        progress["next"] = start + count
        progress["parts"] = sorted(set(progress["parts"] + [str(part)]))
        progress_path.parent.mkdir(parents=True, exist_ok=True)
        progress_path.write_text(
            json.dumps(progress, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return {
            "corpus": corpus,
            "split": split,
            "indexed": progress["next"],
            "skipped_existing_part": str(part),
            "progress": str(progress_path),
        }

    from datasets import load_dataset

    streaming = corpus == "fleurs_tr"
    dataset = load_dataset(
        spec["dataset_id"],
        spec["config"],
        split=split,
        revision=spec["revision"],
        streaming=streaming,
    )
    total = spec.get("split_sizes", {}).get(split) if streaming else len(dataset)
    if total is not None and start >= total:
        progress.update({"total": total, "completed": True})
        progress_path.parent.mkdir(parents=True, exist_ok=True)
        progress_path.write_text(
            json.dumps(progress, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return {
            "corpus": corpus,
            "split": split,
            "indexed": start,
            "total": total,
            "completed": True,
            "progress": str(progress_path),
        }
    if streaming:
        items = list(itertools.islice(dataset, start, start + batch_size))
    else:
        items = dataset.select(range(start, min(start + batch_size, total)))
    audio_root = root / "audio" / corpus / split
    rows = []
    for offset, item in enumerate(items):
        audio = item["audio"]
        if not isinstance(audio, dict) or "array" not in audio or "sampling_rate" not in audio:
            raise ValueError(f"decoded audio unavailable at {corpus}/{split}/{start + offset}")
        source_record_id = str(item.get(spec["id_field"]) or "")
        # FLEURS' public numeric id is not unique in its official test split.
        # The deterministic dataset row index makes a materialization identity unique
        # without claiming a source or speaker grouping.
        stable_id = (
            f"{source_record_id}-{start + offset:06d}"
            if corpus == "fleurs_tr"
            else (source_record_id or f"{split}-{start + offset:06d}")
        )
        destination = audio_root / f"{stable_id}.flac"
        destination.parent.mkdir(parents=True, exist_ok=True)
        sf.write(destination, audio["array"], audio["sampling_rate"], format="FLAC")
        transcript = str(item.get(spec["transcript_field"]) or "").strip()
        if not transcript:
            raise ValueError(f"empty transcript at {corpus}/{split}/{stable_id}")
        rows.append(
            {
                "sample_id": f"{corpus}-{stable_id}",
                "stable_source_id": stable_id,
                "source_record_id": source_record_id or None,
                "audio": str(destination),
                "audio_sha256": sha256_file(destination),
                "reference": transcript,
                "dataset_id": spec["dataset_id"],
                "dataset_revision": spec["revision"],
                "license": spec["license"],
                "official_split": split,
                "speaker_id": item.get(spec["speaker_field"]) if spec["speaker_field"] else None,
                "duration_seconds": float(len(audio["array"]) / audio["sampling_rate"]),
            }
        )
    part_root.mkdir(parents=True, exist_ok=True)
    part.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    progress.update(
        {
            "next": start + len(rows),
            "total": total,
            "completed": total is not None and start + len(rows) >= total,
            "parts": sorted(set(progress["parts"] + [str(part)])),
        }
    )
    progress_path.write_text(
        json.dumps(progress, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {
        "corpus": corpus,
        "split": split,
        "indexed": progress["next"],
        "total": total,
        "completed": progress["completed"],
        "part": str(part),
        "progress": str(progress_path),
    }


def finalize_hf_corpus_manifest(corpus: str, split: str, output_root: str | Path) -> dict:
    """Assemble a final manifest from partial metadata only; never re-read source audio."""
    if corpus not in CORPORA:
        raise ValueError(f"unknown corpus: {corpus}")
    spec, root = CORPORA[corpus], Path(output_root)
    progress_path = root / f"{corpus}_{split}_progress.json"
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    if not progress.get("completed"):
        raise ValueError("materialization batches are incomplete")
    rows = []
    for name in progress["parts"]:
        rows.extend(
            json.loads(line) for line in Path(name).read_text(encoding="utf-8").splitlines() if line
        )
    if len(rows) != progress["total"]:
        raise ValueError("partial row coverage mismatch")
    ids = [str(row["sample_id"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate sample_id in partial rows")
    domain = (
        "cv_scripted_official_test" if corpus == "cv_scripted" else "fleurs_tr_tr_official_test"
    )
    for row in rows:
        row["domain"] = domain
        row["split"] = f"official_{split}"
    manifest = root / f"{corpus}_{split}_v2d.jsonl"
    manifest.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    audio_chain = sha256_bytes(
        "".join(
            f"{row['sample_id']}:{row['audio_sha256']}\n"
            for row in sorted(rows, key=lambda item: item["sample_id"])
        ).encode("utf-8")
    )
    report = {
        "dataset_id": spec["dataset_id"],
        "dataset_revision": spec["revision"],
        "license": spec["license"],
        "official_split": split,
        "samples": len(rows),
        "hours": sum(float(row["duration_seconds"]) for row in rows) / 3600,
        "audio_rows": len(rows),
        "transcript_rows": len(rows),
        "audio_transcript_coverage": 1.0,
        "corrupt": [],
        "missing": [],
        "orphan": [],
        "manifest": str(manifest),
        "manifest_sha256": sha256_file(manifest),
        "audio_sha256_chain": audio_chain,
    }
    report_path = root / f"{corpus}_{split}_report_v2d.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {**report, "report": str(report_path)}
