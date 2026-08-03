"""Materialize deterministic, leakage-safe A3_v2 data roles without starting training."""

from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "materialized" / "training_a3_v2"
SEED = 42
VALIDATION_RATIO = 0.05
REPLAY_RATIO = 0.10
SOURCES = (
    ("tsc", ROOT / "data/materialized/tsc_v2a/tsc_train_v2a.jsonl"),
    ("mediaspeech", ROOT / "data/materialized/mediaspeech_v2d/mediaspeech_train_v2d.jsonl"),
    ("cv_spontaneous", ROOT / "data/materialized/cv_spontaneous_v2c/cv_spontaneous_train_v2c.jsonl"),
)
EVALUATION = (
    ROOT / "data/materialized/mediaspeech_v2d/paired/mediaspeech_holdout_paired_v2d.jsonl",
    ROOT / "data/materialized/hf_v2d/cv_scripted_test_v2d.jsonl",
    ROOT / "data/materialized/fleurs_tr_v2d/fleurs_tr_test_v2d.jsonl",
    ROOT / "data/materialized/cv_spontaneous_v2c/cv_spontaneous_holdout_v2c.jsonl",
    ROOT / "data/materialized/tsc_v2a/tsc_full_v2a.jsonl",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def stable_rank(value: str) -> str:
    return hashlib.sha256(f"{SEED}:{value}".encode("utf-8")).hexdigest()


def canonical(corpus: str, item: dict) -> dict:
    audio = str(item.get("audio") or "")
    transcript = str(item.get("reference") or "").strip()
    audio_hash = str(item.get("audio_sha256") or "")
    missing = []
    if not audio:
        missing.append("audio")
    if not transcript:
        missing.append("reference")
    if len(audio_hash) != 64:
        missing.append("audio_sha256")
    if item.get("duration_seconds") is None:
        missing.append("duration_seconds")
    if missing:
        raise ValueError(
            f"missing_or_invalid_fields={','.join(missing)}: {corpus}:{item.get('sample_id')}"
        )
    absolute_audio = ROOT / Path(audio)
    if not absolute_audio.is_file():
        raise FileNotFoundError(f"missing audio: {absolute_audio}")
    sample_id = str(item["sample_id"])
    stable_source_id = str(item.get("stable_source_id") or sample_id)
    speaker = item.get("speaker_id")
    # Where no speaker id exists, each source recording/file group is isolated.
    group = f"speaker:{speaker}" if speaker else f"recording:{item.get('source_record_id') or stable_source_id}"
    return {
        "sample_id": sample_id,
        "stable_source_id": stable_source_id,
        "audio_path": audio.replace("\\", "/"),
        "audio_sha256": audio_hash,
        "transcript": transcript,
        "transcript_sha256": hashlib.sha256(transcript.encode("utf-8")).hexdigest(),
        "dataset_id": str(item["dataset_id"]),
        "dataset_revision": str(item.get("dataset_revision") or "MISSING"),
        "source": corpus,
        "source_split": str(item.get("split") or "MISSING"),
        "duration_seconds": float(item["duration_seconds"]),
        "speaker_id": speaker,
        "leakage_group": group,
    }


def write_jsonl(path: Path, rows: list[dict]) -> str:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return sha256(path)


def validation_groups(rows: list[dict]) -> set[str]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        groups[row["leakage_group"]].append(row)
    target = max(1, math.ceil(len(rows) * VALIDATION_RATIO))
    chosen: set[str] = set()
    count = 0
    for group, members in sorted(groups.items(), key=lambda pair: stable_rank(pair[0])):
        if count >= target:
            break
        chosen.add(group)
        count += len(members)
    return chosen


def canonical_sort_key(row: dict) -> tuple[str, str, str]:
    return (row["dataset_id"], row["stable_source_id"], row["sample_id"])


def main() -> None:
    eval_audio: set[str] = set()
    eval_sources: set[tuple[str, str]] = set()
    eval_speakers: set[tuple[str, str]] = set()
    for path in EVALUATION:
        for item in read_jsonl(path):
            dataset = str(item.get("dataset_id") or "")
            eval_audio.add(str(item.get("audio_sha256") or ""))
            eval_sources.add((dataset, str(item.get("stable_source_id") or "")))
            if item.get("speaker_id"):
                eval_speakers.add((dataset, str(item["speaker_id"])))

    by_source: dict[str, list[dict]] = {}
    excluded = Counter()
    invalid_rows: list[dict] = []
    for corpus, path in SOURCES:
        kept: list[dict] = []
        for item in read_jsonl(path):
            try:
                row = canonical(corpus, item)
            except (ValueError, FileNotFoundError) as error:
                invalid_rows.append(
                    {
                        "source": corpus,
                        "sample_id": str(item.get("sample_id") or "MISSING"),
                        "reason": str(error),
                    }
                )
                continue
            if (
                row["audio_sha256"] in eval_audio
                or (row["dataset_id"], row["stable_source_id"]) in eval_sources
                or (row["speaker_id"] and (row["dataset_id"], str(row["speaker_id"])) in eval_speakers)
            ):
                excluded[corpus] += 1
                continue
            kept.append(row)
        if not kept:
            raise ValueError(f"no eligible rows for source: {corpus}")
        by_source[corpus] = kept

    validation, remaining = [], []
    for corpus, rows in by_source.items():
        groups = validation_groups(rows)
        validation.extend(row for row in rows if row["leakage_group"] in groups)
        remaining.extend(row for row in rows if row["leakage_group"] not in groups)

    replay, acoustic = [], []
    for corpus in sorted(by_source):
        rows = [row for row in remaining if row["source"] == corpus]
        replay_count = max(1, round(len(rows) * REPLAY_RATIO))
        ordered = sorted(rows, key=lambda row: stable_rank("replay:" + row["sample_id"]))
        replay_ids = {row["sample_id"] for row in ordered[:replay_count]}
        replay.extend(row for row in rows if row["sample_id"] in replay_ids)
        acoustic.extend(row for row in rows if row["sample_id"] not in replay_ids)

    validation.sort(key=canonical_sort_key)
    replay.sort(key=canonical_sort_key)
    acoustic.sort(key=canonical_sort_key)
    sets = {"validation": validation, "replay": replay, "acoustic": acoustic}
    ids = {name: {row["sample_id"] for row in rows} for name, rows in sets.items()}
    hashes = {row["audio_sha256"] for row in validation}
    if ids["validation"] & ids["replay"] or ids["validation"] & ids["acoustic"] or ids["replay"] & ids["acoustic"]:
        raise ValueError("manifest sample_id overlap")
    if hashes & {row["audio_sha256"] for row in replay + acoustic}:
        raise ValueError("manifest audio SHA-256 overlap with validation")

    OUT.mkdir(parents=True, exist_ok=True)
    paths = {
        "a3_train_manifest": OUT / "a3_train_manifest.jsonl",
        "a3_validation_manifest": OUT / "a3_validation_manifest.jsonl",
        "a3_replay_manifest": OUT / "a3_replay_manifest.jsonl",
    }
    manifest_hashes = {
        "a3_train_manifest": write_jsonl(paths["a3_train_manifest"], acoustic),
        "a3_validation_manifest": write_jsonl(paths["a3_validation_manifest"], validation),
        "a3_replay_manifest": write_jsonl(paths["a3_replay_manifest"], replay),
    }

    # Exact 90/10 microbatch role counts for the 200-step, accumulation-16 schedule.
    roles = ["acoustic"] * 2880 + ["clean_replay"] * 320
    rng = random.Random(SEED)
    rng.shuffle(roles)
    pools = {"acoustic": acoustic, "clean_replay": replay}
    schedule = []
    for microstep, role in enumerate(roles):
        item = pools[role][rng.randrange(len(pools[role]))]
        schedule.append({"microstep": microstep, "role": role, "sample_id": item["sample_id"], "source": item["source"]})
    schedule_path = OUT / "a3_sample_schedule_200.jsonl"
    schedule_hash = write_jsonl(schedule_path, schedule)

    metadata = {
        "schema_version": 1,
        "status": "MATERIALIZED_NOT_TRAINED",
        "seed": SEED,
        "validation_ratio_target": VALIDATION_RATIO,
        "clean_replay_ratio": REPLAY_RATIO,
        "manifests": {
            name: {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": manifest_hashes[name], "rows": len(sets[{"a3_train_manifest": "acoustic", "a3_validation_manifest": "validation", "a3_replay_manifest": "replay"}[name]])}
            for name, path in paths.items()
        },
        "schedule": {"path": str(schedule_path.relative_to(ROOT)).replace("\\", "/"), "sha256": schedule_hash, "microbatches": len(schedule), "role_counts": dict(Counter(roles))},
        "source_rows": {name: len(rows) for name, rows in by_source.items()},
        "excluded_due_to_frozen_evaluation": dict(excluded),
        "excluded_invalid_rows": invalid_rows,
        "validation_rows_by_source": dict(Counter(row["source"] for row in validation)),
        "replay_rows_by_source": dict(Counter(row["source"] for row in replay)),
        "acoustic_rows_by_source": dict(Counter(row["source"] for row in acoustic)),
        "leakage_policy": "speaker_id when present; otherwise stable source recording/file group; validation is disjoint by sample_id and audio_sha256.",
    }
    metadata_path = OUT / "a3_manifest_materialization.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
