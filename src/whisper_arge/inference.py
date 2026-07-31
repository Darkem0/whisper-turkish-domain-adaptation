from __future__ import annotations

import json
import time
from pathlib import Path

from .hashing import sha256_file
from .manifests import read_jsonl, validate_manifest
from .selection import stable_selection_key


def cache_base_predictions(
    manifest_path: str | Path, output_path: str | Path, decode_contract: dict, dry_run: bool = False
) -> dict:
    validate_manifest(manifest_path)
    rows = list(read_jsonl(manifest_path))
    if dry_run:
        return {
            "rows": len(rows),
            "dry_run": True,
            "output": str(output_path),
            "cache_exists": Path(output_path).exists(),
        }
    try:
        import librosa
        import torch
        from transformers import pipeline
    except ImportError as exc:
        raise RuntimeError("base inference requires the locked research dependencies") from exc
    device = 0 if torch.cuda.is_available() else -1
    asr = pipeline(
        "automatic-speech-recognition",
        model=decode_contract["model"],
        device=device,
        torch_dtype=torch.float16 if device >= 0 else torch.float32,
    )
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row in rows:
            audio, _ = librosa.load(str(row["audio"]), sr=16000, mono=True)
            result = asr(
                audio,
                generate_kwargs={
                    key: value
                    for key, value in decode_contract.items()
                    if key
                    in {
                        "language",
                        "task",
                        "num_beams",
                        "do_sample",
                        "condition_on_prev_tokens",
                        "max_new_tokens",
                    }
                },
            )
            handle.write(
                json.dumps(
                    {
                        "sample_id": row["sample_id"],
                        "prediction": result["text"],
                        "model": decode_contract["model"],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    return {
        "rows": len(rows),
        "dry_run": False,
        "output": str(output),
        "predictions_sha256": sha256_file(output),
    }


def cache_base_predictions_batch(
    manifest_path: str | Path,
    output_root: str | Path,
    decode_contract: dict,
    *,
    batch_size: int = 5,
    max_samples: int | None = None,
    seed: int = 20260730,
) -> dict:
    """Run one bounded, restartable base-ASR batch and persist predictions immediately."""
    if not 1 <= batch_size <= 25:
        raise ValueError("batch_size must be between 1 and 25")
    validate_manifest(manifest_path)
    rows = list(read_jsonl(manifest_path))
    if max_samples is not None:
        rows = sorted(
            rows,
            key=lambda row: stable_selection_key(
                str(row["dataset_id"]),
                str(row["dataset_revision"]),
                "a0_smoke",
                str(row["sample_id"]),
                seed,
            ),
        )[:max_samples]
    root = Path(output_root)
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
            "predicted": len(rows),
            "total": len(rows),
            "progress": str(progress_path),
        }
    part = root / "partial_predictions" / f"part-{start:06d}.jsonl"
    batch = rows[start : start + batch_size]
    if part.exists():
        count = sum(1 for line in part.read_text(encoding="utf-8").splitlines() if line)
        progress["next"] = start + count
    else:
        import librosa
        import torch
        from transformers import pipeline

        device = 0 if torch.cuda.is_available() else -1
        if device >= 0:
            torch.cuda.reset_peak_memory_stats()
        asr = pipeline(
            "automatic-speech-recognition",
            model=decode_contract["model"],
            device=device,
            torch_dtype=torch.float16 if device >= 0 else torch.float32,
        )
        begin = time.monotonic()
        predictions = []
        generate = {
            key: value
            for key, value in decode_contract.items()
            if key
            in {
                "language",
                "task",
                "num_beams",
                "do_sample",
                "condition_on_prev_tokens",
                "max_new_tokens",
            }
        }
        # transformers 4.46 prepends four Whisper decoder prompt tokens; retain
        # the locked 448-position context limit without exceeding it.
        if int(generate.get("max_new_tokens", 444)) > 444:
            generate["max_new_tokens"] = 444
        progress["effective_max_new_tokens"] = generate.get("max_new_tokens")
        for row in batch:
            audio, _ = librosa.load(str(row["audio"]), sr=16000, mono=True)
            # Whisper long-form decoding (>30 s) requires timestamp prediction
            # in transformers 4.46; the evaluation still consumes result["text"].
            result = asr(audio, generate_kwargs=generate, return_timestamps=True)
            predictions.append(
                {
                    "sample_id": row["sample_id"],
                    "prediction": result["text"],
                    "model": decode_contract["model"],
                }
            )
        part.parent.mkdir(parents=True, exist_ok=True)
        part.write_text(
            "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in predictions),
            encoding="utf-8",
        )
        progress["wall_seconds_last_batch"] = time.monotonic() - begin
        progress["peak_vram_bytes_last_batch"] = (
            int(torch.cuda.max_memory_allocated()) if device >= 0 else None
        )
        progress["next"] = start + len(batch)
    progress.update(
        {
            "total": len(rows),
            "completed": progress["next"] >= len(rows),
            "parts": sorted(set(progress["parts"] + [str(part)])),
            "manifest": str(manifest_path),
            "max_samples": max_samples,
        }
    )
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text(
        json.dumps(progress, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {
        "completed": progress["completed"],
        "predicted": progress["next"],
        "total": len(rows),
        "part": str(part),
        "progress": str(progress_path),
        "wall_seconds_last_batch": progress.get("wall_seconds_last_batch"),
        "peak_vram_bytes_last_batch": progress.get("peak_vram_bytes_last_batch"),
    }


def finalize_base_predictions(output_root: str | Path) -> dict:
    root = Path(output_root)
    progress = json.loads((root / "progress.json").read_text(encoding="utf-8"))
    if not progress.get("completed"):
        raise ValueError("prediction batches incomplete")
    rows = []
    for name in progress["parts"]:
        rows.extend(
            json.loads(line) for line in Path(name).read_text(encoding="utf-8").splitlines() if line
        )
    if len(rows) != progress["total"]:
        raise ValueError("prediction coverage mismatch")
    output = root / "predictions.jsonl"
    output.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8"
    )
    return {
        "predictions": str(output),
        "predictions_sha256": sha256_file(output),
        "rows": len(rows),
        "wall_seconds_last_batch": progress.get("wall_seconds_last_batch"),
        "peak_vram_bytes_last_batch": progress.get("peak_vram_bytes_last_batch"),
    }


def make_deterministic_subset(
    manifest_path: str | Path, output_path: str | Path, *, max_samples: int, seed: int = 20260730
) -> dict:
    if max_samples < 1:
        raise ValueError("max_samples must be positive")
    validate_manifest(manifest_path)
    rows = sorted(
        read_jsonl(manifest_path),
        key=lambda row: stable_selection_key(
            str(row["dataset_id"]),
            str(row["dataset_revision"]),
            "a0_smoke",
            str(row["sample_id"]),
            seed,
        ),
    )[:max_samples]
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return {"rows": len(rows), "manifest": str(output), "manifest_sha256": sha256_file(output)}
