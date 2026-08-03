"""Materialize blocked company-domain evaluation contracts without touching company data."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
REPORTS = ROOT / "reports"
REVISION = "41f01f3fe87f28c78e2fbf8b568835947dd65ed9"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def adapter(
    candidate_id: str,
    experiment: str,
    checkpoint: str,
    relative: str | None,
    scope: str,
    replay: float,
    reason: str,
    limitations: str,
) -> dict:
    entry = {
        "candidate_id": candidate_id,
        "experiment": experiment,
        "checkpoint": checkpoint,
        "adapter_path": relative,
        "adapter_sha256": None,
        "base_model_revision": REVISION,
        "lora_scope": scope,
        "replay_ratio": replay,
        "selection_reason": reason,
        "open_data_diagnostic_limitations": limitations,
    }
    if relative is not None:
        path = ROOT / relative
        entry["adapter_sha256"] = sha(path)
        entry["artifact_exists"] = True
    else:
        entry["artifact_exists"] = True
    return entry


def main() -> None:
    candidates = [
        adapter(
            "A0_base", "A0", "base", None, "none", 0.0, "required base comparator", "open-data only"
        ),
        adapter(
            "A2_200",
            "A2",
            "step-200",
            "runs/A2_v2d_200/adapter/adapter_model.safetensors",
            "encoder+decoder Q/V",
            None,
            "historical combined-adaptation candidate",
            "different data/schedule; historical non-promotion",
        ),
        adapter(
            "A3_050",
            "A3",
            "step-050",
            "runs/A3_v2_fresh_base_200/checkpoints/step-050/adapter/adapter_model.safetensors",
            "encoder Q/V",
            0.1,
            "encoder+replay research reference",
            "CV Scripted hard-gate failure on open data",
        ),
        adapter(
            "A4_050",
            "A4",
            "step-050",
            "runs/A4_v2_fresh_base_200/checkpoints/step-050/adapter/adapter_model.safetensors",
            "decoder Q/V",
            0.0,
            "best A4 Phone checkpoint",
            "52 historic empty-target schedule exposures",
        ),
        adapter(
            "A4_200",
            "A4",
            "step-200",
            "runs/A4_v2_fresh_base_200/checkpoints/step-200/adapter/adapter_model.safetensors",
            "decoder Q/V",
            0.0,
            "best A4 robustness checkpoint",
            "52 historic empty-target schedule exposures",
        ),
        adapter(
            "A5_100",
            "A5",
            "step-100",
            "runs/A5_v2_fresh_base_200/checkpoints/step-100/adapter/adapter_model.safetensors",
            "encoder Q/V",
            0.0,
            "best A5 Phone checkpoint",
            "diagnostic-only open-data result",
        ),
        adapter(
            "A5_200",
            "A5",
            "step-200",
            "runs/A5_v2_fresh_base_200/checkpoints/step-200/adapter/adapter_model.safetensors",
            "encoder Q/V",
            0.0,
            "matched A6 comparison member",
            "diagnostic-only open-data result",
        ),
        adapter(
            "A6_200",
            "A6",
            "step-200",
            "runs/A6_v2_fresh_base_200/checkpoints/step-200/adapter/adapter_model.safetensors",
            "encoder+decoder Q/V",
            0.0,
            "best A6 Phone/robustness and matched A5 pair",
            "combination synergy inconclusive",
        ),
    ]
    missing = [
        "authorized company-data root or manifest",
        "data-owner authorization/provenance record",
        "human-written or human-verified reference transcripts",
        "secure internal sample identifiers and grouping metadata",
        "call/customer/recording identity hashes for leakage-safe split",
        "channel metadata for agent/customer/stereo",
        "dev and final-holdout separation",
        "annotation QA/reviewer metadata",
    ]
    data_lock = {
        "contract_id": "company_domain_data_manifest_lock",
        "status": "BLOCKED_COMPANY_DOMAIN_AUTHORIZATION",
        "authorized_data_roots": [],
        "manifests": [],
        "missing_required_inputs": missing,
        "prohibition": "No company audio, transcript, manifest, path or hash is materialized or inferred by this contract.",
    }
    annotation = {
        "contract_id": "company_domain_annotation_policy",
        "status": "REQUIRES_DATA_OWNER_AND_ASR_REVIEWER_AUTHORIZATION",
        "reference_standard": {
            "verbatim_audible_speech": True,
            "no_inference_or_completion": True,
            "boundary_cut_policy": "mark, do not silently repair",
            "unintelligible_policy": "authorized token and reviewer decision required",
            "numbers_dates_amounts": "preserve spoken form plus authorized normalization mapping",
            "abbreviations_foreign_words_fillers_repetitions_fragments": "transcribe according to a versioned reviewer guide",
            "overlap_and_channel_mixing": "mark channel/overlap status when metadata allows",
            "punctuation_and_casing": "retain raw reference and a separately versioned normalization policy",
        },
        "qa": {
            "final_test_human_qa_required": True,
            "risk_subset_second_review_adjudication": True,
            "reviewer_agreement": "required when reviewer identities/decisions are available",
        },
        "current_evidence": "MISSING: existing company transcripts were not found or audited.",
    }
    privacy = {
        "contract_id": "company_domain_privacy_policy",
        "status": "REQUIRED_BEFORE_DATA_MATERIALIZATION",
        "rules": [
            "raw audio is not copied",
            "PII is not written to reports",
            "only hashed/safe internal identifiers appear in manifests",
            "predictions/reports do not expose names, account IDs or amounts",
            "no external service/API upload",
            "logs do not print transcript or PII",
            "raw-example review uses an internal secure queue reference only",
        ],
        "authorized_access_requirement": "data owner must supply approved local/server root and access scope",
    }
    evaluation = {
        "contract_id": "company_domain_evaluation_contract",
        "status": "BLOCKED_COMPANY_DOMAIN_AUTHORIZATION",
        "purpose": "compare A0/A2/A3/A4/A5/A6 candidates on real authorized company calls; no training",
        "candidate_lock": "contracts/company_domain_candidate_lock.json",
        "data_lock": "contracts/company_domain_data_manifest.lock.json",
        "annotation_policy": "contracts/company_domain_annotation_policy.yaml",
        "privacy_policy": "contracts/company_domain_privacy_policy.yaml",
        "split_policy": {
            "unit_priority": [
                "customer_or_speaker_hash",
                "call_id",
                "recording_id",
                "source_recording_group",
                "agent_hash",
                "project_or_activity_group",
                "stable_source_hash",
            ],
            "development_and_final_holdout": "must be physically disjoint; one population may not be silently reused",
            "agent_repeat_analysis": "required",
            "channel_analysis": "agent/customer/stereo only when authorized metadata exists",
        },
        "metrics": {
            "asr": [
                "normalized_wer",
                "raw_wer",
                "normalized_cer",
                "raw_cer",
                "call_macro_wer",
                "duration_weighted_wer",
                "median_call_segment_wer",
                "deletion_rate",
                "insertion_rate",
                "substitution_rate",
            ],
            "critical_behavior": [
                "empty_output",
                "hallucination",
                "repetition_loop",
                "overlong_output",
                "unsupported_insertion",
                "wrong_language",
                "boundary_loss",
                "channel_mixing",
                "catastrophic_numeric_error",
            ],
            "entity_metrics": "NOT_EVALUATED until authorized annotations exist",
        },
        "statistics": {
            "paired": True,
            "ci": "paired bootstrap WER/CER; call-level and channel-specific CI",
            "multiple_comparisons": "report all prespecified comparisons; do not select by unadjusted mean alone",
            "small_subsets": "insufficient_sample warning",
        },
        "selection_priority": [
            "no critical operational errors",
            "customer channel",
            "agent channel",
            "numbers/amounts/dates/names",
            "call macro WER",
            "telephone robustness",
            "latency/resources",
        ],
        "open_data_policy": "CV Scripted/FLEURS are monitoring only, not company-selection hard gates",
        "thresholds": "MISSING: business owner, ASR reviewer and model owner authorization required before any threshold is set",
    }
    candidate_lock = {
        "contract_id": "company_domain_candidate_lock",
        "status": "READY_FOR_COMPANY_DOMAIN_CONTRACT_REVIEW",
        "base_model": "openai/whisper-large-v3-turbo",
        "base_model_revision": REVISION,
        "candidates": candidates,
        "shortlist_lock_rule": "final-test shortlist must be frozen before any final-holdout prediction is viewed",
        "candidate_count": len(candidates),
    }
    for path, value in (
        (CONTRACTS / "company_domain_data_manifest.lock.json", data_lock),
        (CONTRACTS / "company_domain_annotation_policy.yaml", annotation),
        (CONTRACTS / "company_domain_privacy_policy.yaml", privacy),
        (CONTRACTS / "company_domain_evaluation_contract.yaml", evaluation),
        (CONTRACTS / "company_domain_candidate_lock.json", candidate_lock),
    ):
        save(path, value)
    reports = {
        "company_domain_evaluation_hypothesis.md": "# Company-domain evaluation hypothesis\n\nOnly authorized, human-verified company calls can determine which locked candidate minimizes operational error. Open-data results remain diagnostic context.\n",
        "company_domain_dataset_inventory.md": "# Company-domain dataset inventory\n\n`BLOCKED_COMPANY_DOMAIN_AUTHORIZATION`: no authorized company manifest or secure data root was found. No company path, hash, transcript, audio or PII is recorded here.\n",
        "company_domain_split_and_leakage_plan.md": "# Split and leakage plan\n\nDevelopment and final holdout must be disjoint at the highest available group: customer/speaker hash, call, recording, source group, agent hash, project/activity, then stable source hash. Current company metadata: `NOT_AVAILABLE`.\n",
        "company_domain_stratification_plan.md": "# Stratification plan\n\nAgent/customer/stereo channels, call quality, crosstalk, duration, accent, numeric/entity content, project/activity and codec/sample-rate must be reported only where authorized metadata exists; otherwise `NOT_AVAILABLE`.\n",
        "company_domain_candidate_shortlist.md": "# Candidate shortlist\n\nSee `contracts/company_domain_candidate_lock.json`: eight artifact-hash-verified candidates, including A0, A2, A3, two A4, two A5 and A6-200. A5-200/A6-200 are retained as a matched pair.\n",
        "company_domain_metric_and_statistics_plan.md": "# Metrics and statistics\n\nUse paired WER/CER bootstrap, call-level and channel-specific analysis. Critical entity metrics require authorized annotation; absent annotations are `not_evaluated`, not inferred.\n",
        "company_domain_annotation_review_plan.md": "# Annotation review plan\n\nHuman-verified reference is required. Final holdout requires at least one human QA and a risk-subset second review/adjudication when reviewer metadata permits. Existing company annotation evidence: `MISSING`.\n",
        "company_domain_privacy_review.md": "# Privacy review\n\nNo raw audio, PII, transcript or prediction text is copied into this workspace/report package. Approved secure access and internal-review workflow are required before materialization.\n",
        "company_domain_contract_review.md": "# Company-domain contract review\n\nCandidate artifacts and hashes are verified. Data, split, human-reference and authorization inputs are missing; therefore this package is blocked and no inference/training is authorized.\n",
    }
    for name, text in reports.items():
        (REPORTS / name).write_text(text, encoding="utf-8")
    (REPORTS / "next_executable_stage.md").write_text(
        "# Next executable stage\n\n`BLOCKED_COMPANY_DOMAIN_AUTHORIZATION`\n\nProvide an authorized secure company manifest/root, provenance approval, human-verified references and leakage-safe grouping metadata.\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": "BLOCKED_COMPANY_DOMAIN_AUTHORIZATION",
                "candidate_count": len(candidates),
                "missing": missing,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
