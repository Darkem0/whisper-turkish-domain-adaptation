"""One-sample, offline Transformers smoke test using the immutable local manifest."""
from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "SMOKE_D0"
SNAPSHOT = Path(os.environ.get("WHISPER_ARGE_MODEL_SNAPSHOT", Path.home() / ".cache/huggingface/hub/models--openai--whisper-large-v3-turbo/snapshots/41f01f3fe87f28c78e2fbf8b568835947dd65ed9"))


def main() -> None:
    RUN.mkdir(parents=True, exist_ok=True)
    row = json.loads((ROOT / "protocols/inference_manifest.jsonl").read_text(encoding="utf-8").splitlines()[0])
    result = {"schema_version": 1, "started_at": datetime.now(UTC).isoformat(), "sample_id": row["sample_id"], "audio_path": row["audio_path"], "model": "openai/whisper-large-v3-turbo", "model_revision": SNAPSHOT.name, "offline_only": True, "pipeline": "existing WAV -> Transformers Whisper", "ffmpeg_stage": "not_invoked: input is already a verified WAV; ffmpeg.exe is not discoverable on PATH"}
    try:
        import soundfile as sf
        import torch
        from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor

        if not SNAPSHOT.is_dir():
            raise RuntimeError(f"BLOCKED_MODEL_CACHE: missing snapshot {SNAPSHOT}")
        audio, rate = sf.read(row["audio_path"], dtype="float32", always_2d=False)
        if getattr(audio, "ndim", 1) > 1:
            audio = audio.mean(axis=1)
        if rate != 16000:
            raise RuntimeError(f"BLOCKED_INFERENCE_PATH: existing WAV sample rate is {rate}, expected 16000 and ffmpeg.exe is unavailable")
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if device.startswith("cuda") else torch.float32
        if device.startswith("cuda"):
            torch.cuda.reset_peak_memory_stats()
        processor = AutoProcessor.from_pretrained(str(SNAPSHOT), local_files_only=True)
        model = AutoModelForSpeechSeq2Seq.from_pretrained(str(SNAPSHOT), torch_dtype=dtype, low_cpu_mem_usage=True, local_files_only=True).to(device)
        model.eval()
        inputs = processor(audio, sampling_rate=16000, return_tensors="pt").input_features.to(device=device, dtype=dtype)
        started = time.monotonic()
        with torch.inference_mode():
            generated = model.generate(inputs, language="tr", task="transcribe", num_beams=1, do_sample=False, max_new_tokens=128)
        text = processor.batch_decode(generated, skip_special_tokens=True)[0]
        result.update({"verdict": "PASSED", "ended_at": datetime.now(UTC).isoformat(), "prediction": text, "wall_seconds": time.monotonic() - started, "gpu": torch.cuda.get_device_name(0) if device.startswith("cuda") else None, "peak_vram_bytes": int(torch.cuda.max_memory_allocated()) if device.startswith("cuda") else None, "input_sample_rate": rate, "dtype": str(dtype), "json_validated": bool(text.strip())})
    except Exception as exc:
        result.update({"verdict": "BLOCKED", "ended_at": datetime.now(UTC).isoformat(), "error": f"{type(exc).__name__}: {exc}", "json_validated": False})
    (RUN / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    if result["verdict"] != "PASSED":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
