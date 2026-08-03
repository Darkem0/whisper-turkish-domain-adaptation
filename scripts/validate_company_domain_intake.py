"""Read-only, aggregate-only validator for later authorized company-data intake."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


REQUIRED_AUTH = ("data_owner", "authorizing_person_or_role", "authorization_date", "permitted_purpose", "evaluation_allowed", "authorized_users", "authorized_compute_hosts", "authorized_secure_root", "permitted_output_root", "retention_policy", "deletion_policy", "PII_handling_policy", "approval_reference")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
MANIFEST_FIELDS = (
    "sample_id",
    "audio_path",
    "audio_sha256",
    "duration_seconds",
    "split_group_id",
    "channel_role",
    "transcript_path",
    "transcript_sha256",
    "human_qa_status",
    "annotation_policy_version",
    "source_project",
)
PROVENANCE_FIELDS = (
    "sample_id",
    "reference_type",
    "created_by_human",
    "human_corrected",
    "reviewer_id_hash",
    "review_timestamp",
    "qa_status",
    "annotation_policy_version",
    "adjudication_status",
    "unresolved_issue_count",
)


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def under(root: Path, raw: str) -> Path | None:
    try:
        candidate = Path(raw).resolve(strict=False)
        base = root.resolve(strict=True)
        candidate.relative_to(base)
        return candidate
    except (OSError, ValueError):
        return None


def manifest_schema_error(row: dict) -> bool:
    if any(row.get(field) in (None, "") for field in MANIFEST_FIELDS):
        return True
    if not (row.get("call_id") or row.get("recording_id")):
        return True
    if not isinstance(row.get("source_project"), dict):
        return True
    if not isinstance(row.get("duration_seconds"), (int, float)) or row["duration_seconds"] <= 0:
        return True
    if not SHA256.fullmatch(str(row.get("audio_sha256", ""))) or not SHA256.fullmatch(str(row.get("transcript_sha256", ""))):
        return True
    return row.get("channel_role") not in {"agent", "customer", "mixed", "unknown"} or row.get("human_qa_status") not in {"human_verified", "human_corrected"}


def provenance_schema_error(row: dict) -> bool:
    if any(field not in row for field in PROVENANCE_FIELDS):
        return True
    if not isinstance(row.get("created_by_human"), bool) or not isinstance(row.get("human_corrected"), bool):
        return True
    if not isinstance(row.get("unresolved_issue_count"), int) or row["unresolved_issue_count"] < 0:
        return True
    return row.get("reference_type") not in {"human_created", "human_corrected", "model_only", "unknown"} or row.get("qa_status") not in {"approved", "rejected", "pending"}


def split_schema_error(row: dict) -> bool:
    return any(row.get(field) in (None, "") for field in ("sample_id", "split_group_id", "split")) or row.get("split") not in {"development", "final_holdout"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--splits", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    authorization = json.loads(args.authorization.read_text(encoding="utf-8"))
    failures = ["authorization:" + field for field in REQUIRED_AUTH if authorization.get(field) in (None, "", "REQUIRED")]
    if authorization.get("evaluation_allowed") is not True:
        failures.append("authorization:evaluation_allowed")
    if authorization.get("external_upload_forbidden") is not True:
        failures.append("authorization:external_upload_forbidden")
    root = Path(authorization["authorized_secure_root"]) if not failures else None
    manifest, provenance, splits = rows(args.manifest), rows(args.provenance), rows(args.splits)
    sample_ids = [str(row.get("sample_id", "")) for row in manifest]
    if len(sample_ids) != len(set(sample_ids)):
        failures.append("manifest:duplicate_sample_id")
    audio_hashes = [str(row.get("audio_sha256", "")) for row in manifest]
    if len(audio_hashes) != len(set(audio_hashes)):
        failures.append("manifest:duplicate_audio_sha256")
    by_sample = {str(row.get("sample_id")): row for row in manifest}
    for row in manifest:
        if manifest_schema_error(row):
            failures.append("manifest:schema_validation_failed")
        if root:
            audio, transcript = under(root, str(row.get("audio_path", ""))), under(root, str(row.get("transcript_path", "")))
            if audio is None or transcript is None:
                failures.append("manifest:unauthorized_or_traversal_path")
                continue
            if not audio.is_file() or not transcript.is_file():
                failures.append("manifest:missing_audio_or_transcript")
            elif digest(audio) != row.get("audio_sha256") or digest(transcript) != row.get("transcript_sha256"):
                failures.append("manifest:hash_mismatch")
        if row.get("human_qa_status") not in {"human_verified", "human_corrected"}:
            failures.append("manifest:human_qa_required")
    provenance_by_sample = {str(row.get("sample_id")): row for row in provenance}
    if any(provenance_schema_error(row) for row in provenance):
        failures.append("provenance:schema_validation_failed")
    for sample_id in by_sample:
        item = provenance_by_sample.get(sample_id)
        if not item or item.get("qa_status") != "approved" or not (item.get("created_by_human") or item.get("human_corrected")) or item.get("reference_type") in {"model_only", "unknown"}:
            failures.append("provenance:human_verified_reference_required")
            break
    split_by_group: dict[str, set[str]] = {}
    for item in splits:
        if split_schema_error(item) or item.get("sample_id") not in by_sample:
            failures.append("split:schema_validation_failed")
            continue
        split_by_group.setdefault(str(item.get("split_group_id")), set()).add(str(item.get("split")))
    if any(len(values) > 1 for values in split_by_group.values()):
        failures.append("split:group_overlap_hard_failure")
    if {item.get("split") for item in splits} != {"development", "final_holdout"}:
        failures.append("split:separate_development_and_final_holdout_required")
    result = {"status": "PASSED" if not failures else "BLOCKED", "rows": {"manifest": len(manifest), "provenance": len(provenance), "splits": len(splits)}, "failure_categories": sorted(set(failures)), "privacy": "aggregate_only; no sample IDs, paths, transcripts, PII or raw values emitted"}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "failure_category_count": len(result["failure_categories"])}))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
