"""Audio-only deterministic A7 clipping-safe policy audit."""

from __future__ import annotations
import hashlib
import json
from collections import Counter
from pathlib import Path
import librosa
import numpy as np
from whisper_arge.a7_augmentation import IMPLEMENTATION_ID, apply, policy

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/materialized/training_a7_v2"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rows(p):
    return [json.loads(x) for x in Path(p).read_text(encoding="utf8").splitlines() if x]


def main():
    schedule = rows(DATA / "a7_sample_schedule.jsonl")
    manifest = {
        x["sample_id"]: x
        for x in rows(ROOT / "data/materialized/training_a5_v2/a5_train_manifest.jsonl")
    }
    audited = []
    peaks = []
    prevented = Counter()
    max_snr_delta = 0.0
    for e in schedule:
        if e["augmentation_bucket"] not in {
            "phone_band",
            "speed_075",
            "noise_gain",
            "phone_band_noise_gain",
        }:
            continue
        r = manifest[e["sample_id"]]
        audio, _ = librosa.load(ROOT / r["audio_path"], sr=16000, mono=True)
        first, p = apply(audio, e["augmentation_bucket"], e["deterministic_seed"])
        second, p2 = apply(audio, e["augmentation_bucket"], e["deterministic_seed"])
        if (
            hashlib.sha256(first.tobytes()).hexdigest()
            != hashlib.sha256(second.tobytes()).hexdigest()
        ):
            raise ValueError("nondeterministic tensor")
        if (
            not np.isfinite(first).all()
            or not np.any(np.abs(first) > 1e-8)
            or p["final_peak"] > 0.980001
        ):
            raise ValueError("audio validation")
        if e["augmentation_bucket"] in {"noise_gain", "phone_band_noise_gain"}:
            max_snr_delta = max(
                max_snr_delta,
                abs(p["measured_snr_before_safety"] - p["measured_snr_after_safety"]),
            )
        prevented[e["augmentation_bucket"]] += int(p["clipping_prevented"])
        peaks.append(p["final_peak"])
        audited.append({**e, "augmentation_parameters": p})
    assign = []
    for e in schedule:
        q = dict(e)
        q["augmentation_parameters"] = policy(e["augmentation_bucket"], e["deterministic_seed"])
        assign.append(q)
    for a in audited:
        assign[a["schedule_index"]]["augmentation_parameters"] = a["augmentation_parameters"]
    (DATA / "a7_augmentation_assignment_peak_guard_v3.jsonl").write_text(
        "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in assign), encoding="utf8"
    )
    source_lock = json.loads((DATA / "a7_schedule_lock.json").read_text(encoding="utf8"))
    lock = {
        "status": "PASSED",
        "policy_version": IMPLEMENTATION_ID,
        "implementation_sha256": sha(ROOT / "src/whisper_arge/a7_augmentation.py"),
        "old_policy_hash": sha(DATA / "a7_schedule_lock.json"),
        "schedule_rows": source_lock["schedule_rows"],
        "bucket_counts": source_lock["bucket_counts"],
        "source_counts": source_lock["source_counts"],
        "schedule_sha256": sha(DATA / "a7_sample_schedule.jsonl"),
        "assignment_sha256": sha(DATA / "a7_augmentation_assignment_peak_guard_v3.jsonl"),
        "revision_reason": "smoke-detected clipping",
        "optimizer_steps_before_revision": 0,
        "training_contamination": False,
        "audited_noise_occurrences": len(audited),
        "clipping_prevented_by_bucket": prevented,
        "max_final_peak": max(peaks),
        "max_snr_delta_db": max_snr_delta,
    }
    (DATA / "a7_schedule_lock_peak_guard_v3.json").write_text(
        json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
    )
    print(json.dumps(lock, ensure_ascii=False))


if __name__ == "__main__":
    main()
