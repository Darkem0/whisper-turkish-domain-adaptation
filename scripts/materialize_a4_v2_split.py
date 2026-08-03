"""Authorized deterministic A4 group-disjoint materialization; no model calls."""

from __future__ import annotations
import hashlib, json, random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/materialized/training_a4_v2"
TRAIN = ROOT / "data/materialized/training_v2d/target_train_v2d.jsonl"
VAL = ROOT / "data/materialized/training_a3_v2/a3_validation_manifest.jsonl"
SEED = 20260730


def rows(path):
    return [json.loads(x) for x in path.read_text(encoding="utf8").splitlines() if x]


def save(path, values):
    path.write_text(
        "".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in values),
        encoding="utf8",
    )


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def group(row, validation=False):
    source = row["source"] if validation else row["corpus"]
    stable = row["stable_source_id"] if validation else row["source_stable_id"]
    return f"{source}:source_stable_id:{stable}"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    train, valid = rows(TRAIN), rows(VAL)
    assert (
        len(valid) == 9081
        and len({r["sample_id"] for r in valid}) == 9081
        and len({r["audio_sha256"] for r in valid}) == 9081
    )
    validation = [
        {
            "sample_id": r["sample_id"],
            "audio_path": r["audio_path"],
            "transcript": r["transcript"],
            "source": r["source"],
            "duration_seconds": r["duration_seconds"],
            "audio_sha256": r["audio_sha256"],
            "resolved_group_key": group(r, True),
            "group_key_source_field": "source_stable_id",
            "assigned_split": "validation",
        }
        for r in valid
    ]
    vg = {r["resolved_group_key"] for r in validation}
    va = {r["audio_sha256"] for r in validation}
    material = []
    purge = []
    for r in train:
        item = {
            "sample_id": r["source_sample_id"],
            "audio_path": r["audio_path"],
            "transcript": r["transcript"],
            "source": r["corpus"],
            "duration_seconds": r["duration"],
            "audio_sha256": r["audio_sha256"],
            "resolved_group_key": group(r),
            "group_key_source_field": "source_stable_id",
            "assigned_split": "train",
        }
        if item["audio_sha256"] in va or item["resolved_group_key"] in vg:
            purge.append(item)
        else:
            material.append(item)
    material.sort(key=lambda r: r["sample_id"])
    validation.sort(key=lambda r: r["sample_id"])
    assert not ({r["audio_sha256"] for r in material} & va) and not (
        {r["resolved_group_key"] for r in material} & vg
    )
    save(OUT / "a4_train_manifest.jsonl", material)
    save(OUT / "a4_validation_manifest.jsonl", validation)
    save(OUT / "a4_replay_manifest.jsonl", [])
    by_source = {}
    for r in material:
        by_source.setdefault(r["source"], []).append(r)
    rng = random.Random(SEED)
    [rng.shuffle(v) for v in by_source.values()]
    proportions = {"tsc": 0.6316, "mediaspeech": 0.3158, "cv_spontaneous": 0.0526}
    pools = {k: iter(v * 100) for k, v in by_source.items()}
    schedule = []
    choices = []
    for source, p in proportions.items():
        choices += [source] * round(p * 10000)
    rng.shuffle(choices)
    for microstep in range(3200):
        r = next(pools[choices[microstep % len(choices)]])
        schedule.append(
            {
                "microstep": microstep,
                "optimizer_step": microstep // 16 + 1,
                "sample_id": r["sample_id"],
                "audio_sha256": r["audio_sha256"],
                "role": "acoustic",
            }
        )
    save(OUT / "a4_sample_schedule.jsonl", schedule)
    audit = {
        "status": "PASSED",
        "seed": SEED,
        "validation_rows": len(validation),
        "train_rows": len(material),
        "purged_rows": len(purge),
        "purged_groups": len({r["resolved_group_key"] for r in purge}),
        "group_key": "source + source_stable_id",
        "validation_audio_overlap": 0,
        "validation_group_overlap": 0,
        "replay_rows": 0,
        "schedule_rows": len(schedule),
        "schedule_roles": {"acoustic": 3200, "replay": 0},
        "files": {p.name: digest(p) for p in OUT.glob("*.jsonl")},
    }
    (OUT / "a4_split_audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf8"
    )


if __name__ == "__main__":
    main()
