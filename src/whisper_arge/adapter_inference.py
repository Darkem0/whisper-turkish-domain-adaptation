from __future__ import annotations

import json
import time
from pathlib import Path

from .hashing import sha256_file
from .manifests import read_jsonl, validate_manifest


def cache_adapter_predictions_batch(
    manifest_path: str | Path,
    output_root: str | Path,
    decode_contract: dict,
    *,
    adapter_path: str | Path,
    model_revision: str,
    batch_size: int = 25,
) -> dict:
    """Decode one durable adapter-evaluation batch; completed parts are never recomputed."""
    if not 1 <= batch_size <= 25:
        raise ValueError("batch_size must be between 1 and 25")
    validate_manifest(manifest_path)
    rows = list(read_jsonl(manifest_path))
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
    if part.exists():
        count = sum(1 for line in part.read_text(encoding="utf-8").splitlines() if line)
        progress["next"] = start + count
    else:
        import librosa
        import torch
        from peft import PeftModel
        from transformers import WhisperForConditionalGeneration, WhisperProcessor, pipeline

        device = 0 if torch.cuda.is_available() else -1
        if device >= 0:
            torch.cuda.reset_peak_memory_stats()
        base = WhisperForConditionalGeneration.from_pretrained(
            decode_contract["model"],
            revision=model_revision,
            torch_dtype=torch.float16 if device >= 0 else torch.float32,
        )
        model = PeftModel.from_pretrained(base, str(adapter_path))
        processor = WhisperProcessor.from_pretrained(
            decode_contract["model"], revision=model_revision
        )
        asr = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            device=device,
            torch_dtype=torch.float16 if device >= 0 else torch.float32,
        )
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
        if int(generate.get("max_new_tokens", 444)) > 444:
            generate["max_new_tokens"] = 444
        begin = time.monotonic()
        predictions = []
        for row in rows[start : start + batch_size]:
            audio, _ = librosa.load(str(row["audio"]), sr=16000, mono=True)
            result = asr(audio, generate_kwargs=generate, return_timestamps=True)
            predictions.append(
                {
                    "sample_id": row["sample_id"],
                    "prediction": result["text"],
                    "model": decode_contract["model"],
                    "adapter_sha256": sha256_file(Path(adapter_path) / "adapter_model.safetensors"),
                }
            )
        part.parent.mkdir(parents=True, exist_ok=True)
        part.write_text(
            "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in predictions),
            encoding="utf-8",
        )
        progress["next"] = start + len(predictions)
        progress["wall_seconds_last_batch"] = time.monotonic() - begin
        progress["peak_vram_bytes_last_batch"] = (
            int(torch.cuda.max_memory_allocated()) if device >= 0 else None
        )
    progress.update(
        {
            "total": len(rows),
            "completed": progress["next"] >= len(rows),
            "parts": sorted(set(progress["parts"] + [str(part)])),
            "manifest": str(manifest_path),
            "adapter": str(adapter_path),
            "adapter_sha256": sha256_file(Path(adapter_path) / "adapter_model.safetensors"),
            "model_revision": model_revision,
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
