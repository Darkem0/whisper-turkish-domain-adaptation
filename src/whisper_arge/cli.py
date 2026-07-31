from __future__ import annotations

import argparse
import json
from pathlib import Path

from .evaluation import evaluate
from .evaluation_v2 import evaluate_v2
from .calibration import smoke_calibration
from .a0_report import build_a0_report
from .acceptance_stats import audit_acceptance_statistics
from .training_contract import create_training_contract
from .lora_train import run_lora_steps
from .lora_audit import audit_lora_run
from .adapter_inference import cache_adapter_predictions_batch
from .candidate_evaluation import dry_run_candidate_v2d, evaluate_candidate_v2d
from .inference import (
    cache_base_predictions,
    cache_base_predictions_batch,
    finalize_base_predictions,
    make_deterministic_subset,
)
from .ledger import summarize
from .lock import verify_lock
from .manifests import validate_manifest
from .matrix import validate_matrix
from .materialize import disk_preflight, leakage_report, materialize_rows, materialize_tsc_rows
from .provenance import capture_environment, reserve_run
from .tsc import fetch_tsc, index_tsc
from .tsc_audit import audit_tsc_leakage
from .tsc_official import materialize_tsc_official
from .cv_spontaneous import materialize_cv_spontaneous
from .hf_corpora import finalize_hf_corpus_manifest, materialize_hf_corpus_batch
from .mediaspeech import (
    finalize_mediaspeech_manifests,
    index_mediaspeech_batch,
    materialize_mediaspeech,
    materialize_mediaspeech_batch,
)
from .mediaspeech_degradation import (
    finalize_mediaspeech_degradations,
    materialize_mediaspeech_degradations,
)


def _print(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description="Whisper Turkish autoresearch controls")
    commands = parser.add_subparsers(dest="command", required=True)
    lock_command = commands.add_parser("verify-eval-lock")
    lock_command.add_argument("--lock", default="evaluation/EVAL_LOCK.json")
    commands.add_parser("capture-environment")
    manifest = commands.add_parser("validate-manifest")
    manifest.add_argument("path")
    matrix = commands.add_parser("validate-matrix")
    matrix.add_argument("path")
    ledger = commands.add_parser("ledger-summary")
    ledger.add_argument("path")
    evaluation = commands.add_parser("evaluate")
    evaluation.add_argument("--manifest", required=True)
    evaluation.add_argument("--predictions", required=True)
    evaluation.add_argument("--baseline-report")
    evaluation.add_argument("--output")
    evaluation.add_argument("--v2", action="store_true")
    materialize = commands.add_parser("materialize-v2")
    materialize.add_argument("--source-manifest", required=True)
    materialize.add_argument("--output", required=True)
    materialize.add_argument("--group-field", required=True, choices=["source_id", "speaker_id"])
    materialize.add_argument("--holdout-fraction", type=float, default=0.2)
    materialize.add_argument("--seed", type=int, default=20260730)
    materialize.add_argument("--dry-run", action="store_true")
    materialize.add_argument("--tsc-archive-url")
    materialize.add_argument("--destination", default=".")
    materialize.add_argument("--tsc-mode", choices=["research_provisional", "commercial_cleared"])
    materialize.add_argument("--commercial-clearance-evidence")
    materialize.add_argument("--leakage-report")
    materialize.add_argument("--tsc-holdout-hours", type=float)
    fetch = commands.add_parser("fetch-tsc")
    fetch.add_argument("--url", required=True)
    fetch.add_argument("--output", required=True)
    fetch.add_argument(
        "--mode", required=True, choices=["research_provisional", "commercial_cleared"]
    )
    fetch.add_argument("--commercial-clearance-evidence")
    index = commands.add_parser("index-tsc")
    index.add_argument("--archive", required=True)
    index.add_argument("--output", required=True)
    index.add_argument("--leakage-report", required=True)
    index.add_argument("--revision", required=True)
    official = commands.add_parser("materialize-tsc-official")
    official.add_argument("--archive", required=True)
    official.add_argument("--index", required=True)
    official.add_argument("--output-root", required=True)
    official.add_argument("--include-train", action="store_true")
    official.add_argument("--seed", type=int, default=20260730)
    audit = commands.add_parser("audit-tsc-leakage")
    audit.add_argument("--archive", required=True)
    audit.add_argument("--index", required=True)
    audit.add_argument("--output", required=True)
    audit.add_argument("--limit", type=int, default=10000)
    audit.add_argument("--seed", type=int, default=20260730)
    cvsp = commands.add_parser("materialize-cv-spontaneous")
    cvsp.add_argument("--archive", required=True)
    cvsp.add_argument("--output-root", required=True)
    cvsp.add_argument("--revision", required=True)
    cvsp.add_argument("--seed", type=int, default=20260730)
    media = commands.add_parser("materialize-mediaspeech")
    media.add_argument("--archive", required=True)
    media.add_argument("--output-root", required=True)
    media.add_argument("--revision", default="SLR108")
    media.add_argument("--seed", type=int, default=20260730)
    media_batch = commands.add_parser("materialize-mediaspeech-batch")
    media_batch.add_argument("--archive", required=True)
    media_batch.add_argument("--output-root", required=True)
    media_batch.add_argument("--revision", default="SLR108")
    media_batch.add_argument("--seed", type=int, default=20260730)
    media_batch.add_argument("--batch-size", type=int, default=300)
    media_index = commands.add_parser("materialize-mediaspeech-index-batch")
    media_index.add_argument("--archive", required=True)
    media_index.add_argument("--output-root", required=True)
    media_index.add_argument("--batch-size", type=int, default=300)
    media_manifest = commands.add_parser("finalize-mediaspeech-manifests")
    media_manifest.add_argument("--output-root", required=True)
    media_manifest.add_argument("--seed", type=int, default=20260730)
    media_degrade = commands.add_parser("materialize-mediaspeech-degradation-batch")
    media_degrade.add_argument("--holdout-manifest", required=True)
    media_degrade.add_argument("--output-root", required=True)
    media_degrade.add_argument("--batch-size", type=int, default=100)
    commands.add_parser("finalize-mediaspeech-degradations").add_argument(
        "--output-root", required=True
    )
    hf_batch = commands.add_parser("materialize-hf-corpus-batch")
    hf_batch.add_argument("--corpus", required=True, choices=["cv_scripted", "fleurs_tr"])
    hf_batch.add_argument("--split", required=True)
    hf_batch.add_argument("--output-root", required=True)
    hf_batch.add_argument("--batch-size", type=int, default=100)
    hf_finalize = commands.add_parser("finalize-hf-corpus-manifest")
    hf_finalize.add_argument("--corpus", required=True, choices=["cv_scripted", "fleurs_tr"])
    hf_finalize.add_argument("--split", required=True)
    hf_finalize.add_argument("--output-root", required=True)
    base_cache = commands.add_parser("cache-base-predictions")
    base_cache.add_argument("--manifest", required=True)
    base_cache.add_argument("--output", required=True)
    base_cache.add_argument("--suite", default="evaluation/suite_v2.json")
    base_cache.add_argument("--dry-run", action="store_true")
    base_batch = commands.add_parser("cache-base-predictions-batch")
    base_batch.add_argument("--manifest", required=True)
    base_batch.add_argument("--output-root", required=True)
    base_batch.add_argument("--suite", default="evaluation/suite_v2d.json")
    base_batch.add_argument("--batch-size", type=int, default=5)
    base_batch.add_argument("--max-samples", type=int)
    base_batch.add_argument("--seed", type=int, default=20260730)
    base_finalize = commands.add_parser("finalize-base-predictions")
    base_finalize.add_argument("--output-root", required=True)
    adapter_batch = commands.add_parser("cache-adapter-predictions-batch")
    adapter_batch.add_argument("--manifest", required=True)
    adapter_batch.add_argument("--output-root", required=True)
    adapter_batch.add_argument("--adapter", required=True)
    adapter_batch.add_argument("--suite", default="evaluation/suite_v2d.json")
    adapter_batch.add_argument("--model-revision", required=True)
    adapter_batch.add_argument("--batch-size", type=int, default=25)
    subset = commands.add_parser("make-eval-subset")
    subset.add_argument("--manifest", required=True)
    subset.add_argument("--output", required=True)
    subset.add_argument("--max-samples", required=True, type=int)
    subset.add_argument("--seed", type=int, default=20260730)
    a0_report = commands.add_parser("build-a0-report")
    a0_report.add_argument("--output-root", default="runs/a0_v2d_final")
    stats = commands.add_parser("audit-acceptance-statistics")
    stats.add_argument("--output", default="runs/a0_v2d_final/acceptance_statistics_audit_v2d.json")
    stats.add_argument("--replicates", type=int, default=10000)
    stats.add_argument("--seed", type=int, default=20260730)
    contract = commands.add_parser("create-training-contract-v2d")
    contract.add_argument("--output-root", default="data/materialized/training_v2d")
    contract.add_argument("--seed", type=int, default=20260730)
    contract.add_argument("--steps", type=int, default=200)
    train = commands.add_parser("run-lora-v2d")
    train.add_argument("--condition", required=True, choices=["A1", "A2", "A3", "A6"])
    train.add_argument("--output-root", required=True)
    train.add_argument("--steps", type=int, required=True)
    train.add_argument("--technical-smoke", action="store_true")
    train.add_argument("--gpu-telemetry", action="store_true")
    train.add_argument("--seed", type=int, default=20260730)
    audit_run = commands.add_parser("audit-lora-run-v2d")
    audit_run.add_argument("--run-root", required=True)
    candidate_eval = commands.add_parser("evaluate-candidate-v2d")
    candidate_eval.add_argument("--candidate-root", required=True)
    candidate_eval.add_argument("--seed", type=int, default=20260730)
    candidate_dry = commands.add_parser("dry-run-candidate-v2d")
    candidate_dry.add_argument("--candidate-root", required=True)
    calibration = commands.add_parser("smoke-calibration")
    calibration.add_argument("--results", required=True)
    reserve = commands.add_parser("reserve-run")
    reserve.add_argument("--config", required=True)
    reserve.add_argument("--ledger", default="ledger/experiments.jsonl")
    reserve.add_argument("--runs-root", default="runs")
    args = parser.parse_args()

    if args.command == "verify-eval-lock":
        errors = verify_lock(args.lock)
        if errors:
            raise SystemExit("\n".join(errors))
        _print({"status": "ok", "lock": args.lock})
    elif args.command == "capture-environment":
        _print(capture_environment())
    elif args.command == "validate-manifest":
        _print(validate_manifest(args.path))
    elif args.command == "validate-matrix":
        _print(validate_matrix(args.path))
    elif args.command == "ledger-summary":
        _print(summarize(args.path))
    elif args.command == "reserve-run":
        _print(reserve_run(args.config, args.ledger, args.runs_root))
    elif args.command == "materialize-v2":
        if not 0 < args.holdout_fraction < 1:
            raise SystemExit("--holdout-fraction must be between 0 and 1")
        if args.tsc_archive_url:
            preflight = disk_preflight(args.tsc_archive_url, args.destination)
            _print({"tsc_preflight": preflight})
            if not preflight["sufficient"]:
                raise SystemExit(
                    "TSC download/materialization not started: disk preflight is insufficient or unresolved"
                )
        if args.tsc_mode:
            from .tsc import assert_tsc_use_mode

            assert_tsc_use_mode(args.tsc_mode, args.commercial_clearance_evidence)
        if args.tsc_holdout_hours:
            _print(
                materialize_tsc_rows(
                    args.source_manifest,
                    args.output,
                    seed=args.seed,
                    dry_run=args.dry_run,
                    holdout_hours=args.tsc_holdout_hours,
                )
            )
        else:
            _print(
                materialize_rows(
                    args.source_manifest,
                    args.output,
                    holdout_fraction=args.holdout_fraction,
                    seed=args.seed,
                    group_field=args.group_field,
                    dry_run=args.dry_run,
                )
            )
        if args.leakage_report:
            report = leakage_report(
                args.source_manifest,
                group_field=args.group_field,
                holdout_hours=args.tsc_holdout_hours or 10,
                seed=args.seed,
            )
            Path(args.leakage_report).parent.mkdir(parents=True, exist_ok=True)
            Path(args.leakage_report).write_text(
                json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            _print({"leakage_report": args.leakage_report, **report})
    elif args.command == "fetch-tsc":
        _print(
            fetch_tsc(
                args.url,
                args.output,
                mode=args.mode,
                clearance_evidence=args.commercial_clearance_evidence,
            )
        )
    elif args.command == "index-tsc":
        _print(index_tsc(args.archive, args.output, args.leakage_report, revision=args.revision))
    elif args.command == "materialize-tsc-official":
        _print(
            materialize_tsc_official(
                args.archive,
                args.index,
                args.output_root,
                seed=args.seed,
                include_train=args.include_train,
            )
        )
    elif args.command == "audit-tsc-leakage":
        _print(
            audit_tsc_leakage(
                args.archive, args.index, args.output, limit=args.limit, seed=args.seed
            )
        )
    elif args.command == "materialize-cv-spontaneous":
        _print(
            materialize_cv_spontaneous(
                args.archive, args.output_root, revision=args.revision, seed=args.seed
            )
        )
    elif args.command == "materialize-mediaspeech":
        _print(
            materialize_mediaspeech(
                args.archive, args.output_root, revision=args.revision, seed=args.seed
            )
        )
    elif args.command == "materialize-mediaspeech-batch":
        _print(
            materialize_mediaspeech_batch(
                args.archive,
                args.output_root,
                revision=args.revision,
                seed=args.seed,
                batch_size=args.batch_size,
            )
        )
    elif args.command == "materialize-mediaspeech-index-batch":
        _print(index_mediaspeech_batch(args.archive, args.output_root, batch_size=args.batch_size))
    elif args.command == "finalize-mediaspeech-manifests":
        _print(finalize_mediaspeech_manifests(args.output_root, seed=args.seed))
    elif args.command == "materialize-mediaspeech-degradation-batch":
        _print(
            materialize_mediaspeech_degradations(
                args.holdout_manifest, args.output_root, batch_size=args.batch_size
            )
        )
    elif args.command == "finalize-mediaspeech-degradations":
        _print(finalize_mediaspeech_degradations(args.output_root))
    elif args.command == "materialize-hf-corpus-batch":
        _print(
            materialize_hf_corpus_batch(
                args.corpus, args.split, args.output_root, batch_size=args.batch_size
            )
        )
    elif args.command == "finalize-hf-corpus-manifest":
        _print(finalize_hf_corpus_manifest(args.corpus, args.split, args.output_root))
    elif args.command == "cache-base-predictions":
        suite = json.loads(Path(args.suite).read_text(encoding="utf-8"))
        _print(
            cache_base_predictions(
                args.manifest, args.output, suite["decode_contract"], args.dry_run
            )
        )
    elif args.command == "cache-base-predictions-batch":
        suite = json.loads(Path(args.suite).read_text(encoding="utf-8"))
        _print(
            cache_base_predictions_batch(
                args.manifest,
                args.output_root,
                suite["decode_contract"],
                batch_size=args.batch_size,
                max_samples=args.max_samples,
                seed=args.seed,
            )
        )
    elif args.command == "finalize-base-predictions":
        _print(finalize_base_predictions(args.output_root))
    elif args.command == "cache-adapter-predictions-batch":
        suite = json.loads(Path(args.suite).read_text(encoding="utf-8"))
        _print(
            cache_adapter_predictions_batch(
                args.manifest,
                args.output_root,
                suite["decode_contract"],
                adapter_path=args.adapter,
                model_revision=args.model_revision,
                batch_size=args.batch_size,
            )
        )
    elif args.command == "make-eval-subset":
        _print(
            make_deterministic_subset(
                args.manifest, args.output, max_samples=args.max_samples, seed=args.seed
            )
        )
    elif args.command == "build-a0-report":
        _print(build_a0_report(args.output_root))
    elif args.command == "audit-acceptance-statistics":
        _print(audit_acceptance_statistics(args.output, replicates=args.replicates, seed=args.seed))
    elif args.command == "create-training-contract-v2d":
        _print(create_training_contract(args.output_root, seed=args.seed, steps=args.steps))
    elif args.command == "run-lora-v2d":
        _print(
            run_lora_steps(
                args.condition,
                args.output_root,
                steps=args.steps,
                technical_smoke=args.technical_smoke,
                gpu_telemetry=args.gpu_telemetry,
                seed=args.seed,
            )
        )
    elif args.command == "audit-lora-run-v2d":
        _print(audit_lora_run(args.run_root))
    elif args.command == "evaluate-candidate-v2d":
        _print(evaluate_candidate_v2d(args.candidate_root, seed=args.seed))
    elif args.command == "dry-run-candidate-v2d":
        _print(dry_run_candidate_v2d(args.candidate_root))
    elif args.command == "smoke-calibration":
        _print(smoke_calibration(args.results))
    else:
        report = (
            evaluate_v2(args.manifest, args.predictions)
            if args.v2
            else evaluate(args.manifest, args.predictions, args.baseline_report)
        )
        if args.output:
            Path(args.output).write_text(
                json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        _print(report)


if __name__ == "__main__":
    main()
