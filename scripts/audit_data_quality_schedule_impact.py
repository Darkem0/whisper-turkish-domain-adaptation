"""Read-only intersection of completed data-quality findings and A2/A3/A4 schedules."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from whisper_arge.normalization import normalize_turkish


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
TRAIN = ROOT / "data/materialized/training_a4_v2/a4_train_manifest.jsonl"
VALIDATION = ROOT / "data/materialized/training_a4_v2/a4_validation_manifest.jsonl"
SCHEDULES = {
    "A2": ROOT / "data/materialized/training_v2d/sample_schedule_v2d_200.jsonl",
    "A3_v2": ROOT / "data/materialized/training_a3_v2/a3_sample_schedule_200.jsonl",
    "A4_v2": ROOT / "data/materialized/training_a4_v2/a4_sample_schedule.jsonl",
}
EMPTY = {"cvsp-68089", "cvsp-72082", "cvsp-78549", "cvsp-78550", "cvsp-79391", "cvsp-84256", "cvsp-91623"}
PLACEHOLDERS = {"cvsp-72098", "cvsp-78486"}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def duplicate_ids(rows: list[dict]) -> set[str]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        key = " ".join(normalize_turkish(str(row["transcript"])).split())
        if key:
            groups[key].append(row)
    return {str(row["sample_id"]) for members in groups.values() if len(members) > 1 for row in members}


def main() -> None:
    train, validation = read_jsonl(TRAIN), read_jsonl(VALIDATION)
    duplicate_train, duplicate_validation = duplicate_ids(train), duplicate_ids(validation)
    issues = {
        "empty_transcript_train": EMPTY,
        "duplicate_transcript_train": duplicate_train,
        "duplicate_transcript_validation": duplicate_validation,
        "placeholder_validation": PLACEHOLDERS,
    }
    intersections: list[dict] = []
    for experiment, path in SCHEDULES.items():
        if not path.exists():
            intersections.append({"experiment": experiment, "schedule_path": str(path.relative_to(ROOT)), "schedule_status": "MISSING", "issue_type": "all", "issue_rows_in_schedule": "MISSING", "uses": "MISSING", "microbatch_percent": "MISSING", "sample_id_matching": "NOT_EVALUABLE"})
            continue
        schedule = read_jsonl(path)
        for issue_type, sample_ids in issues.items():
            matched = [row for row in schedule if str(row.get("sample_id")) in sample_ids]
            intersections.append({"experiment": experiment, "schedule_path": str(path.relative_to(ROOT)), "schedule_status": "PRESENT", "issue_type": issue_type, "issue_rows_in_schedule": len({str(row["sample_id"]) for row in matched}), "uses": len(matched), "total_microbatches": len(schedule), "microbatch_percent": round(100 * len(matched) / len(schedule), 8), "sample_id_matching": "EXACT"})
    with (REPORTS / "data_quality_schedule_intersections.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=sorted({key for row in intersections for key in row}))
        writer.writeheader()
        writer.writerows(intersections)

    by_experiment: dict[str, dict[str, dict]] = defaultdict(dict)
    for row in intersections:
        by_experiment[str(row["experiment"])][str(row["issue_type"])] = row
    text = ["# Data-quality experiment schedule-impact audit", "", "This is an exact, read-only `sample_id` intersection with locked schedules. Duplicate findings are exposure signals, not confirmed label errors.", "", "## Input population", "", f"- Empty train transcripts: {len(EMPTY)}.", f"- Duplicate transcript members: train={len(duplicate_train)}, validation={len(duplicate_validation)}.", f"- Placeholder validation rows: {len(PLACEHOLDERS)} of {len(validation)} local-validation rows ({100 * len(PLACEHOLDERS) / len(validation):.5f}%).", "", "## Per-experiment impact"]
    for experiment, values in by_experiment.items():
        empty = values.get("empty_transcript_train", {})
        dup = values.get("duplicate_transcript_train", {})
        text += ["", f"### {experiment}", "", f"- Empty-transcript exposure: {empty.get('uses', 'MISSING')} uses ({empty.get('microbatch_percent', 'MISSING')}% of locked microbatches).", f"- Train duplicate-cluster exposure: {dup.get('uses', 'MISSING')} uses ({dup.get('microbatch_percent', 'MISSING')}% of locked microbatches).", f"- Placeholder validation theoretical upper bound: 2 / 9,081 = {100 * 2 / len(validation):.5f}% of rows. The rows are validation-only and have no training-schedule exposure.", "- Interpretation: a schedule intersection alone cannot attribute broad, cross-dataset A2/A3/A4 gains or regressions to these low-prevalence data-quality findings; it only quantifies potential exposure."]
    text += ["", "## Conclusion", "", "No schedule is modified. The full row-level evidence is in `data_quality_schedule_intersections.csv`."]
    (REPORTS / "data_quality_experiment_impact_audit.md").write_text("\n".join(text) + "\n", encoding="utf-8")
    print(json.dumps({"status": "COMPLETED", "intersections": intersections}, ensure_ascii=False))


if __name__ == "__main__":
    main()
