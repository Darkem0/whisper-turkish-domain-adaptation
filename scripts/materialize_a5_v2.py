"""Materialize the authorized A5 clean population and matched zero-replay schedule."""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/materialized/training_a4_v2/a4_train_manifest.jsonl"
VALIDATION = ROOT / "data/materialized/training_a4_v2/a4_validation_manifest.jsonl"
SCHEDULE = ROOT / "data/materialized/training_a4_v2/a4_sample_schedule.jsonl"
OUT = ROOT / "data/materialized/training_a5_v2"
REMOVED = {"cvsp-68089", "cvsp-72082", "cvsp-78549", "cvsp-78550", "cvsp-79391", "cvsp-84256", "cvsp-91623"}
SEED = 20260730


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    source, validation, schedule = read_jsonl(SOURCE), read_jsonl(VALIDATION), read_jsonl(SCHEDULE)
    removed_rows = [row for row in source if str(row["sample_id"]) in REMOVED]
    clean = [row for row in source if str(row["sample_id"]) not in REMOVED]
    if len(source) != 172238 or len(removed_rows) != 7 or len(clean) != 172231:
        raise ValueError("A5 clean-population cardinality mismatch")
    if any(str(row.get("transcript", "")).strip() == "" for row in clean):
        raise ValueError("empty transcript remained in A5 training population")
    clean_by_id = {str(row["sample_id"]): row for row in clean}
    if len(clean_by_id) != len(clean):
        raise ValueError("duplicate A5 train sample_id")
    candidates = sorted(clean_by_id)
    rng = random.Random(SEED)
    replacements: list[dict] = []
    output_schedule: list[dict] = []
    for row in schedule:
        updated = dict(row)
        original = str(row["sample_id"])
        if original in REMOVED:
            # Deterministic uniform selection over valid locked A5 population.
            replacement = candidates[rng.randrange(len(candidates))]
            updated["sample_id"] = replacement
            updated["audio_sha256"] = clean_by_id[replacement]["audio_sha256"]
            replacements.append({"microstep": row["microstep"], "optimizer_step": row["optimizer_step"], "old_sample_id": original, "new_sample_id": replacement, "replacement_reason": "removed_objectively_empty_transcript", "seed": SEED})
        output_schedule.append(updated)
    if len(replacements) != 52 or len(output_schedule) != 3200:
        raise ValueError("matched replacement cardinality mismatch")
    if any(str(row["sample_id"]) not in clean_by_id for row in output_schedule):
        raise ValueError("A5 schedule references non-clean row")
    write_jsonl(OUT / "a5_train_manifest.jsonl", clean)
    write_jsonl(OUT / "a5_removed_rows.jsonl", removed_rows)
    write_jsonl(OUT / "a5_sample_schedule.jsonl", output_schedule)
    write_jsonl(OUT / "a5_schedule_replacement_ledger.jsonl", replacements)
    (OUT / "a5_replay_manifest.jsonl").write_text("", encoding="utf-8")
    write_json(OUT / "a5_validation_manifest.reference.json", {"path": str(VALIDATION.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(VALIDATION), "rows": len(validation), "immutable": True})
    audio_overlap = {str(row["audio_sha256"]) for row in clean} & {str(row["audio_sha256"]) for row in validation}
    group_overlap = {str(row["resolved_group_key"]) for row in clean} & {str(row["resolved_group_key"]) for row in validation}
    replacement_ids = [row["new_sample_id"] for row in replacements]
    audit = {"status": "PASSED", "train_rows": len(clean), "validation_rows": len(validation), "empty_transcript_train": 0, "train_validation_audio_overlap": len(audio_overlap), "train_validation_group_overlap": len(group_overlap), "schedule_rows": len(output_schedule), "acoustic_microbatches": sum(row["role"] == "acoustic" for row in output_schedule), "replay_microbatches": sum(row["role"] != "acoustic" for row in output_schedule), "empty_schedule_exposure": sum(row["sample_id"] in REMOVED for row in output_schedule), "replacement_occurrences": len(replacements), "replacement_unique_samples": len(set(replacement_ids)), "replacement_duplicate_sampling_count": len(replacement_ids) - len(set(replacement_ids)), "seed": SEED}
    if audio_overlap or group_overlap or audit["empty_schedule_exposure"] or audit["replay_microbatches"]:
        audit["status"] = "BLOCKED"
    write_json(OUT / "a5_data_integrity_audit.json", audit)
    write_json(OUT / "a5_data_cleanup_ledger.json", {"source_manifest": str(SOURCE.relative_to(ROOT)).replace("\\", "/"), "source_sha256": sha(SOURCE), "removed_count": len(removed_rows), "removed_sample_ids": sorted(REMOVED), "reason": "automatic audit confirmed empty transcript", "a5_train_manifest": "data/materialized/training_a5_v2/a5_train_manifest.jsonl", "a5_train_sha256": sha(OUT / "a5_train_manifest.jsonl")})
    write_json(OUT / "a5_schedule_audit.json", audit)
    write_json(OUT / "a5_data_manifest.lock.json", {"schema_version": 1, "status": audit["status"], "materialized": {name: {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(path)} for name, path in {"train": OUT / "a5_train_manifest.jsonl", "replay": OUT / "a5_replay_manifest.jsonl", "removed_rows": OUT / "a5_removed_rows.jsonl", "schedule": OUT / "a5_sample_schedule.jsonl", "replacement_ledger": OUT / "a5_schedule_replacement_ledger.jsonl", "validation_reference": OUT / "a5_validation_manifest.reference.json"}.items()}, "validation": {"path": str(VALIDATION.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(VALIDATION), "rows": len(validation)}, "audit": audit})
    print(json.dumps(audit, ensure_ascii=False))


if __name__ == "__main__":
    main()
