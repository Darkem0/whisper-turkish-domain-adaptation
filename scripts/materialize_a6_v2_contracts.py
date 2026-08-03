"""Materialize and statically review the authorized A6 contract package.

This script is intentionally CPU-only: it neither imports model libraries nor
loads a checkpoint.  A6 refers to immutable A5/A4 inputs instead of copying
them, so A0-A5 artifacts remain untouched.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
DATA = ROOT / "data" / "materialized" / "training_a6_v2"
REPORTS = ROOT / "reports"
A5_DATA = ROOT / "data" / "materialized" / "training_a5_v2"
A4_VALIDATION = ROOT / "data" / "materialized" / "training_a4_v2" / "a4_validation_manifest.jsonl"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def reference(path: Path, rows: int) -> dict:
    return {
        "reference_type": "immutable_external_reference",
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "sha256": digest(path),
        "rows": rows,
        "copy_created": False,
    }


def field_missing(document: dict, dotted_paths: tuple[str, ...]) -> list[str]:
    missing = []
    for dotted in dotted_paths:
        value: object = document
        for key in dotted.split("."):
            if not isinstance(value, dict) or key not in value:
                missing.append(dotted)
                break
            value = value[key]
    return missing


def main() -> None:
    train = A5_DATA / "a5_train_manifest.jsonl"
    schedule = A5_DATA / "a5_sample_schedule.jsonl"
    replay = A5_DATA / "a5_replay_manifest.jsonl"
    train_rows, validation_rows, schedule_rows = (
        json_rows(train),
        json_rows(A4_VALIDATION),
        json_rows(schedule),
    )
    train_ids = {row["sample_id"] for row in train_rows}
    schedule_ids = [row["sample_id"] for row in schedule_rows]
    audio_overlap = {row["audio_sha256"] for row in train_rows} & {
        row["audio_sha256"] for row in validation_rows
    }
    group_overlap = {row["resolved_group_key"] for row in train_rows} & {
        row["resolved_group_key"] for row in validation_rows
    }
    empty_schedule = [
        row["sample_id"]
        for row in schedule_rows
        if not next((x for x in train_rows if x["sample_id"] == row["sample_id"]), {})
        .get("transcript", "")
        .strip()
    ]
    schedule_missing = sorted(set(schedule_ids) - train_ids)
    refs = {
        "train": reference(train, len(train_rows)),
        "validation": reference(A4_VALIDATION, len(validation_rows)),
        "replay": reference(replay, 0),
        "schedule": reference(schedule, len(schedule_rows)),
    }
    for name, item in refs.items():
        write_json(
            DATA / f"a6_{name}_manifest.reference.json"
            if name != "schedule"
            else DATA / "a6_sample_schedule.reference.json",
            item,
        )
    training = {
        "contract_id": "A6_v2_encoder_decoder_zero_replay_training_contract",
        "schema_version": 1,
        "status": "READY_FOR_A6_V2_RESOURCE_SMOKE",
        "blocker": None,
        "identity": {
            "experiment": "A6_v2_encoder_decoder_zero_replay",
            "base_model": "openai/whisper-large-v3-turbo",
            "base_model_revision": "41f01f3fe87f28c78e2fbf8b568835947dd65ed9",
            "tokenizer_processor_revision": "41f01f3fe87f28c78e2fbf8b568835947dd65ed9",
        },
        "initialization": {
            "mode": "fresh_base",
            "parent_adapter": None,
            "parent_weights_loaded": False,
            "adapter_loading": "FORBIDDEN_A2_A3_A4_A5",
            "legacy_resume": "FORBIDDEN: A3_legacy_aborted_step34_invalid",
        },
        "lora": {
            "scope": "encoder+decoder",
            "encoder_target_modules": ["q_proj", "v_proj"],
            "decoder_target_modules": ["q_proj", "v_proj"],
            "rank": 16,
            "alpha": 32,
            "dropout": 0.05,
            "trainable_parameter_count": "RUNTIME_MEASUREMENT_REQUIRED; approximate_sum_A3_A4=3276800 is not a contract assertion",
        },
        "optimization": {
            "dtype": "fp16",
            "gradient_checkpointing": True,
            "per_device_batch_size": 1,
            "gradient_accumulation_steps": 16,
            "effective_batch_size": 16,
            "optimizer": "AdamW",
            "learning_rate": 0.00001,
            "betas": [0.9, 0.999],
            "weight_decay": 0.01,
            "scheduler": "linear",
            "warmup_steps": 20,
            "max_steps": 200,
            "seed": 20260730,
        },
        "cadence": {
            "checkpoint_steps": [50, 100, 150, 200],
            "local_validation_steps": [50, 100, 150, 200],
        },
        "data": {
            "train_manifest": refs["train"]["path"],
            "validation_manifest": refs["validation"]["path"],
            "replay_manifest": refs["replay"]["path"],
            "schedule": refs["schedule"]["path"],
            "replay_ratio": 0.0,
            "replay_rows": 0,
            "schedule_policy": "exact immutable A5 cleaned schedule; no regeneration",
        },
        "resume": {
            "policy": "only a verified A6 checkpoint from this exact contract may resume",
            "legacy_resume_forbidden": True,
        },
        "promotion": {"diagnostic_only": True, "production_promotion_allowed": False},
        "resources": {
            "vram_limit_mib": 12282,
            "smoke_steps": 2,
            "smoke_microbatches": 32,
            "reserved_vram_gate_mib": 10000,
        },
    }
    a5_eval = json.loads((CONTRACTS / "A5_v2_eval_contract.yaml").read_text(encoding="utf-8"))
    evaluation = dict(a5_eval)
    evaluation.update(
        {
            "contract_id": "A6_v2_encoder_decoder_zero_replay_eval_contract",
            "schema_version": 1,
            "status": "READY_FOR_A6_V2_RESOURCE_SMOKE",
            "diagnostic_only": True,
            "production_promotion_allowed": False,
            "comparison_policy": {
                "primary": "A6 vs A5: same cleaned train manifest, exact schedule, zero replay, seed, optimizer and cadence; only encoder+decoder versus encoder-only scope differs.",
                "secondary": "A6 vs A4: supporting only; A4 schedule has 52 historic empty-target exposures.",
                "a2": "supporting only; data/schedule/replay conditions may differ.",
                "a0": "absolute target-domain and general-domain reference.",
            },
            "interpretation_classes": [
                "combination_synergy_supported",
                "decoder_dominant_no_combination_gain",
                "combination_gain_with_general_domain_cost",
                "combination_inconclusive",
                "technical_failure",
            ],
            "monitoring_policy": {
                "target_domain": [
                    "mediaspeech_clean",
                    "mediaspeech_phone",
                    "mediaspeech_g711",
                    "robustness_proxy",
                ],
                "general_domain": ["cv_scripted", "fleurs", "cv_spontaneous", "tsc_exploratory"],
                "cv_scripted_and_fleurs": "scientific_monitoring_not_automatic_production_rejection",
                "cv_spontaneous": "report_only",
                "tsc_exploratory": True,
            },
        }
    )
    lock = {
        "contract_id": "A6_v2_encoder_decoder_zero_replay_data_manifest_lock",
        "schema_version": 1,
        "status": "READY_FOR_A6_V2_RESOURCE_SMOKE",
        "authoritative_lineage": "A5_cleaned_population_and_exact_schedule",
        "materialized": refs,
        "expected": {
            "train_rows": 172231,
            "validation_rows": 9081,
            "schedule_rows": 3200,
            "acoustic_microbatches": 3200,
            "replay_microbatches": 0,
            "empty_transcript_schedule_exposure": 0,
        },
        "leakage_audit": {"audio_overlap": len(audio_overlap), "group_overlap": len(group_overlap)},
    }
    write_json(CONTRACTS / "A6_v2_training_contract.yaml", training)
    write_json(CONTRACTS / "A6_v2_eval_contract.yaml", evaluation)
    write_json(CONTRACTS / "A6_v2_data_manifest.lock.json", lock)
    required_training = (
        "identity.base_model",
        "identity.base_model_revision",
        "identity.tokenizer_processor_revision",
        "initialization.mode",
        "initialization.parent_adapter",
        "initialization.parent_weights_loaded",
        "initialization.legacy_resume",
        "lora.encoder_target_modules",
        "lora.decoder_target_modules",
        "optimization.optimizer",
        "optimization.scheduler",
        "cadence.checkpoint_steps",
        "data.train_manifest",
        "data.validation_manifest",
        "data.schedule",
        "resume.policy",
        "promotion.diagnostic_only",
        "promotion.production_promotion_allowed",
    )
    required_eval = (
        "evaluation_lock.path",
        "evaluation_lock.sha256",
        "acceptance_lock.path",
        "acceptance_lock.sha256",
        "immutable_registry.path",
        "immutable_registry.sha256",
        "frozen_evaluation_plan.checkpoints",
        "frozen_evaluation_plan.targets",
        "comparison_policy.primary",
        "monitoring_policy.target_domain",
    )
    blockers = field_missing(training, required_training) + field_missing(evaluation, required_eval)
    checks = {
        "train_rows": len(train_rows) == 172231,
        "validation_rows": len(validation_rows) == 9081,
        "schedule_rows": len(schedule_rows) == 3200,
        "acoustic_rows": all(row.get("role") == "acoustic" for row in schedule_rows),
        "schedule_membership": not schedule_missing,
        "empty_schedule_exposure": not empty_schedule,
        "audio_overlap": not audio_overlap,
        "group_overlap": not group_overlap,
        "replay_empty": replay.stat().st_size == 0,
        "target_plan": evaluation["frozen_evaluation_plan"]
        == {"checkpoints": [50, 100, 150, 200], "targets": 28},
        "production_prohibited": training["promotion"]["production_promotion_allowed"] is False
        and evaluation["production_promotion_allowed"] is False,
    }
    blockers.extend(name for name, passed in checks.items() if not passed)
    status = (
        "READY_FOR_A6_V2_RESOURCE_SMOKE"
        if not blockers
        else "BLOCKED_A6_V2_CONTRACT_MATERIALIZATION"
    )
    for document in (training, evaluation, lock):
        document["status"] = status
    write_json(CONTRACTS / "A6_v2_training_contract.yaml", training)
    write_json(CONTRACTS / "A6_v2_eval_contract.yaml", evaluation)
    write_json(CONTRACTS / "A6_v2_data_manifest.lock.json", lock)
    hashes = {
        name: digest(path)
        for name, path in {
            "training_contract": CONTRACTS / "A6_v2_training_contract.yaml",
            "eval_contract": CONTRACTS / "A6_v2_eval_contract.yaml",
            "data_lock": CONTRACTS / "A6_v2_data_manifest.lock.json",
            "train": train,
            "validation": A4_VALIDATION,
            "schedule": schedule,
        }.items()
    }
    (REPORTS / "a6_v2_hypothesis.md").write_text(
        "# A6_v2 hypothesis\n\nA6 tests whether jointly adapting encoder and decoder Q/V LoRA on the exact A5 cleaned zero-replay data/schedule yields complementary target-domain gain over either single-side scope, or instead neutralization/general-domain cost. It is diagnostic-only and cannot promote a production model.\n",
        encoding="utf-8",
    )
    (REPORTS / "a6_v2_matched_ablation_design.md").write_text(
        "# A6 matched-ablation design\n\nA6 versus A5 is primary and matched on cleaned manifest, exact schedule, zero replay, seed, optimizer and cadence; scope is the sole intervention. A6 versus A4 is supportive only because A4 had 52 empty-target schedule exposures. A6 versus A2 is supportive only because its data/schedule/replay conditions differ.\n",
        encoding="utf-8",
    )
    (REPORTS / "a6_v2_data_and_schedule_audit.md").write_text(
        "# A6 data and schedule audit\n\n```json\n"
        + json.dumps({"checks": checks, "hashes": hashes, "blockers": blockers}, indent=2)
        + "\n```\n",
        encoding="utf-8",
    )
    (REPORTS / "a6_v2_contract_review.md").write_text(
        "# A6 contract review\n\n```json\n"
        + json.dumps(
            {"status": status, "required_path_blockers": blockers, "hashes": hashes}, indent=2
        )
        + "\n```\n",
        encoding="utf-8",
    )
    (REPORTS / "a6_v2_execution_plan.md").write_text(
        "# A6 execution plan\n\nNext authorized action: a 2-optimizer-step resource smoke only after this contract review. Smoke must measure trainable parameters at runtime; no count is asserted here. It must not begin full training, local validation, or frozen evaluation.\n",
        encoding="utf-8",
    )
    (REPORTS / "next_executable_stage.md").write_text(
        f"# Next executable stage\n\n`{status}`\n\nA6 training, smoke, and evaluation were not started by contract materialization.\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": status, "blockers": blockers, "hashes": hashes}, indent=2))


if __name__ == "__main__":
    main()
