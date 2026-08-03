"""Apply approved A3_v2 decisions to existing contracts; never starts a run."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
REPORTS = ROOT / "reports"
META = json.loads((ROOT / "data/materialized/training_a3_v2/a3_manifest_materialization.json").read_text(encoding="utf-8"))


def dump(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    training_path = CONTRACTS / "A3_v2_training_contract.yaml"
    training = json.loads(training_path.read_text(encoding="utf-8"))
    training["status"] = "READY_FOR_A3_V2_RESOURCE_SMOKE"
    training["data"].update({
        "train_manifest": META["manifests"]["a3_train_manifest"]["path"],
        "train_manifest_sha256": META["manifests"]["a3_train_manifest"]["sha256"],
        "validation_manifest": META["manifests"]["a3_validation_manifest"]["path"],
        "validation_manifest_sha256": META["manifests"]["a3_validation_manifest"]["sha256"],
        "a2_clean_replay_ratio": 0.0,
        "a3_clean_replay_ratio": 0.10,
        "replay_manifest": META["manifests"]["a3_replay_manifest"]["path"],
        "replay_manifest_sha256": META["manifests"]["a3_replay_manifest"]["sha256"],
        "sampler_schedule": META["schedule"]["path"],
        "sampler_schedule_sha256": META["schedule"]["sha256"],
        "sampler_microbatches": 3200,
        "sampler_role_counts": META["schedule"]["role_counts"],
        "mixture": {"acoustic_adaptation": 0.90, "clean_replay": 0.10, "enforcement": "precomputed deterministic microbatch schedule"},
    })
    training["initialization"] = {
        "initialization_mode": "fresh_base",
        "base_model_revision": training["identity"]["base_model_revision"],
        "parent_adapter": None,
        "parent_reference": "A2_v2d_200",
        "parent_weights_loaded": False,
        "a2_role": "baseline, technical reference, and comparison result only",
        "failed_a2_promotion_policy": "A2 promotion failure is not parent promotion and does not relax A3 gates.",
        "code_compatibility": "VERIFIED: src/whisper_arge/lora_train.py:run_lora_steps calls WhisperForConditionalGeneration.from_pretrained(MODEL, revision=REVISION) and has no A2 adapter load path.",
        "legacy_resume": "FORBIDDEN: A3_legacy_aborted_step34_invalid"
    }
    training["optimization"].update({"seed": 42, "per_device_train_batch_size": 1, "gradient_accumulation_steps": 16, "effective_batch_size": 16})
    training["cadence"] = {
        "save_steps": 50,
        "eval_steps": 50,
        "logging_steps": 5,
        "checkpoint_steps": [50, 100, 150, 200],
        "final_adapter": "step_200 adapter must be separately SHA-256 locked",
        "automatic_best_checkpoint_promotion": False,
        "checkpoint_evaluation": "Evaluate each checkpoint against the frozen A3_v2 eval contract.",
        "resume_policy": "Only a verified A3_v2 checkpoint from this contract may resume; legacy A3 step 34 is forbidden."
    }
    training["resources"] = {
        "vram_limit_mib": 12282,
        "preflight_smoke": {
            "status": "DEFINED_NOT_RUN",
            "steps": 2,
            "acceptance_gates": ["no CUDA OOM", "finite loss", "forward/backward/optimizer complete", "peak CUDA reserved < 10000 MiB", "process stable", "adapter checkpoint written", "only encoder Q/V LoRA parameters trainable", "actual trainable parameters verified against approximately 2621440"]
        },
        "expected_peak_vram_mib": "MISSING until the A3_v2-only smoke is run",
        "expected_runtime_seconds": "MISSING until smoke: median_step_time * 200; report an additional 25 percent safety margin",
        "smoke_metrics_required": ["median_step_time_seconds", "peak_allocated_mib", "peak_reserved_mib", "driver_vram_mib"]
    }
    training["activation_gates"] = [
        "All input and contract SHA-256 values match.",
        "Run the defined A3_v2-only two-step resource smoke after explicit authorization.",
        "Pass every resource smoke acceptance gate.",
        "Obtain separate authorization before the 200-step training run."
    ]
    dump(training_path, training)

    data_path = CONTRACTS / "A3_v2_data_manifest.lock.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    data["status"] = "MATERIALIZED_READY_FOR_RESOURCE_SMOKE"
    data["a3_manifests"] = META["manifests"]
    data["deterministic_sampler"] = META["schedule"]
    data["selection"] = {k: META[k] for k in ("seed", "validation_ratio_target", "clean_replay_ratio", "source_rows", "validation_rows_by_source", "replay_rows_by_source", "acoustic_rows_by_source", "excluded_due_to_frozen_evaluation", "excluded_invalid_rows", "leakage_policy")}
    data["unresolved_required_inputs"] = []
    data["invariant"] = "A3 train, replay, and validation manifests are mutually disjoint by sample_id; validation is disjoint from train/replay by audio SHA-256. Frozen external evaluation remains read-only."
    dump(data_path, data)

    eval_path = CONTRACTS / "A3_v2_eval_contract.yaml"
    evaluation = json.loads(eval_path.read_text(encoding="utf-8"))
    evaluation["status"] = "FROZEN_READY_FOR_RESOURCE_SMOKE"
    evaluation["immutable_registry"]["sha256"] = sha(ROOT / "protocols/immutable_test_registry.json")
    evaluation["checkpoint_policy"] = {"evaluate_steps": [50, 100, 150, 200], "automatic_best_checkpoint_promotion": False, "normalization": "Use the existing frozen evaluation code and normalization lock."}
    evaluation["a2_gate_policy"] = "A2 promotion failure does not permit a relaxed A3 promotion gate."
    dump(eval_path, evaluation)

    hashes = {str(path.relative_to(ROOT)).replace("\\", "/"): sha(path) for path in (training_path, data_path, eval_path)}
    data = json.loads(data_path.read_text(encoding="utf-8"))
    # A file cannot truthfully contain its own final hash; lock the peer contracts
    # here and report the final data-lock hash externally.
    data["peer_contract_sha256"] = {
        str(training_path.relative_to(ROOT)).replace("\\", "/"): hashes[str(training_path.relative_to(ROOT)).replace("\\", "/")],
        str(eval_path.relative_to(ROOT)).replace("\\", "/"): hashes[str(eval_path.relative_to(ROOT)).replace("\\", "/")],
    }
    dump(data_path, data)
    hashes[str(data_path.relative_to(ROOT)).replace("\\", "/")] = sha(data_path)

    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "a3_v2_initialization_decision.md").write_text(
        "# A3_v2 initialization decision\n\n"
        "A3_v2 uses `initialization_mode=fresh_base` from the pinned base model revision. `parent_adapter=null`, `parent_reference=A2_v2d_200`, and `parent_weights_loaded=false`. A2 is retained only as baseline/technical/comparison evidence; its failed promotion is neither a silent parent promotion nor a reason to relax any A3 gate. `src/whisper_arge/lora_train.py` is compatible because it loads the pinned base model and has no parent-adapter loading path. `A3_legacy_aborted_step34_invalid` is forbidden.\n",
        encoding="utf-8",
    )
    (REPORTS / "a3_v2_manifest_materialization.md").write_text(
        "# A3_v2 manifest materialization\n\n"
        f"Status: **MATERIALIZED_NOT_TRAINED**. Train/validation/replay rows are {META['manifests']['a3_train_manifest']['rows']}/{META['manifests']['a3_validation_manifest']['rows']}/{META['manifests']['a3_replay_manifest']['rows']}. SHA-256 values are locked in `contracts/A3_v2_data_manifest.lock.json`. The 200-step sampler has exactly 2,880 acoustic and 320 clean-replay microbatches (90/10).\n\n"
        f"Seven source rows were excluded for missing required fields: {', '.join(x['sample_id'] for x in META['excluded_invalid_rows'])}. No frozen-evaluation overlap was found. CV spontaneous uses speaker-disjoint grouping; its small pool resulted in 17 validation rows, which is above the approximate 5% target to preserve group isolation.\n",
        encoding="utf-8",
    )
    (REPORTS / "a3_v2_contract_audit.md").write_text(
        "# A3_v2 preflight contract audit\n\n"
        "Status: **READY_FOR_A3_V2_RESOURCE_SMOKE**. No training, smoke, decoding, or inference was run. The A3_v2 train, validation, replay, sampler, initialization, checkpoint/eval cadence, pinned environment, and frozen evaluation gates are now materialized and hash-locked. The next action is only the separately authorized two-step A3_v2 resource smoke.\n\n"
        "A3 starts fresh from the pinned base model; A2 weights are not loaded. A2 remains a failed-promotion comparison reference and does not weaken gates.\n",
        encoding="utf-8",
    )
    (REPORTS / "a3_v2_missing_inputs.md").write_text(
        "# A3_v2 missing inputs\n\n"
        "No contract or manifest input remains missing for the defined resource smoke. Runtime, A3-specific peak VRAM, and actual trainable-parameter count remain **MISSING until the smoke executes** and must not be inferred.\n\n"
        "Excluded source records (not used): `cvsp-68089`, `cvsp-72082`, `cvsp-78549`, `cvsp-78550`, `cvsp-79391`, `cvsp-84256`, `cvsp-91623`; each has a missing `reference` field in `data/materialized/cv_spontaneous_v2c/cv_spontaneous_train_v2c.jsonl`.\n",
        encoding="utf-8",
    )
    (REPORTS / "a3_v2_vram_feasibility.md").write_text(
        "# A3_v2 VRAM feasibility\n\n"
        "RTX 4070 SUPER capacity is 12,282 MiB. A3’s two-step smoke is defined but not run. Acceptance requires no OOM, finite loss, completed optimization, stable process, adapter write, encoder Q/V-only trainability, approximately 2,621,440 actual trainable parameters, and peak CUDA reserved below 10,000 MiB.\n\n"
        "Expected runtime is intentionally not estimated. After smoke, use median step time × 200 and separately report a 25% safety margin, together with allocated/reserved/driver VRAM.\n",
        encoding="utf-8",
    )
    (REPORTS / "next_executable_stage.md").write_text(
        "# Next executable stage\n\n`READY_FOR_A3_V2_RESOURCE_SMOKE`\n\nOnly the defined A3_v2 two-step resource smoke may be requested next. It is not authorized or run by this task. Do not resume `A3_legacy_aborted_step34_invalid`; do not start the 200-step run without separate authorization.\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "READY_FOR_A3_V2_RESOURCE_SMOKE", "contract_sha256": hashes}, sort_keys=True))


if __name__ == "__main__":
    main()
