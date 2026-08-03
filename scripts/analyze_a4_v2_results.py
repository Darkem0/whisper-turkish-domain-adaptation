"""Read-only comparative analysis for completed A4_v2 frozen-evaluation artefacts.

This script never loads a model or audio.  It reuses locked manifests and
prediction JSONL files to calculate paired corpus WER/CER deltas and reports.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from rapidfuzz.distance import Levenshtein

from whisper_arge.normalization import normalize_turkish


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
CHECKPOINTS = ("step-050", "step-100", "step-150", "step-200")
SETS = {
    "mediaspeech_clean": ("data/materialized/mediaspeech_v2d/paired/mediaspeech_holdout_paired_v2d.jsonl", "clean"),
    "mediaspeech_phone": ("data/materialized/mediaspeech_v2d/paired/mediaspeech_holdout_paired_v2d.jsonl", "phone_8khz"),
    "mediaspeech_g711": ("data/materialized/mediaspeech_v2d/paired/mediaspeech_holdout_paired_v2d.jsonl", "g711_mulaw"),
    "cv_scripted": ("data/materialized/hf_v2d/cv_scripted_test_v2d.jsonl", None),
    "fleurs": ("data/materialized/fleurs_tr_v2d/fleurs_tr_test_v2d.jsonl", None),
    "cv_spontaneous": ("data/materialized/cv_spontaneous_v2c/cv_spontaneous_holdout_v2c.jsonl", None),
    "tsc_exploratory": ("data/materialized/tsc_v2a/tsc_full_v2a.jsonl", None),
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def prediction_map(path: Path) -> dict[str, str]:
    return {str(row["sample_id"]): str(row["prediction"]) for row in read_jsonl(path)}


def manifests() -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    for name, (relative, degradation) in SETS.items():
        rows = read_jsonl(ROOT / relative)
        if degradation:
            rows = [row for row in rows if row.get("degradation") == degradation]
        result[name] = rows
    return result


def prediction_path(model: str, checkpoint: str | None, dataset: str) -> Path:
    if model == "A0":
        base = {"mediaspeech_clean": "mediaspeech_paired", "mediaspeech_phone": "mediaspeech_paired", "mediaspeech_g711": "mediaspeech_paired", "cv_scripted": "cv_scripted", "fleurs": "fleurs", "cv_spontaneous": "cv_spontaneous", "tsc_exploratory": "tsc_exploratory"}[dataset]
        root = "runs/a0_v2d_smoke" if dataset == "cv_spontaneous" else "runs/a0_v2d_full"
        return ROOT / root / base / "predictions.jsonl"
    if model == "A2":
        base = "mediaspeech_paired" if dataset.startswith("mediaspeech_") else dataset
        return ROOT / "runs/A2_v2d_eval" / base / "predictions.jsonl"
    assert checkpoint
    root = "runs/A3_v2_frozen_evaluation" if model == "A3_step050" else "runs/A4_v2_frozen_evaluation"
    return ROOT / root / checkpoint / dataset / "predictions.jsonl"


def counts(rows: list[dict], predictions: dict[str, str]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    word_errors: list[int] = []
    words: list[int] = []
    char_errors: list[int] = []
    chars: list[int] = []
    for row in rows:
        sample_id = str(row["sample_id"])
        reference = normalize_turkish(str(row["reference"]))
        prediction = normalize_turkish(predictions[sample_id])
        reference_words, prediction_words = reference.split(), prediction.split()
        reference_chars, prediction_chars = reference.replace(" ", ""), prediction.replace(" ", "")
        word_errors.append(Levenshtein.distance(reference_words, prediction_words))
        words.append(len(reference_words))
        char_errors.append(Levenshtein.distance(reference_chars, prediction_chars))
        chars.append(len(reference_chars))
    return tuple(np.asarray(value, dtype=np.int64) for value in (word_errors, words, char_errors, chars))  # type: ignore[return-value]


def bootstrap(base: np.ndarray, candidate: np.ndarray, denom: np.ndarray, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    samples: list[np.ndarray] = []
    # Chunking keeps the 9,650-row comparisons bounded in RAM.
    for _ in range(1):
        draw = rng.integers(0, len(denom), size=(100, len(denom)))
        samples.append((candidate[draw].sum(axis=1) - base[draw].sum(axis=1)) / denom[draw].sum(axis=1))
    values = np.concatenate(samples)
    point = float((candidate.sum() - base.sum()) / denom.sum())
    return {"point": point, "lower": float(np.quantile(values, .025)), "upper": float(np.quantile(values, .975)), "replicates": 100}


def bootstrap_many(errors: dict[str, np.ndarray], denom: np.ndarray, seed: int) -> dict[str, np.ndarray]:
    """One deterministic resample matrix per dataset/metric, reused for all contrasts."""
    rng = np.random.default_rng(seed)
    draw = rng.integers(0, len(denom), size=(100, len(denom)))
    sampled_denominator = denom[draw].sum(axis=1)
    return {name: values[draw].sum(axis=1) / sampled_denominator for name, values in errors.items()}


def label(ci: dict, dataset: str) -> str:
    if dataset == "cv_spontaneous":
        return "report_only"
    if dataset == "tsc_exploratory":
        return "exploratory"
    if ci["upper"] < 0:
        return "statistically_supported_gain"
    if ci["lower"] > 0:
        return "statistically_supported_regression"
    return "inconclusive"


def fmt(value: float) -> str:
    return f"{value:.4f}"


def main() -> None:
    rows_by_set = manifests()
    models = ["A0", "A2", "A3_step050"]
    cache: dict[tuple[str, str, str | None], dict[str, str]] = {}

    def get(model: str, dataset: str, checkpoint: str | None = None) -> dict[str, str]:
        key = (model, dataset, checkpoint)
        if key not in cache:
            cache[key] = prediction_map(prediction_path(model, checkpoint, dataset))
        expected = {str(row["sample_id"]) for row in rows_by_set[dataset]}
        if set(cache[key]) & expected != expected:
            missing = len(expected - set(cache[key]))
            raise RuntimeError(f"unaligned predictions: {model}/{checkpoint}/{dataset}; missing={missing}")
        return cache[key]

    metric_rows: list[dict[str, object]] = []
    for model in models:
        checkpoint = "step-050" if model == "A3_step050" else None
        for dataset, rows in rows_by_set.items():
            werr, words, cerr, chars = counts(rows, get(model, dataset, checkpoint))
            metric_rows.append({"model": model, "checkpoint": checkpoint or "base", "dataset": dataset, "samples": len(rows), "normalized_wer": werr.sum() / words.sum(), "normalized_cer": cerr.sum() / chars.sum()})
    for checkpoint in CHECKPOINTS:
        for dataset, rows in rows_by_set.items():
            werr, words, cerr, chars = counts(rows, get("A4", dataset, checkpoint))
            metric_rows.append({"model": "A4", "checkpoint": checkpoint, "dataset": dataset, "samples": len(rows), "normalized_wer": werr.sum() / words.sum(), "normalized_cer": cerr.sum() / chars.sum()})

    lookup = {(str(row["model"]), str(row["checkpoint"]), str(row["dataset"])): row for row in metric_rows}
    for row in metric_rows:
        for ref, ref_cp in (("A0", "base"), ("A2", "base"), ("A3_step050", "step-050")):
            other = lookup[(ref, ref_cp, str(row["dataset"]))]
            row[f"wer_delta_vs_{ref}"] = float(row["normalized_wer"]) - float(other["normalized_wer"])
            row[f"cer_delta_vs_{ref}"] = float(row["normalized_cer"]) - float(other["normalized_cer"])
    with (REPORTS / "a0_a2_a3_a4_metrics_comparison.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = list(metric_rows[0])
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(metric_rows)

    ci_rows: list[dict[str, object]] = []
    for dataset_index, dataset in enumerate(("mediaspeech_clean", "mediaspeech_phone", "mediaspeech_g711", "cv_scripted", "fleurs")):
        rows = rows_by_set[dataset]
        source = {"A0": counts(rows, get("A0", dataset)), "A2": counts(rows, get("A2", dataset)), "A3_step050": counts(rows, get("A3_step050", dataset, "step-050"))}
        candidates = {checkpoint: counts(rows, get("A4", dataset, checkpoint)) for checkpoint in CHECKPOINTS}
        wer_samples = bootstrap_many({**{name: values[0] for name, values in source.items()}, **{checkpoint: values[0] for checkpoint, values in candidates.items()}}, source["A0"][1], 20260801 + dataset_index)
        cer_samples = bootstrap_many({**{name: values[2] for name, values in source.items()}, **{checkpoint: values[2] for checkpoint, values in candidates.items()}}, source["A0"][3], 20260901 + dataset_index)
        for checkpoint in CHECKPOINTS:
            for reference in source:
                for metric, sampled, error_index, denominator_index in (("normalized_WER", wer_samples, 0, 1), ("normalized_CER", cer_samples, 2, 3)):
                    point = float((candidates[checkpoint][error_index].sum() - source[reference][error_index].sum()) / source[reference][denominator_index].sum())
                    samples = sampled[checkpoint] - sampled[reference]
                    ci = {"point": point, "lower": float(np.quantile(samples, .025)), "upper": float(np.quantile(samples, .975)), "replicates": 100}
                    ci_rows.append({"checkpoint": checkpoint, "dataset": dataset, "reference": reference, "metric": metric, **ci, "classification": label(ci, dataset)})
    with (REPORTS / "a4_v2_paired_bootstrap_ci.json").open("w", encoding="utf-8") as handle:
        json.dump({"method": "paired stable sample_id, utterance-with-replacement, 100 replicates", "rows": ci_rows}, handle, ensure_ascii=False, indent=2)

    def value(checkpoint: str, dataset: str) -> float:
        return float(lookup[("A4", checkpoint, dataset)]["normalized_wer"])
    proxy = {cp: .5 * value(cp, "mediaspeech_clean") + .25 * value(cp, "mediaspeech_phone") + .25 * value(cp, "mediaspeech_g711") for cp in CHECKPOINTS}
    best = {dataset: min(CHECKPOINTS, key=lambda cp: value(cp, dataset)) for dataset in SETS}
    best["robustness_proxy"] = min(CHECKPOINTS, key=proxy.get)
    general = {cp: value(cp, "cv_scripted") - float(lookup[("A0", "base", "cv_scripted")]["normalized_wer"]) + value(cp, "fleurs") - float(lookup[("A0", "base", "fleurs")]["normalized_wer"]) for cp in CHECKPOINTS}
    lowest_general = min(CHECKPOINTS, key=general.get)

    lines = ["# A4_v2 comparative analysis", "", "All values are normalized corpus metrics reconstructed from locked predictions; lower is better. A4 remains diagnostic-only and no production promotion is made.", "", "## A4 checkpoint trajectory", "", "| Checkpoint | Clean WER | Phone WER | G.711 WER | Proxy | CV Scripted WER | FLEURS WER |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for cp in CHECKPOINTS:
        lines.append(f"| {cp} | {fmt(value(cp, 'mediaspeech_clean'))} | {fmt(value(cp, 'mediaspeech_phone'))} | {fmt(value(cp, 'mediaspeech_g711'))} | {fmt(proxy[cp])} | {fmt(value(cp, 'cv_scripted'))} | {fmt(value(cp, 'fleurs'))} |")
    lines += ["", "## Category-specific references", "", *[f"- {name}: `{checkpoint}`." for name, checkpoint in best.items()], f"- Lowest combined A0-relative CV Scripted + FLEURS WER regression: `{lowest_general}` (not a production score).", "", "The full A0/A2/A3-step-050/A4 table, including WER/CER absolute deltas, is in `a0_a2_a3_a4_metrics_comparison.csv`. A3 step-050 is the meaningful frozen-evaluation reference; it is retained as research-only and its terminal decision is unchanged."]
    (REPORTS / "a4_v2_comparative_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    ci_table = ["# A4_v2 paired bootstrap statistical analysis", "", "Paired stable `sample_id` matching passed for A0, A2, A3 step-050 and every A4 checkpoint on all analysed sets. Delta is A4 minus reference; negative favours A4. 95% percentile intervals use 100 deterministic utterance-resampling replicates; this is an exploratory precision level and should be increased before any future formal acceptance gate. CV Spontaneous is report-only and TSC exploratory, therefore they are excluded from inferential labels.", "", "| Checkpoint | Dataset | Ref | Metric | Delta | 95% CI | Classification |", "| --- | --- | --- | --- | ---: | --- | --- |"]
    for row in ci_rows:
        ci_table.append(f"| {row['checkpoint']} | {row['dataset']} | {row['reference']} | {row['metric']} | {fmt(float(row['point']))} | [{fmt(float(row['lower']))}, {fmt(float(row['upper']))}] | {row['classification']} |")
    (REPORTS / "a4_v2_statistical_analysis.md").write_text("\n".join(ci_table) + "\n", encoding="utf-8")

    attribution = """# Encoder–decoder attribution

## Design facts

| Experiment | Intervention | Replay |
| --- | --- | --- |
| A0 | base | n/a |
| A2 | encoder + decoder Q/V LoRA | experiment-specific prior design |
| A3 | encoder-only Q/V LoRA | 10% clean replay |
| A4 | decoder-only Q/V LoRA | 0% replay |

## Interpretation boundaries

- **Phone robustness is encoder-driven:** `HYPOTHESIS`, not established. A3/A4 differ simultaneously in LoRA location and replay, and A2 changes both encoder and decoder; the available factorial contrasts cannot isolate the encoder contribution.
- **Decoder-only helps the target domain:** supported only descriptively where an A4 MediaSpeech delta and its paired CI show a gain; it is not proof of a decoder-specific causal mechanism.
- **A3 CV Scripted regression is encoder-related:** `HYPOTHESIS`. Its measured regression is real in the A3 record, but A3's replay setting differs from A4.
- **Decoder involvement in A2 FLEURS regression:** `HYPOTHESIS` only. A2 is encoder+decoder and no decoder-only run with A2's replay/data conditions exists.
- **A2 requires the encoder+decoder combination:** unsupported. Its result cannot be decomposed without matched ablations.
- **Direct causal comparison blocked:** A3 versus A4 (layer target *and* replay), and A2 versus either A3/A4 (combined layer target plus prior experiment differences). The reports retain descriptive paired comparisons but do not convert them into causal claims.
"""
    (REPORTS / "a4_v2_encoder_decoder_attribution.md").write_text(attribution, encoding="utf-8")

    quality: dict[str, dict[str, int]] = {}
    for checkpoint in CHECKPOINTS:
        summary = {"samples": 0, "empty_output": 0, "extreme_length_ratio": 0, "repeated_adjacent_bigram": 0, "malformed_unicode": 0}
        for dataset, rows in rows_by_set.items():
            predictions = get("A4", dataset, checkpoint)
            for row in rows:
                reference = normalize_turkish(str(row["reference"]))
                prediction = normalize_turkish(predictions[str(row["sample_id"])])
                ref_words, pred_words = reference.split(), prediction.split()
                summary["samples"] += 1
                summary["empty_output"] += int(not pred_words)
                ratio = len(pred_words) / max(1, len(ref_words))
                summary["extreme_length_ratio"] += int(ratio < .25 or ratio > 4)
                summary["repeated_adjacent_bigram"] += int(any(pred_words[index:index + 2] == pred_words[index + 2:index + 4] for index in range(max(0, len(pred_words) - 3))))
                summary["malformed_unicode"] += int(any(0xD800 <= ord(char) <= 0xDFFF for char in prediction))
        quality[checkpoint] = summary
    (REPORTS / "a4_v2_quality_summary.md").write_text("# A4_v2 prediction-derived quality summary\n\nThese are deterministic diagnostics over the completed prediction artefacts, not a semantic hallucination or real-call safety evaluation.\n\n" + json.dumps(quality, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    framework = """# Revised production evaluation framework

This is a prospective framework; it does not rewrite A2/A3 terminal scientific records or promote A4.

## Dataset roles

- **Production-relevant:** MediaSpeech Phone, MediaSpeech G.711 and the predeclared MediaSpeech robustness proxy. Any natural/spontaneous telephone-like subset must be frozen and provenance-checked before it is added.
- **General-domain scientific monitoring:** CV Scripted, FLEURS, clean read speech and other company-external sets. Regressions are reported with paired CIs and investigated, but do not alone trigger automatic production rejection.
- **Critical-behavior guardrails:** empty output, prediction-derived repetition/length outliers, malformed/non-Turkish text, number/name errors and catastrophic paired regressions. Semantic hallucination, real call-flow safety and business terminology require a company-domain test set and manual review; they are `MISSING`, not inferred.

## Reclassification without changing terminal records

| Experiment | Existing scientific terminal | Additional operational class |
| --- | --- | --- |
| A2 | unchanged prior non-promotion record | insufficient_company_domain_evidence |
| A3 | A3_V2_NO_PROMOTABLE_CHECKPOINT | research_only; measured CV Scripted failure remains recorded |
| A4 | A4_V2_FROZEN_EVALUATION_COMPLETED, diagnostic-only | insufficient_company_domain_evidence |

No result above establishes production readiness without an independently frozen company-domain test set and critical-behavior audit.
"""
    framework += "\n## Available A4 prediction-derived guardrail diagnostics\n\n" + json.dumps(quality, ensure_ascii=False, indent=2) + "\n\nThese checks cannot establish semantic hallucination, number/name correctness in a business workflow, or company-call operational safety; those remain `MISSING` pending a frozen company-domain set and manual review.\n"
    (REPORTS / "revised_production_evaluation_framework.md").write_text(framework, encoding="utf-8")

    data_plan = """# Training-data quality audit plan before A5

## Stage 1 — automated audit

Run on the locked A5 candidate manifest without training: transcript normalization/casing/punctuation consistency; exact and near duplicate audio/text; duration/text-length, SNR/level and codec distributions; silence/near-silence; segment-boundary and audio-text duration outliers; recording/speaker/template overrepresentation; Turkish/foreign-token and number/date/currency/name coverage; and manifest channel labels. Audio–text semantic alignment, crosstalk and agent/customer correctness are flags for review, not automatically asserted from metadata.

## Stage 2 — stratified human audit

Independently inspect clean telephone, noisy telephone, G.711, short/long speech, numbers/totals, proper names, agent/customer-labelled rows, high/low baseline WER and high A0/A4 disagreement rows. Record audio, transcript, normalized transcript, assessor decision and reason.

| Issue | Severity rule | Prevalence estimate | Likely model effect | Action |
| --- | --- | --- | --- | --- |
| Wrong/misaligned transcript | critical | stratified audited rate with CI | destructive supervision | remove/correct; re-lock split |
| Truncation/extra speech/crosstalk | high | automated flag + manual confirmation | deletion/insertion bias | re-segment or exclude |
| Wrong agent/customer channel | high | labelled-sample audit | role/domain mismatch | correct label or exclude |
| Silent/near-silent or codec imbalance | medium | full-manifest rate | spurious robustness result | rebalance/stratify |
| Duplicate audio/text/template dominance | high | exact/near-duplicate clusters | memorization and misleading validation | group-aware deduplicate |
| Number/name/foreign-token/normalization gaps | medium | coverage table + manual rate | business-critical substitutions | targeted data repair |

The audit must publish raw counts, sampling frame, reviewed sample IDs, reviewer rubric and unresolved blockers before an A5 training contract is materialized.
"""
    (REPORTS / "training_data_quality_audit_plan.md").write_text(data_plan, encoding="utf-8")

    decision = """# A5 decision gate

## Decision

`DATA_QUALITY_AUDIT_REQUIRED_BEFORE_A5`

Priority order:

1. Execute and lock the two-stage training-data quality audit described in `training_data_quality_audit_plan.md`.
2. Materialize an independent frozen company-domain test set with explicit privacy/provenance approval before any production-oriented conclusion.
3. Only then decide whether the A5 hypothesis needs revision and materialize its contract.

Rationale: A4 is a diagnostic-only decoder ablation, A3/A4 attribution is replay-confounded, and the available public proxies do not provide company-domain behavioural evidence. A5 is not started by this decision.
"""
    (REPORTS / "a5_decision_gate.md").write_text(decision, encoding="utf-8")

    ledger = {"experiment": "A4_v2", "status": "A4_V2_FROZEN_EVALUATION_COMPLETED", "intervention": "fresh-base decoder-only Q/V LoRA r16, replay=0", "checkpoints": [50, 100, 150, 200], "integrity": "28/28 frozen targets and prediction locks verified", "promotion": "not performed; diagnostic-only", "comparative_analysis": "reports/a4_v2_comparative_analysis.md", "causal_limit": "A3 vs A4 confounded by replay; attribution is hypothesis only", "next_gate": "DATA_QUALITY_AUDIT_REQUIRED_BEFORE_A5"}
    ledger_path = REPORTS / "research_experiment_ledger.jsonl"
    existing_records = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines() if line] if ledger_path.exists() else []
    existing_records = [record for record in existing_records if record.get("experiment") != "A4_v2"]
    existing_records.append(ledger)
    ledger_path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in existing_records), encoding="utf-8")
    (REPORTS / "research_experiment_ledger.md").write_text("# Research experiment ledger\n\n| Experiment | Terminal result | Implication |\n| --- | --- | --- |\n| A3_v2 | `A3_V2_NO_PROMOTABLE_CHECKPOINT` | Preserve the A3 step-050 research reference; no promotion. |\n| A4_v2 | `A4_V2_FROZEN_EVALUATION_COMPLETED` | Diagnostic-only decoder ablation; complete analysis before A5. |\n", encoding="utf-8")
    result_log = REPORTS / "manuscript_results_log.md"
    result_entry = "A4_v2 completed all 28 frozen-evaluation targets with verified prediction locks. It is a decoder-only, zero-replay diagnostic ablation; its public-set comparison does not establish company-domain production readiness."
    if result_entry not in result_log.read_text(encoding="utf-8"):
        with result_log.open("a", encoding="utf-8") as handle:
            handle.write("\n" + result_entry + "\n")
    negative_log = REPORTS / "manuscript_negative_results_log.md"
    negative_entry = "A4_v2 does not isolate decoder causality from the A3 encoder-only result because replay differs (A3 10% clean replay; A4 0%). This is a design limitation, not a measured model failure."
    if negative_entry not in negative_log.read_text(encoding="utf-8"):
        with negative_log.open("a", encoding="utf-8") as handle:
            handle.write("\n" + negative_entry + "\n")
    (REPORTS / "next_executable_stage.md").write_text("# Next executable stage\n\n`DATA_QUALITY_AUDIT_REQUIRED_BEFORE_A5`\n\nPerform the locked, two-stage A5 training-data quality audit. A5 training, inference, frozen evaluation and production promotion are not authorized by this result.\n", encoding="utf-8")
    print(json.dumps({"status": "COMPLETED_READ_ONLY_ANALYSIS", "best": best, "lowest_general_regression": lowest_general, "proxy": proxy}, ensure_ascii=False))


if __name__ == "__main__":
    main()
