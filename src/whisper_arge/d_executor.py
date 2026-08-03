"""Offline, bounded D-profile executor using only Transformers Whisper."""
# ruff: noqa
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Callable

from .metrics import corpus_metrics

SNAPSHOT = Path(os.environ.get("WHISPER_ARGE_MODEL_SNAPSHOT", Path.home() / ".cache/huggingface/hub/models--openai--whisper-large-v3-turbo/snapshots/41f01f3fe87f28c78e2fbf8b568835947dd65ed9"))


def _rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def execute(profile_id: str, profile: dict, manifest: Path, output: Path, *, heartbeat: Callable[[int, int], None] | None = None, decoder=None) -> dict:
    rows = _rows(manifest); output.mkdir(parents=True, exist_ok=True)
    (output / "config.resolved.json").write_text(json.dumps(profile, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    done_path = output / "predictions.jsonl"
    completed = {json.loads(line)["sample_id"] for line in done_path.read_text(encoding="utf-8").splitlines() if line} if done_path.exists() else set()
    if decoder is None:
        import soundfile as sf
        import torch
        from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor

        if not SNAPSHOT.is_dir():
            raise RuntimeError(f"BLOCKED_MODEL_CACHE: {SNAPSHOT}")
        device = "cuda:0" if torch.cuda.is_available() else "cpu"; dtype = torch.float16 if device.startswith("cuda") else torch.float32
        torch.cuda.reset_peak_memory_stats() if device.startswith("cuda") else None
        processor = AutoProcessor.from_pretrained(str(SNAPSHOT), local_files_only=True)
        model = AutoModelForSpeechSeq2Seq.from_pretrained(str(SNAPSHOT), torch_dtype=dtype, low_cpu_mem_usage=True, local_files_only=True).to(device).eval()
        def decoder(row: dict) -> dict:
            audio, rate = sf.read(row["audio_path"], dtype="float32", always_2d=False)
            if getattr(audio, "ndim", 1) > 1: audio = audio.mean(axis=1)
            if rate != 16000:
                import librosa
                audio = librosa.resample(audio, orig_sr=rate, target_sr=16000)
            features = processor(audio, sampling_rate=16000, return_tensors="pt").input_features.to(device=device, dtype=dtype)
            generate = {k: v for k, v in profile.items() if k in {"language", "task", "num_beams", "do_sample", "condition_on_prev_tokens", "max_new_tokens", "temperature", "compression_ratio_threshold", "logprob_threshold", "no_speech_threshold"}}
            if int(generate.get("max_new_tokens", 444)) > 444:
                generate["max_new_tokens"] = 444
            # Transformers 4.46 Whisper crashes in the no-speech fallback path
            # when this threshold is supplied (see reports/d7_failure_traceback.md).
            # Never claim the unsupported threshold was applied.
            with torch.inference_mode(): out = model.generate(features, **generate)
            return {"prediction": processor.batch_decode(out, skip_special_tokens=True)[0], "device": device, "peak_vram_bytes": int(torch.cuda.max_memory_allocated()) if device.startswith("cuda") else None}
    started = time.monotonic(); resource = output / "resource_usage.jsonl"; log = output / "execution.log"
    with done_path.open("a", encoding="utf-8") as handle:
        for index, row in enumerate(rows, 1):
            if row["sample_id"] in completed:
                continue
            result = decoder(row)
            payload = {"sample_id": row["sample_id"], "prediction": result["prediction"], "reference": row.get("reference_text"), "profile": profile_id}
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n"); handle.flush()
            progress = {"current": index, "total": len(rows), "percent": round(100 * index / len(rows), 2), "eta_seconds": round((time.monotonic() - started) / index * (len(rows) - index), 1)}
            (output / "progress.json").write_text(json.dumps(progress, indent=2) + "\n", encoding="utf-8")
            resource.open("a", encoding="utf-8").write(json.dumps({"sample_id": row["sample_id"], "elapsed_seconds": time.monotonic() - started, "peak_vram_bytes": result.get("peak_vram_bytes")}) + "\n")
            log.open("a", encoding="utf-8").write(f"{index}/{len(rows)} {row['sample_id']}\n")
            if heartbeat: heartbeat(index, len(rows))
    actual = _rows(done_path)
    if len(actual) != len(rows) or {x["sample_id"] for x in actual} != {x["sample_id"] for x in rows}: raise RuntimeError("prediction coverage incomplete")
    pairs = [(x["reference"], x["prediction"]) for x in actual if x.get("reference") is not None]
    metrics = corpus_metrics(pairs) if pairs else {"gold_rows": 0}
    metrics.update({"profile": profile_id, "processed": len(actual), "total": len(rows), "wall_seconds": time.monotonic() - started})
    (output / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "environment.json").write_text(json.dumps({"backend": "transformers", "model": "openai/whisper-large-v3-turbo", "offline_only": True}, indent=2) + "\n", encoding="utf-8")
    return metrics
