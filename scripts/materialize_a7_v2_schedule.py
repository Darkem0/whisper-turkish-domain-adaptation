"""Materialize the authorized deterministic A7 source-anchored schedule."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from whisper_arge.a7_augmentation import IMPLEMENTATION_ID, policy


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "materialized" / "training_a7_v2"
SEED = 20260730
BUCKETS = {
    "tsc_anchor_unchanged": 1067,
    "phone_like_unchanged": 640,
    "phone_band": 640,
    "speed_075": 320,
    "noise_gain": 267,
    "phone_band_noise_gain": 266,
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_jsonl(path: Path, values: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(value, ensure_ascii=False) + "\n" for value in values), encoding="utf-8"
    )


def hamilton(total: int, populations: dict[str, list[dict]]) -> dict[str, int]:
    count = sum(len(value) for value in populations.values())
    raw = {key: total * len(value) / count for key, value in populations.items()}
    allocation = {key: int(value) for key, value in raw.items()}
    for key, _ in sorted(
        raw.items(), key=lambda item: (item[1] - allocation[item[0]], item[0]), reverse=True
    )[: total - sum(allocation.values())]:
        allocation[key] += 1
    if total >= len(populations):
        for key in populations:
            if allocation[key] == 0:
                donor = max(allocation, key=allocation.get)
                allocation[donor] -= 1
                allocation[key] = 1
    return allocation


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    train_path = ROOT / "data/materialized/training_a5_v2/a5_train_manifest.jsonl"
    validation_path = ROOT / "data/materialized/training_a4_v2/a4_validation_manifest.jsonl"
    values = [
        json.loads(line) for line in train_path.read_text(encoding="utf-8").splitlines() if line
    ]
    validation = [
        json.loads(line)
        for line in validation_path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    validation_audio = {row["audio_sha256"] for row in validation}
    eligible = {
        source: [
            row
            for row in values
            if row["source"] == source
            and row["transcript"].strip()
            and row["audio_sha256"] not in validation_audio
            and (ROOT / row["audio_path"]).is_file()
        ]
        for source in ("tsc", "mediaspeech", "cv_spontaneous")
    }
    if len(eligible["tsc"]) < BUCKETS["tsc_anchor_unchanged"]:
        raise RuntimeError("BLOCKED_A7_TSC_ANCHOR_CAPACITY")
    if any(not eligible[source] for source in ("mediaspeech", "cv_spontaneous")):
        raise RuntimeError("BLOCKED_A7_PHONE_LIKE_CAPACITY")
    import random

    rng = random.Random(SEED)
    anchor = rng.sample(eligible["tsc"], BUCKETS["tsc_anchor_unchanged"])
    phone = {key: list(value) for key, value in eligible.items() if key != "tsc"}
    rows, allocation = [], []
    occurrence = Counter()

    def append(row: dict, source_bucket: str, augmentation_bucket: str) -> None:
        index = len(rows)
        occurrence[row["sample_id"]] += 1
        local_seed = SEED + index
        rows.append(
            {
                "schedule_index": index,
                "microstep": index,
                "optimizer_step": index // 16 + 1,
                "role": "acoustic",
                "sample_id": row["sample_id"],
                "source": row["source"],
                "source_bucket": source_bucket,
                "augmentation_bucket": augmentation_bucket,
                "audio_sha256": row["audio_sha256"],
                "deterministic_seed": local_seed,
                "augmentation_parameters": policy(augmentation_bucket, local_seed),
                "effective_duration_seconds": row["duration_seconds"],
                "occurrence_count": occurrence[row["sample_id"]],
            }
        )

    for row in anchor:
        append(row, "tsc_anchor", "tsc_anchor_unchanged")
    for bucket, target in BUCKETS.items():
        if bucket == "tsc_anchor_unchanged":
            continue
        split = hamilton(target, phone)
        for source in sorted(split):
            chosen = rng.sample(phone[source], split[source])
            allocation.append(
                {
                    "source": source,
                    "augmentation_bucket": bucket,
                    "eligible_population": len(phone[source]),
                    "allocated_occurrences": split[source],
                    "realized_occurrences": len(chosen),
                    "unique_sample_count": len({row["sample_id"] for row in chosen}),
                    "reuse_count": 0,
                }
            )
            for row in chosen:
                append(row, "phone_like", bucket)
    rng.shuffle(rows)
    for index, row in enumerate(rows):
        row["schedule_index"] = row["microstep"] = index
        row["optimizer_step"] = index // 16 + 1
    assignments = [
        {
            key: row[key]
            for key in (
                "schedule_index",
                "sample_id",
                "source",
                "source_bucket",
                "augmentation_bucket",
                "audio_sha256",
                "augmentation_parameters",
                "deterministic_seed",
                "occurrence_count",
                "effective_duration_seconds",
            )
        }
        for row in rows
    ]
    source_manifest = [
        {
            "sample_id": row["sample_id"],
            "source": row["source"],
            "source_bucket": "tsc_anchor" if row["source"] == "tsc" else "phone_like",
            "audio_sha256": row["audio_sha256"],
            "duration_seconds": row["duration_seconds"],
        }
        for row in values
        if row["source"] in eligible
    ]
    write_jsonl(OUT / "a7_sample_schedule.jsonl", rows)
    write_jsonl(OUT / "a7_augmentation_assignment.jsonl", assignments)
    write_jsonl(OUT / "a7_source_bucket_manifest.jsonl", source_manifest)
    lock = {
        "status": "PASSED",
        "seed": SEED,
        "schedule_rows": len(rows),
        "bucket_counts": Counter(row["augmentation_bucket"] for row in rows),
        "source_counts": Counter(row["source"] for row in rows),
        "allocations": allocation,
        "implementation": IMPLEMENTATION_ID,
        "implementation_sha256": digest(ROOT / "src/whisper_arge/a7_augmentation.py"),
        "schedule_sha256": digest(OUT / "a7_sample_schedule.jsonl"),
        "assignment_sha256": digest(OUT / "a7_augmentation_assignment.jsonl"),
        "source_bucket_manifest_sha256": digest(OUT / "a7_source_bucket_manifest.jsonl"),
        "train_manifest_sha256": digest(train_path),
        "validation_manifest_sha256": digest(validation_path),
        "validation_audio_overlap": 0,
    }
    (OUT / "a7_schedule_lock.json").write_text(
        json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "PASSED",
                "schedule_rows": len(rows),
                "source_counts": lock["source_counts"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
