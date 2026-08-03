"""Resumable, read-only Phase-1 A4 training-data quality audit.

The worker reads locked A4 manifests and audio files only.  It never writes
audio, manifests, splits, transcripts, evaluation artefacts, or model state.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import re
import time
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import soundfile as sf


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
STATE = ROOT / "state"
LOGS = ROOT / "logs"
TRAIN = ROOT / "data/materialized/training_a4_v2/a4_train_manifest.jsonl"
VALIDATION = ROOT / "data/materialized/training_a4_v2/a4_validation_manifest.jsonl"
SCHEDULE = ROOT / "data/materialized/training_a4_v2/a4_sample_schedule.jsonl"
EXPECTED = {
    str(
        TRAIN.relative_to(ROOT)
    ): "8dd1b0624d2d97648f2c653ebd9f6acda814a3ff095e7894ea381e5e903acf55",
    str(
        VALIDATION.relative_to(ROOT)
    ): "864e801656175b9dc515f52d2852f1a740d2d88224ee4801fcd45806f4c09976",
    str(
        SCHEDULE.relative_to(ROOT)
    ): "5e3e531a57372f3bf990d95409e455063690bfe3ab04541c44d2df513a15b446",
}
REQUIRED = {
    "assigned_split",
    "audio_path",
    "audio_sha256",
    "duration_seconds",
    "resolved_group_key",
    "sample_id",
    "source",
    "transcript",
}
SEED = 20260801


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def heartbeat(status: str, **extra: object) -> None:
    payload = {"status": status, "pid": os.getpid(), "updated_unix": time.time(), **extra}
    atomic_json(STATE / "data_quality_audit_heartbeat.json", payload)


def jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise ValueError(f"blank JSONL line: {path}:{line_number}")
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL: {path}:{line_number}: {exc}") from exc
    return rows


def issue(
    issue_type: str,
    severity: str,
    evidence: str,
    rows: list[dict],
    split: str,
    effect: str,
    confidence: str,
    action: str,
    duration: float = 0.0,
) -> dict:
    return {
        "issue_type": issue_type,
        "severity": severity,
        "evidence": evidence,
        "affected_rows": len(rows),
        "affected_duration": round(duration, 3),
        "prevalence_percent": None,
        "train_or_validation": split,
        "likely_model_effect": effect,
        "confidence": confidence,
        "recommended_action": action,
        "sample_ids": [str(row["sample_id"]) for row in rows[:200]],
    }


def normalized_text(text: str) -> str:
    return " ".join(text.casefold().split())


def repeated_bigram(tokens: list[str]) -> bool:
    return any(
        tokens[index : index + 2] == tokens[index + 2 : index + 4]
        for index in range(max(0, len(tokens) - 3))
    )


def audio_metrics(path: Path) -> dict:
    info = sf.info(str(path))
    # Bounded blocks avoid keeping complete recordings in memory while preserving
    # read-only peak/RMS/silence measures.
    samples = 0
    sum_sq = 0.0
    sum_values = 0.0
    peak = 0.0
    clipped = 0
    near_silent = 0
    channel_energy = np.zeros(info.channels, dtype=np.float64)
    leading = 0
    trailing = 0
    seen_non_silent = False
    with sf.SoundFile(str(path)) as audio:
        while True:
            block = audio.read(65536, dtype="float32", always_2d=True)
            if not len(block):
                break
            absolute = np.abs(block)
            mono = absolute.max(axis=1)
            silent = mono < 0.001
            if not seen_non_silent:
                leading += int(np.cumprod(silent, dtype=np.int8).sum())
                seen_non_silent = bool((~silent).any())
            trailing = (
                int(np.cumprod(silent[::-1], dtype=np.int8).sum())
                if (~silent).any()
                else trailing + len(silent)
            )
            samples += int(block.size)
            sum_sq += float(np.square(block, dtype=np.float64).sum())
            sum_values += float(block.sum(dtype=np.float64))
            peak = max(peak, float(absolute.max(initial=0.0)))
            clipped += int((absolute >= 0.999).sum())
            near_silent += int((absolute < 0.001).sum())
            channel_energy += np.square(block, dtype=np.float64).sum(axis=0)
    mean_energy = channel_energy / max(1, info.frames)
    imbalance = (
        float(mean_energy.max() / max(mean_energy.min(), 1e-12)) if info.channels > 1 else 1.0
    )
    return {
        "duration": info.frames / info.samplerate,
        "samplerate": info.samplerate,
        "channels": info.channels,
        "format": info.format,
        "subtype": info.subtype,
        "peak": peak,
        "rms": (sum_sq / max(1, samples)) ** 0.5,
        "dc_offset": sum_values / max(1, samples),
        "clipping_ratio": clipped / max(1, samples),
        "near_silence_ratio": near_silent / max(1, samples),
        "leading_silence_seconds": leading / info.samplerate,
        "trailing_silence_seconds": trailing / info.samplerate,
        "channel_energy_imbalance": imbalance,
        "silent_channel": bool(info.channels > 1 and mean_energy.min() < mean_energy.max() * 0.01),
    }


def summarize_population(
    rows: list[dict], split: str
) -> tuple[list[dict], list[dict], list[dict], dict[str, dict]]:
    issues: list[dict] = []
    row_issues: list[dict] = []
    distributions: list[dict] = []
    by_id = Counter(str(row.get("sample_id")) for row in rows)
    by_audio = Counter(str(row.get("audio_sha256")) for row in rows)
    by_text = defaultdict(list)
    malformed: list[dict] = []
    placeholders: list[dict] = []
    punctuation_only: list[dict] = []
    empty: list[dict] = []
    text_stats: list[tuple[dict, int, int]] = []
    for row in rows:
        transcript = str(row.get("transcript", ""))
        by_text[normalized_text(transcript)].append(row)
        if not transcript.strip():
            empty.append(row)
        if transcript.strip() and not any(char.isalnum() for char in transcript):
            punctuation_only.append(row)
        if any(
            unicodedata.category(char).startswith("C") and char not in "\n\t" for char in transcript
        ):
            malformed.append(row)
        if re.search(r"<[^>]{1,64}>|\[[^\]]{1,64}\]", transcript):
            placeholders.append(row)
        words = transcript.split()
        text_stats.append((row, len(transcript), len(words)))
        if repeated_bigram(words):
            row_issues.append(
                {
                    "sample_id": row["sample_id"],
                    "train_or_validation": split,
                    "issue_type": "repeated_transcript_bigram",
                    "severity": "low",
                    "confidence": "weak_signal",
                }
            )
    for name, affected, severity, effect, confidence, action in (
        (
            "empty_transcript",
            empty,
            "critical",
            "invalid supervision",
            "confirmed",
            "exclude or correct only after human verification",
        ),
        (
            "punctuation_only_transcript",
            punctuation_only,
            "high",
            "degenerate supervision",
            "confirmed",
            "manual review",
        ),
        (
            "unicode_control_character",
            malformed,
            "high",
            "tokenization inconsistency",
            "confirmed",
            "manual review",
        ),
        (
            "placeholder_annotation_token",
            placeholders,
            "medium",
            "annotation leakage",
            "strong_signal",
            "manual review",
        ),
    ):
        if affected:
            issues.append(
                issue(
                    name,
                    severity,
                    f"{len(affected)} rows",
                    affected,
                    split,
                    effect,
                    confidence,
                    action,
                    sum(float(row.get("duration_seconds", 0)) for row in affected),
                )
            )
    duplicates = {
        digest: members for digest, members in by_text.items() if digest and len(members) > 1
    }
    duplicate_rows = [row for members in duplicates.values() for row in members]
    if duplicate_rows:
        issues.append(
            issue(
                "duplicate_transcript_cluster",
                "medium",
                f"{len(duplicates)} normalized-text clusters",
                duplicate_rows,
                split,
                "template overrepresentation or leakage",
                "strong_signal",
                "review clusters and group-aware sampling",
                sum(float(row.get("duration_seconds", 0)) for row in duplicate_rows),
            )
        )
    return (
        issues,
        row_issues,
        distributions,
        {"sample_id": by_id, "audio_sha256": by_audio, "text": by_text, "text_stats": text_stats},
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("full", "preflight"), default="full")
    args = parser.parse_args()
    REPORTS.mkdir(exist_ok=True)
    STATE.mkdir(exist_ok=True)
    LOGS.mkdir(exist_ok=True)
    (STATE / "data_quality_audit.pid").write_text(f"{os.getpid()}\n", encoding="utf-8")
    logging.basicConfig(
        filename=LOGS / "data-quality-audit.worker.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    state_path = STATE / "data_quality_audit_state.json"
    atomic_json(
        state_path,
        {"status": "RUNNING", "mode": args.mode, "pid": os.getpid(), "phase": "preflight"},
    )
    heartbeat("RUNNING", phase="preflight")
    actual = {relative: sha256(ROOT / relative) for relative in EXPECTED}
    preflight = {
        "expected_sha256": EXPECTED,
        "actual_sha256": actual,
        "passed": actual == EXPECTED,
        "paths": list(EXPECTED),
        "seed": SEED,
        "read_only": True,
    }
    if not preflight["passed"]:
        atomic_json(
            state_path,
            {
                "status": "BLOCKED_DATA_INTEGRITY_CRITICAL",
                "phase": "preflight",
                "preflight": preflight,
            },
        )
        heartbeat("BLOCKED_DATA_INTEGRITY_CRITICAL", phase="preflight")
        return 2
    train, validation, schedule = jsonl(TRAIN), jsonl(VALIDATION), jsonl(SCHEDULE)
    missing_fields = {
        "train": sorted(REQUIRED - set().union(*(set(row) for row in train))),
        "validation": sorted(REQUIRED - set().union(*(set(row) for row in validation))),
    }
    if any(missing_fields.values()):
        atomic_json(
            state_path,
            {
                "status": "BLOCKED_DATA_INTEGRITY_CRITICAL",
                "phase": "schema",
                "missing_fields": missing_fields,
            },
        )
        heartbeat("BLOCKED_DATA_INTEGRITY_CRITICAL", phase="schema")
        return 2
    if args.mode == "preflight":
        atomic_json(
            state_path,
            {
                "status": "PREFLIGHT_PASSED",
                "preflight": preflight,
                "train_rows": len(train),
                "validation_rows": len(validation),
                "schedule_rows": len(schedule),
            },
        )
        heartbeat("PREFLIGHT_PASSED", phase="complete")
        return 0
    atomic_json(
        state_path,
        {
            "status": "RUNNING",
            "phase": "manifest_and_text",
            "train_rows": len(train),
            "validation_rows": len(validation),
            "schedule_rows": len(schedule),
        },
    )
    train_issues, train_row_issues, _, train_meta = summarize_population(train, "train")
    validation_issues, validation_row_issues, _, validation_meta = summarize_population(
        validation, "validation"
    )
    all_ids = {str(row["sample_id"]) for row in train}
    schedule_missing = [row for row in schedule if str(row.get("sample_id")) not in all_ids]
    overlap_audio = set(train_meta["audio_sha256"]) & set(validation_meta["audio_sha256"])
    overlap_groups = {str(row["resolved_group_key"]) for row in train} & {
        str(row["resolved_group_key"]) for row in validation
    }
    issues = train_issues + validation_issues
    if schedule_missing:
        issues.append(
            issue(
                "schedule_missing_manifest_reference",
                "critical",
                f"{len(schedule_missing)} schedule references absent from train",
                schedule_missing,
                "train",
                "invalid schedule",
                "confirmed",
                "do not use schedule",
            )
        )
    if overlap_audio:
        rows = [row for row in train if str(row["audio_sha256"]) in overlap_audio] + [
            row for row in validation if str(row["audio_sha256"]) in overlap_audio
        ]
        issues.append(
            issue(
                "train_validation_audio_overlap",
                "critical",
                f"{len(overlap_audio)} shared audio hashes",
                rows,
                "both",
                "leakage",
                "confirmed",
                "block split use",
            )
        )
    if overlap_groups:
        rows = [row for row in train if str(row["resolved_group_key"]) in overlap_groups] + [
            row for row in validation if str(row["resolved_group_key"]) in overlap_groups
        ]
        issues.append(
            issue(
                "train_validation_group_overlap",
                "critical",
                f"{len(overlap_groups)} shared groups",
                rows,
                "both",
                "leakage",
                "confirmed",
                "block split use",
            )
        )
    audio_duplicates = []
    for split, metadata in (("train", train_meta), ("validation", validation_meta)):
        for digest, count in metadata["audio_sha256"].items():
            if count > 1:
                members = [
                    row
                    for row in (train if split == "train" else validation)
                    if str(row["audio_sha256"]) == digest
                ]
                audio_duplicates.append(
                    {
                        "train_or_validation": split,
                        "audio_sha256": digest,
                        "rows": count,
                        "sample_ids": "|".join(str(row["sample_id"]) for row in members[:50]),
                        "distinct_transcripts": len(
                            {normalized_text(str(row["transcript"])) for row in members}
                        ),
                    }
                )
    atomic_json(
        state_path,
        {
            "status": "RUNNING",
            "phase": "audio_scan",
            "processed_audio": 0,
            "total_audio": len(train) + len(validation),
        },
    )
    audio_rows: list[dict] = []
    for index, row in enumerate(train + validation, start=1):
        split = str(row["assigned_split"])
        path = ROOT / str(row["audio_path"])
        result = {
            "sample_id": row["sample_id"],
            "train_or_validation": split,
            "audio_path": str(row["audio_path"]),
            "manifest_duration_seconds": float(row["duration_seconds"]),
        }
        if not path.exists():
            result["audio_status"] = "missing"
        elif path.stat().st_size == 0:
            result["audio_status"] = "zero_byte"
        else:
            try:
                result.update(audio_metrics(path))
                result["audio_status"] = "ok"
            except Exception as exc:  # read-only evidence only
                result["audio_status"] = "unreadable"
                result["audio_error"] = f"{type(exc).__name__}: {exc}"
        audio_rows.append(result)
        if index % 250 == 0:
            atomic_json(
                state_path,
                {
                    "status": "RUNNING",
                    "phase": "audio_scan",
                    "processed_audio": index,
                    "total_audio": len(train) + len(validation),
                },
            )
            heartbeat(
                "RUNNING",
                phase="audio_scan",
                processed_audio=index,
                total_audio=len(train) + len(validation),
            )
    for result in audio_rows:
        if result["audio_status"] != "ok":
            source = train if result["train_or_validation"] == "train" else validation
            row = next(item for item in source if item["sample_id"] == result["sample_id"])
            severity = "critical" if result["audio_status"] in {"missing", "zero_byte"} else "high"
            issues.append(
                issue(
                    f"audio_{result['audio_status']}",
                    severity,
                    str(result.get("audio_error", result["audio_status"])),
                    [row],
                    result["train_or_validation"],
                    "unavailable or invalid acoustic supervision",
                    "confirmed",
                    "repair source then re-lock manifest",
                )
            )
        elif abs(float(result["duration"]) - float(result["manifest_duration_seconds"])) > 0.25:
            source = train if result["train_or_validation"] == "train" else validation
            row = next(item for item in source if item["sample_id"] == result["sample_id"])
            issues.append(
                issue(
                    "manifest_duration_mismatch",
                    "medium",
                    f"actual={result['duration']:.3f}, manifest={result['manifest_duration_seconds']:.3f}",
                    [row],
                    result["train_or_validation"],
                    "duration-derived filtering error",
                    "confirmed",
                    "inspect metadata provenance",
                )
            )
    distributions = []
    for split, population in (("train", train), ("validation", validation)):
        for key in ("source", "group_key_source_field"):
            for value, count in Counter(
                str(row.get(key, "NOT_AVAILABLE")) for row in population
            ).most_common():
                distributions.append(
                    {
                        "train_or_validation": split,
                        "dimension": key,
                        "value": value,
                        "rows": count,
                        "duration_seconds": round(
                            sum(
                                float(row["duration_seconds"])
                                for row in population
                                if str(row.get(key, "NOT_AVAILABLE")) == value
                            ),
                            3,
                        ),
                    }
                )
    issue_rows = train_row_issues + validation_row_issues
    with (REPORTS / "data_quality_duplicate_audio_report.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "train_or_validation",
                "audio_sha256",
                "rows",
                "sample_ids",
                "distinct_transcripts",
            ],
        )
        writer.writeheader()
        writer.writerows(audio_duplicates)
    duplicates_text = []
    for split, metadata in (("train", train_meta), ("validation", validation_meta)):
        for transcript, members in metadata["text"].items():
            if transcript and len(members) > 1:
                duplicates_text.append(
                    {
                        "train_or_validation": split,
                        "normalized_transcript": transcript,
                        "rows": len(members),
                        "sample_ids": "|".join(str(row["sample_id"]) for row in members[:50]),
                    }
                )
    with (REPORTS / "data_quality_duplicate_transcript_report.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["train_or_validation", "normalized_transcript", "rows", "sample_ids"],
        )
        writer.writeheader()
        writer.writerows(duplicates_text)
    mismatch = [
        result
        for result in audio_rows
        if result["audio_status"] == "ok"
        and (
            abs(float(result["duration"]) - float(result["manifest_duration_seconds"])) > 0.25
            or result["near_silence_ratio"] > 0.9
            or result["leading_silence_seconds"] > 2
            or result["trailing_silence_seconds"] > 2
        )
    ]
    with (REPORTS / "data_quality_audio_text_mismatch_candidates.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        fields = sorted({key for row in mismatch for key in row}) or ["sample_id"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(mismatch)
    with (REPORTS / "data_quality_distribution_summary.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["train_or_validation", "dimension", "value", "rows", "duration_seconds"],
        )
        writer.writeheader()
        writer.writerows(distributions)
    for item in issues:
        item["prevalence_percent"] = round(
            100
            * item["affected_rows"]
            / (
                len(train)
                if item["train_or_validation"] == "train"
                else len(validation)
                if item["train_or_validation"] == "validation"
                else len(train) + len(validation)
            ),
            5,
        )
    with (REPORTS / "data_quality_issue_summary.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        fields = (
            [key for key in issues[0] if key != "sample_ids"]
            if issues
            else [
                "issue_type",
                "severity",
                "evidence",
                "affected_rows",
                "affected_duration",
                "prevalence_percent",
                "train_or_validation",
                "likely_model_effect",
                "confidence",
                "recommended_action",
            ]
        )
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(
            [
                {key: value for key, value in entry.items() if key != "sample_ids"}
                for entry in issues
            ]
        )
    with (REPORTS / "data_quality_issue_rows.jsonl").open("w", encoding="utf-8") as handle:
        for entry in issues:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        for entry in issue_rows:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    rng = np.random.default_rng(SEED)
    shortlist = []
    candidates = [result for result in audio_rows if result["audio_status"] == "ok"]
    for result in rng.choice(candidates, size=min(100, len(candidates)), replace=False):
        source = train if result["train_or_validation"] == "train" else validation
        row = next(item for item in source if item["sample_id"] == result["sample_id"])
        labels = ["random_control"]
        if result["near_silence_ratio"] > 0.9:
            labels.append("near_silent_audio")
        if result["clipping_ratio"] > 0.001:
            labels.append("clipping_high_level")
        if float(result["duration"]) > 20:
            labels.append("long_utterance")
        if float(result["duration"]) < 1:
            labels.append("short_answer")
        if re.search(r"\d|₺|TL|lira|tarih", str(row["transcript"]), re.I):
            labels.append("number_date_currency")
        shortlist.append(
            {
                "seed": SEED,
                "selection_reason": "|".join(labels),
                "sample_id": row["sample_id"],
                "audio_path": row["audio_path"],
                "transcript": row["transcript"],
                "train_or_validation": result["train_or_validation"],
                "source": row.get("source", "NOT_AVAILABLE"),
                "resolved_group_key": row.get("resolved_group_key", "NOT_AVAILABLE"),
                "automatic_risk_signals": "|".join(labels[1:]) or "none",
            }
        )
    with (REPORTS / "data_quality_manual_review_sample.jsonl").open(
        "w", encoding="utf-8"
    ) as handle:
        for entry in shortlist:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    (REPORTS / "data_quality_manual_review_sampling_plan.md").write_text(
        "# Phase-2 manual review sampling plan\n\nDeterministic seed: `20260801`. The current automated worker creates a 100-row control shortlist and multi-labels detectable risks. Channel, clean/noisy telephone, G.711, crosstalk, high/low WER and agent/customer strata are `NOT_AVAILABLE` unless present in locked A4 metadata or existing artefacts; they must be added only from authoritative sources during manual review.\n",
        encoding="utf-8",
    )
    critical = sum(entry["severity"] == "critical" for entry in issues)
    high = sum(entry["severity"] == "high" for entry in issues)
    terminal = (
        "BLOCKED_DATA_INTEGRITY_CRITICAL" if critical else "READY_FOR_MANUAL_DATA_QUALITY_REVIEW"
    )
    report = [
        "# Automatic data quality audit",
        "",
        f"Terminal: `{terminal}`.",
        "",
        f"- Train rows: {len(train):,}; validation rows: {len(validation):,}.",
        f"- Manifest duration: {sum(float(row['duration_seconds']) for row in train + validation):,.2f} seconds.",
        f"- Audio files scanned: {len(audio_rows):,}.",
        f"- Issue categories: critical={critical}, high={high}, medium={sum(entry['severity'] == 'medium' for entry in issues)}, low={sum(entry['severity'] == 'low' for entry in issues)}.",
        "",
        "All audio checks are read-only. Audio–text mismatch candidates are suspicion signals requiring human review, not confirmed label errors.",
    ]
    (REPORTS / "data_quality_automatic_audit.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    (REPORTS / "data_quality_representation_analysis.md").write_text(
        "# Representation analysis\n\nSee `data_quality_distribution_summary.csv`. Fields absent from the locked A4 manifests are reported as `NOT_AVAILABLE`; no source, speaker, call, project, agent/customer or codec labels are invented.\n",
        encoding="utf-8",
    )
    reproducibility = {
        "status": terminal,
        "worker": "scripts/run_data_quality_automatic_audit.py",
        "seed": SEED,
        "preflight": preflight,
        "input_rows": {
            "train": len(train),
            "validation": len(validation),
            "schedule": len(schedule),
        },
        "audio_files_scanned": len(audio_rows),
        "read_only": True,
    }
    atomic_json(REPORTS / "data_quality_audit_reproducibility.json", reproducibility)
    lock_paths = [
        REPORTS / name
        for name in (
            "data_quality_automatic_audit.md",
            "data_quality_issue_summary.csv",
            "data_quality_issue_rows.jsonl",
            "data_quality_distribution_summary.csv",
            "data_quality_duplicate_audio_report.csv",
            "data_quality_duplicate_transcript_report.csv",
            "data_quality_audio_text_mismatch_candidates.csv",
            "data_quality_representation_analysis.md",
            "data_quality_manual_review_sampling_plan.md",
            "data_quality_manual_review_sample.jsonl",
            "data_quality_audit_reproducibility.json",
        )
    ]
    atomic_json(
        REPORTS / "data_quality_audit_artifact_lock.json",
        {str(path.relative_to(ROOT)): sha256(path) for path in lock_paths},
    )
    (REPORTS / "next_executable_stage.md").write_text(
        f"# Next executable stage\n\n`{terminal}`\n\nPhase 2 human data-quality review is required; A5 is not authorized.\n",
        encoding="utf-8",
    )
    atomic_json(
        state_path,
        {
            "status": terminal,
            "phase": "completed",
            "train_rows": len(train),
            "validation_rows": len(validation),
            "audio_files_scanned": len(audio_rows),
            "issue_categories": {
                level: sum(entry["severity"] == level for entry in issues)
                for level in ("critical", "high", "medium", "low")
            },
        },
    )
    heartbeat(terminal, phase="completed", audio_files_scanned=len(audio_rows))
    return 0 if terminal == "READY_FOR_MANUAL_DATA_QUALITY_REVIEW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
