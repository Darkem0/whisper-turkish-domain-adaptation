from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from .hashing import sha256_file
from .manifests import read_jsonl


def materialize_mediaspeech_degradations(
    holdout_manifest: str | Path, output_root: str | Path, *, batch_size: int = 100
) -> dict:
    """Write clean/phone/G.711 pairs in resumable batches without changing stable IDs."""
    if not 1 <= batch_size <= 300:
        raise ValueError("batch_size must be between 1 and 300")
    root = Path(output_root)
    rows = list(read_jsonl(holdout_manifest))
    progress_path = root / "progress.json"
    progress = (
        json.loads(progress_path.read_text(encoding="utf-8"))
        if progress_path.exists()
        else {"next": 0, "parts": []}
    )
    start = int(progress["next"])
    if start >= len(rows):
        return {
            "completed": True,
            "indexed": len(rows),
            "total": len(rows),
            "progress": str(progress_path),
        }
    part = root / "partial_rows" / f"part-{start:04d}.jsonl"
    batch = rows[start : start + batch_size]
    if part.exists():
        completed = sum(1 for line in part.read_text(encoding="utf-8").splitlines() if line) // 3
        progress["next"] = start + completed
    else:
        variants = []
        for clean in batch:
            signal, sample_rate = sf.read(clean["audio"], always_2d=False)
            signal = np.asarray(signal, dtype=np.float32)
            if signal.ndim > 1:
                signal = signal.mean(axis=1)
            stable_id = str(clean["stable_source_id"])
            for degradation, audio, rate, subtype in (
                ("clean", signal, sample_rate, "PCM_16"),
                ("phone_8khz", resample_poly(signal, 8000, sample_rate), 8000, "PCM_16"),
                ("g711_mulaw", signal, sample_rate, "ULAW"),
            ):
                target = root / "audio" / degradation / f"{stable_id}.wav"
                target.parent.mkdir(parents=True, exist_ok=True)
                sf.write(target, audio, rate, format="WAV", subtype=subtype)
                row = dict(clean)
                row.update(
                    {
                        "sample_id": f"{clean['sample_id']}--{degradation}",
                        "stable_source_id": stable_id,
                        "audio": str(target),
                        "audio_sha256": sha256_file(target),
                        "degradation": degradation,
                        "paired_clean_sample_id": f"{clean['sample_id']}--clean"
                        if degradation != "clean"
                        else None,
                        "domain": f"mediaspeech_holdout_{degradation}",
                    }
                )
                variants.append(row)
        part.parent.mkdir(parents=True, exist_ok=True)
        part.write_text(
            "".join(
                json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in variants
            ),
            encoding="utf-8",
        )
        progress["next"] = start + len(batch)
    progress.update(
        {
            "total": len(rows),
            "completed": progress["next"] >= len(rows),
            "parts": sorted(set(progress["parts"] + [str(part)])),
        }
    )
    progress_path.write_text(
        json.dumps(progress, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {
        "completed": progress["completed"],
        "indexed": progress["next"],
        "total": len(rows),
        "progress": str(progress_path),
    }


def finalize_mediaspeech_degradations(output_root: str | Path) -> dict:
    root = Path(output_root)
    progress = json.loads((root / "progress.json").read_text(encoding="utf-8"))
    if not progress.get("completed"):
        raise ValueError("degradation batches incomplete")
    rows = []
    for name in progress["parts"]:
        rows.extend(
            json.loads(line) for line in Path(name).read_text(encoding="utf-8").splitlines() if line
        )
    if len(rows) != progress["total"] * 3:
        raise ValueError("paired degradation coverage mismatch")
    manifest = root / "mediaspeech_holdout_paired_v2d.jsonl"
    manifest.write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in rows),
        encoding="utf-8",
    )
    return {
        "rows": len(rows),
        "pairs": progress["total"],
        "manifest": str(manifest),
        "manifest_sha256": sha256_file(manifest),
    }
