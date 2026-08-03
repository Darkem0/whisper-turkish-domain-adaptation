"""Build a read-only Phase-2 package from completed A4 automatic-audit evidence."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import numpy as np
import soundfile as sf

from whisper_arge.normalization import normalize_turkish


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
OUTPUT = REPORTS / "manual_data_quality_review"
TRAIN = ROOT / "data/materialized/training_a4_v2/a4_train_manifest.jsonl"
VALIDATION = ROOT / "data/materialized/training_a4_v2/a4_validation_manifest.jsonl"
SEED = 20260802
EMPTY_IDS = {"cvsp-68089", "cvsp-72082", "cvsp-78549", "cvsp-78550", "cvsp-79391", "cvsp-84256", "cvsp-91623"}
PLACEHOLDER_IDS = {"cvsp-72098", "cvsp-78486"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def audio_info(path: Path) -> dict:
    info = sf.info(str(path))
    samples = 0
    sum_sq = 0.0
    peak = 0.0
    with sf.SoundFile(str(path)) as source:
        while True:
            block = source.read(65536, dtype="float32", always_2d=True)
            if not len(block):
                break
            samples += int(block.size)
            sum_sq += float(np.square(block, dtype=np.float64).sum())
            peak = max(peak, float(np.abs(block).max(initial=0.0)))
    return {"actual_duration_seconds": round(info.frames / info.samplerate, 6), "sample_rate_hz": info.samplerate, "channels": info.channels, "format": info.format, "subtype": info.subtype, "peak_amplitude": peak, "rms": (sum_sq / max(1, samples)) ** .5}


def text_key(text: str) -> str:
    return " ".join(normalize_turkish(text).split())


def metadata(row: dict) -> dict:
    return {
        "sample_id": str(row["sample_id"]),
        "audio_path": str(row["audio_path"]),
        "audio_sha256": str(row["audio_sha256"]),
        "manifest_duration_seconds": row["duration_seconds"],
        "source": row.get("source", "NOT_AVAILABLE"),
        "resolved_group_key": row.get("resolved_group_key", "NOT_AVAILABLE"),
        "group_key_source_field": row.get("group_key_source_field", "NOT_AVAILABLE"),
        "speaker": row.get("speaker", "NOT_AVAILABLE"),
        "recording": row.get("recording", "NOT_AVAILABLE"),
        "call": row.get("call", "NOT_AVAILABLE"),
        "channel": row.get("channel", "NOT_AVAILABLE"),
        "train_or_validation": row["assigned_split"],
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    keys = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    train, validation = read_jsonl(TRAIN), read_jsonl(VALIDATION)
    by_id = {str(row["sample_id"]): row for row in train + validation}
    required = EMPTY_IDS | PLACEHOLDER_IDS
    missing = required - set(by_id)
    if missing:
        raise RuntimeError(f"required audit sample IDs missing from locked manifests: {sorted(missing)}")

    empty_rows: list[dict] = []
    queue: dict[str, dict] = {}
    for sample_id in sorted(EMPTY_IDS):
        row = by_id[sample_id]
        raw = str(row["transcript"])
        record = {
            **metadata(row),
            **audio_info(ROOT / str(row["audio_path"])),
            "raw_transcript_repr": repr(raw),
            "transcript_is_empty": raw == "",
            "transcript_is_whitespace_only": bool(raw) and not raw.strip(),
            "unicode_code_points": " ".join(f"U+{ord(char):04X}" for char in raw) or "NONE",
            "control_character_present": any(unicodedata.category(char).startswith("C") for char in raw),
            "existing_vad_or_speech_ratio": "NOT_AVAILABLE",
            "selection_reason": "automatic_audit: empty_transcript critical finding",
            "audible_speech": "",
            "label_status": "",
            "proposed_action": "",
            "reviewer_note": "",
        }
        empty_rows.append(record)
        queue[sample_id] = {**metadata(row), "transcript": raw, "selection_labels": ["empty_transcript"], "selection_reason": record["selection_reason"], "automatic_risk_signals": ["empty_transcript"]}
    write_csv(OUTPUT / "empty_transcripts.csv", empty_rows)

    placeholder_rows: list[dict] = []
    for sample_id in sorted(PLACEHOLDER_IDS):
        row = by_id[sample_id]
        raw = str(row["transcript"])
        tokens = re.findall(r"<[^>]{1,64}>|\[[^\]]{1,64}\]", raw)
        record = {
            **metadata(row),
            "raw_transcript": raw,
            "normalization_before": raw,
            "normalization_after": normalize_turkish(raw),
            "unicode_code_points": " ".join(f"U+{ord(char):04X}" for char in raw),
            "placeholder_tokens": "|".join(tokens) or "NOT_DETECTED",
            "placeholder_spoken": "",
            "benchmark_status": "",
            "proposed_future_validation_action": "",
            "reviewer_note": "",
            "selection_reason": "automatic_audit: placeholder_annotation_token medium finding",
        }
        placeholder_rows.append(record)
        existing = queue.setdefault(sample_id, {**metadata(row), "transcript": raw, "selection_labels": [], "selection_reason": "", "automatic_risk_signals": []})
        existing["selection_labels"].append("placeholder_annotation_token")
        existing["automatic_risk_signals"].append("placeholder_annotation_token")
        existing["selection_reason"] = "automatic_audit: placeholder_annotation_token medium finding"
    write_csv(OUTPUT / "placeholder_tokens.csv", placeholder_rows)

    clusters: list[dict] = []
    cluster_members: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in train + validation:
        key = text_key(str(row["transcript"]))
        if key:
            cluster_members[(str(row["assigned_split"]), key)].append(row)
    for (split, normalized), members in cluster_members.items():
        if len(members) < 2:
            continue
        audio_hashes = {str(member["audio_sha256"]) for member in members}
        groups = {str(member.get("resolved_group_key", "NOT_AVAILABLE")) for member in members}
        raw_texts = {str(member["transcript"]) for member in members}
        duration = sum(float(member["duration_seconds"]) for member in members)
        long_text = len(normalized.split()) >= 12
        cluster_type = "different_audio_same_short_standard_expression"
        if len(audio_hashes) == 1 and len(raw_texts) == 1:
            cluster_type = "same_audio_same_transcript"
        elif len(audio_hashes) == 1:
            cluster_type = "same_audio_different_transcript"
        elif long_text:
            cluster_type = "different_audio_same_long_transcript"
        scope = "same_group_repeat" if len(groups) == 1 else "different_group_repeat"
        risk = "probable_script_or_template" if len(audio_hashes) > 1 and not long_text else "possible_copy_label_risk" if long_text else "review_required"
        clusters.append({"cluster_id": hashlib.sha256((split + "\0" + normalized).encode()).hexdigest()[:16], "train_or_validation": split, "cluster_size": len(members), "total_duration_seconds": round(duration, 3), "unique_audio_sha_count": len(audio_hashes), "unique_group_count": len(groups), "unique_speaker_count": "NOT_AVAILABLE", "sources": "|".join(sorted({str(member.get("source", "NOT_AVAILABLE")) for member in members})), "exact_transcripts": " || ".join(sorted(raw_texts)[:3]), "normalized_transcript": normalized, "duplicate_signal": cluster_type, "group_scope_signal": scope, "risk_interpretation": risk, "sample_ids": "|".join(str(member["sample_id"]) for member in members)})
    clusters.sort(key=lambda item: (-int(item["cluster_size"]), -float(item["total_duration_seconds"]), str(item["cluster_id"])))
    write_csv(OUTPUT / "duplicate_clusters.csv", clusters)

    selected_clusters = [item for item in clusters if item["train_or_validation"] == "train"][:20]
    selected_clusters += [item for item in clusters if item["train_or_validation"] == "validation"][:10]
    selected_clusters += [item for item in clusters if item["duplicate_signal"] == "different_audio_same_long_transcript"][:20]
    rng = np.random.default_rng(SEED)
    unselected = [item for item in clusters if item not in selected_clusters]
    if unselected:
        selected_clusters += list(rng.choice(unselected, size=min(10, len(unselected)), replace=False))
    seen_clusters: set[str] = set()
    for cluster in selected_clusters:
        cluster_id = str(cluster["cluster_id"])
        if cluster_id in seen_clusters:
            continue
        seen_clusters.add(cluster_id)
        members = [by_id[sample_id] for sample_id in str(cluster["sample_ids"]).split("|")]
        representative = members[0]
        sample_id = str(representative["sample_id"])
        existing = queue.setdefault(sample_id, {**metadata(representative), "transcript": str(representative["transcript"]), "selection_labels": [], "selection_reason": "", "automatic_risk_signals": []})
        existing["selection_labels"].append("duplicate_cluster")
        existing["automatic_risk_signals"].append(str(cluster["duplicate_signal"]))
        existing["selection_reason"] = "|".join(sorted(set(filter(None, [existing["selection_reason"], "largest_or_risk_duplicate_cluster"]))))
        existing["related_sample_ids"] = cluster["sample_ids"]
        existing["cluster_id"] = cluster_id

    existing_shortlist = REPORTS / "data_quality_manual_review_sample.jsonl"
    for item in read_jsonl(existing_shortlist):
        sample_id = str(item["sample_id"])
        if sample_id not in by_id:
            continue
        row = by_id[sample_id]
        existing = queue.setdefault(sample_id, {**metadata(row), "transcript": str(row["transcript"]), "selection_labels": [], "selection_reason": "", "automatic_risk_signals": []})
        existing["selection_labels"].append("automatic_random_control")
        existing["automatic_risk_signals"].extend(str(item.get("automatic_risk_signals", "none")).split("|"))
        existing["selection_reason"] = "|".join(sorted(set(filter(None, [existing["selection_reason"], str(item.get("selection_reason", "automatic_random_control"))]))))

    queue_rows = []
    for item in queue.values():
        item["selection_labels"] = "|".join(sorted(set(item["selection_labels"])))
        item["automatic_risk_signals"] = "|".join(sorted(set(signal for signal in item["automatic_risk_signals"] if signal and signal != "none"))) or "none"
        queue_rows.append(item)
    queue_rows.sort(key=lambda item: ("empty_transcript" not in item["selection_labels"], str(item["sample_id"])))
    with (OUTPUT / "review_queue.jsonl").open("w", encoding="utf-8") as handle:
        for item in queue_rows:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")

    form_rows = [{"sample_id": item["sample_id"], "reviewer": "", "review_timestamp": "", "audible_speech": "", "transcript_correctness": "", "boundary_correctness": "", "channel_correctness": "", "duplicate_legitimacy": "", "severity": "", "recommended_action": "", "note": ""} for item in queue_rows]
    write_csv(OUTPUT / "review_form.csv", form_rows)
    (OUTPUT / "review_instructions.md").write_text("""# Focused manual data-quality review instructions

This package does not change A4 or any frozen A0–A4 artefact. Reviewers must listen to the referenced source audio in a private, authorized environment and fill `review_form.csv`; blank decision fields mean **not reviewed**.

For empty transcripts, choose only evidence-supported values for `audible_speech`, `label_status`, and `proposed_action`. For placeholders, decide whether the token is spoken content or annotation. For duplicate clusters, distinguish valid repeated phrases/scripts from same-audio conflicts, suspicious long copy-label repetition, or source-level investigations. Do not alter source files; every future A5 manifest must cite reviewer decisions and lock provenance/hashes.
""", encoding="utf-8")
    (OUTPUT / "audio_open_commands.ps1").write_text("""param([Parameter(Mandatory=$true)][string]$SampleId)
$queue = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'review_queue.jsonl') | ForEach-Object { $_ | ConvertFrom-Json }
$item = $queue | Where-Object { $_.sample_id -eq $SampleId } | Select-Object -First 1
if ($null -eq $item) { throw "SampleId not present in review_queue.jsonl: $SampleId" }
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$path = Join-Path $root $item.audio_path
if (-not (Test-Path -LiteralPath $path)) { throw "Audio path missing: $path" }
Start-Process -FilePath $path
""", encoding="utf-8")
    remediation = """# A5 possible remediation plan — no manifest materialized

The completed automatic audit identifies seven confirmed empty transcripts; their underlying label/audio status still requires human review. Placeholder and duplicate findings remain review signals, not automatic removals. A0–A4 frozen manifests and validation artefacts remain immutable.

After reviewer decisions only, classify rows as: `confirmed_bad_row_quarantine`, `relabel_required`, `valid_repeated_script`, `template_down_weighting_candidate`, `source_level_investigation_required`, or `no_action`. Any future versioned A5 manifest must lock source-manifest hashes, excluded rows and rationale, reviewer decisions, new manifest hashes, and a fresh train/validation leakage audit.
"""
    (REPORTS / "a5_possible_data_remediation_plan.md").write_text(remediation, encoding="utf-8")
    files = [OUTPUT / name for name in ("empty_transcripts.csv", "placeholder_tokens.csv", "duplicate_clusters.csv", "review_queue.jsonl", "review_form.csv", "review_instructions.md", "audio_open_commands.ps1")]
    (OUTPUT / "artifact_lock.json").write_text(json.dumps({str(path.relative_to(ROOT)): digest(path) for path in files}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (REPORTS / "next_executable_stage.md").write_text("# Next executable stage\n\n`READY_FOR_FOCUSED_MANUAL_DATA_REVIEW`\n\nComplete the review queue and record human decisions. A5 contract materialization and training remain unauthorized.\n", encoding="utf-8")
    print(json.dumps({"status": "READY_FOR_FOCUSED_MANUAL_DATA_REVIEW", "empty_rows": len(empty_rows), "placeholder_rows": len(placeholder_rows), "duplicate_clusters": len(clusters), "review_queue_rows": len(queue_rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
