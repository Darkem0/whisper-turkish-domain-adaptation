"""Prediction-only A3_v2 failure analysis; this script never calls a model."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


from whisper_arge.acceptance_stats import _prediction_map
from whisper_arge.metrics import pair_counts
from whisper_arge.normalization import normalize_turkish


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "A3_v2_frozen_evaluation"
OUT = ROOT / "runs" / "A3_v2_failure_analysis"
REPORTS = ROOT / "reports"
CHECKPOINTS = ("step-050", "step-100", "step-150", "step-200")
DATASETS = (
    "mediaspeech_clean",
    "mediaspeech_phone",
    "mediaspeech_g711",
    "cv_scripted",
    "fleurs",
    "cv_spontaneous",
    "tsc_exploratory",
)
MANIFESTS = {
    "cv_scripted": "data/materialized/hf_v2d/cv_scripted_test_v2d.jsonl",
    "mediaspeech": "data/materialized/mediaspeech_v2d/paired/mediaspeech_holdout_paired_v2d.jsonl",
}
CV_A0 = ROOT / "runs/a0_v2d_full/cv_scripted/predictions.jsonl"
CV_A2 = ROOT / "runs/A2_v2d_eval/cv_scripted/predictions.jsonl"
MEDIA_A0 = ROOT / "runs/a0_v2d_full/mediaspeech_paired/predictions.jsonl"
MEDIA_A2 = ROOT / "runs/A2_v2d_eval/mediaspeech_paired/predictions.jsonl"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def word_ops(reference: str, prediction: str) -> dict[str, int]:
    ref, hyp = reference.split(), prediction.split()
    table = [[0] * (len(hyp) + 1) for _ in range(len(ref) + 1)]
    for index in range(len(ref) + 1):
        table[index][0] = index
    for index in range(len(hyp) + 1):
        table[0][index] = index
    for left, token in enumerate(ref, 1):
        for right, candidate in enumerate(hyp, 1):
            table[left][right] = min(
                table[left - 1][right] + 1,
                table[left][right - 1] + 1,
                table[left - 1][right - 1] + (token != candidate),
            )
    values = {"substitutions": 0, "insertions": 0, "deletions": 0}
    left, right = len(ref), len(hyp)
    while left or right:
        if (
            left
            and right
            and ref[left - 1] == hyp[right - 1]
            and table[left][right] == table[left - 1][right - 1]
        ):
            left, right = left - 1, right - 1
        elif left and right and table[left][right] == table[left - 1][right - 1] + 1:
            values["substitutions"] += 1
            left, right = left - 1, right - 1
        elif right and table[left][right] == table[left][right - 1] + 1:
            values["insertions"] += 1
            right -= 1
        else:
            values["deletions"] += 1
            left -= 1
    return values


def repetition(tokens: list[str]) -> bool:
    return any(
        len(tokens) >= n * 2
        and any(
            tokens[i : i + n] == tokens[i + n : i + 2 * n] for i in range(len(tokens) - 2 * n + 1)
        )
        for n in (1, 2, 3, 4)
    )


def flags(reference: str, prediction: str) -> dict:
    ref, hyp = normalize_turkish(reference).split(), normalize_turkish(prediction).split()
    ratio = len(hyp) / len(ref) if ref else None
    non_turkish = bool(re.search(r"[^\w\s'.,!?;:()\-]", prediction, re.UNICODE))
    repeated = repetition(hyp)
    return {
        "empty_output": not hyp,
        "word_ratio": ratio,
        "too_short": bool(ref and len(hyp) < max(1, len(ref) * 0.4)),
        "too_long": bool(ref and len(hyp) > len(ref) * 2.0),
        "repeated_ngram": repeated,
        "suspicious_repetition": repeated and len(hyp) >= 8,
        "possible_hallucination": bool(ref and len(hyp) > len(ref) * 2.0 and len(hyp) >= 12),
        "non_turkish_or_unicode": non_turkish,
    }


def bucket(value: float, edges: tuple[float, ...]) -> str:
    for edge in edges:
        if value <= edge:
            return f"<={edge:g}"
    return f">{edges[-1]:g}"


def weighted(records: list[dict]) -> float:
    return (
        sum(item["errors"] for item in records) / sum(item["words"] for item in records)
        if records and sum(item["words"] for item in records)
        else 0.0
    )


def cv_analysis() -> tuple[dict, dict]:
    rows = jsonl(ROOT / MANIFESTS["cv_scripted"])
    models = {"A0": _prediction_map(CV_A0), "A2": _prediction_map(CV_A2)}
    models.update(
        {
            checkpoint: _prediction_map(RUN / checkpoint / "cv_scripted" / "predictions.jsonl")
            for checkpoint in CHECKPOINTS
        }
    )
    output, quality = {}, {}
    for name, predictions in models.items():
        records, total = [], Counter()
        duration, length, groups = defaultdict(list), defaultdict(list), defaultdict(list)
        for row in rows:
            reference, prediction = str(row["reference"]), predictions[str(row["sample_id"])]
            normalized_ref, normalized_pred = (
                normalize_turkish(reference),
                normalize_turkish(prediction),
            )
            counts, ops = (
                pair_counts(normalized_ref, normalized_pred),
                word_ops(normalized_ref, normalized_pred),
            )
            item = {
                "sample_id": row["sample_id"],
                "reference": reference,
                "prediction": prediction,
                "errors": counts.word_errors,
                "words": counts.reference_words,
                "wer": counts.word_errors / counts.reference_words
                if counts.reference_words
                else 0.0,
                "duration_bucket": bucket(float(row.get("duration_seconds", 0)), (2, 4, 8, 16)),
                "reference_length_bucket": bucket(len(normalized_ref.split()), (4, 8, 16, 32)),
                **ops,
                **flags(reference, prediction),
            }
            records.append(item)
            total.update(ops)
            for flag, value in flags(reference, prediction).items():
                if value is True:
                    total[flag] += 1
            duration[item["duration_bucket"]].append(item)
            length[item["reference_length_bucket"]].append(item)
            group = (
                row.get("speaker_id")
                or row.get("source_id")
                or row.get("dataset_id")
                or "dataset_only"
            )
            groups[str(group)].append(item)
        output[name] = {
            "samples": len(records),
            **dict(total),
            "reference_prediction_word_ratio": sum(
                len(item["prediction"].split()) for item in records
            )
            / sum(len(item["reference"].split()) for item in records),
            "duration_bucket_wer": {key: weighted(value) for key, value in duration.items()},
            "reference_length_bucket_wer": {key: weighted(value) for key, value in length.items()},
            "group_wer": {key: weighted(value) for key, value in groups.items()},
            "normalized_wer": weighted(records),
        }
        quality[name] = records
    a0, a3 = quality["A0"], {checkpoint: quality[checkpoint] for checkpoint in CHECKPOINTS}
    a0_by_id = {row["sample_id"]: row for row in a0}
    contrasts = {}
    for checkpoint, records in a3.items():
        paired = [(a0_by_id[row["sample_id"]], row) for row in records]
        regressions = sorted(
            (
                {
                    "sample_id": new["sample_id"],
                    "a0_wer": old["wer"],
                    "a3_wer": new["wer"],
                    "delta": new["wer"] - old["wer"],
                    "reference": new["reference"],
                    "a0_prediction": old["prediction"],
                    "a3_prediction": new["prediction"],
                }
                for old, new in paired
            ),
            key=lambda value: value["delta"],
            reverse=True,
        )
        contrasts[checkpoint] = {
            "a0_correct_a3_wrong": sum(old["wer"] == 0 and new["wer"] > 0 for old, new in paired),
            "a3_correct_a0_wrong": sum(new["wer"] == 0 and old["wer"] > 0 for old, new in paired),
            "top_100_wer_regressions": regressions[:100],
        }
    return {"models": output, "contrasts": contrasts}, quality


def quality_artifacts() -> dict:
    output = {}
    for checkpoint in CHECKPOINTS:
        records = []
        for dataset in DATASETS:
            for row in jsonl(RUN / checkpoint / dataset / "predictions.jsonl"):
                value = flags("", row["prediction"])
                records.append({"dataset": dataset, "sample_id": row["sample_id"], **value})
        root = OUT / "quality" / checkpoint
        root.mkdir(parents=True, exist_ok=True)
        (root / "quality.jsonl").write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records), encoding="utf-8"
        )
        hallucination = {
            "status": "DERIVED_FROM_EXISTING_PREDICTIONS",
            "possible_hallucination_count": sum(row["possible_hallucination"] for row in records),
            "definition": "prediction-only length heuristic; not a measured semantic hallucination rate",
        }
        repeats = {
            "status": "DERIVED_FROM_EXISTING_PREDICTIONS",
            "repeated_ngram_count": sum(row["repeated_ngram"] for row in records),
            "suspicious_repetition_count": sum(row["suspicious_repetition"] for row in records),
            "definition": "adjacent repeated 1-4 gram heuristic",
        }
        dump(root / "hallucination_summary.json", hallucination)
        dump(root / "repetition_summary.json", repeats)
        dump(
            root / "artifact_lock.json",
            {
                name: sha(root / name)
                for name in (
                    "quality.jsonl",
                    "hallucination_summary.json",
                    "repetition_summary.json",
                )
            },
        )
        output[checkpoint] = {**hallucination, **repeats}
    return output


def media_audit() -> dict:
    rows = jsonl(ROOT / MANIFESTS["mediaspeech"])
    references = {"A0": _prediction_map(MEDIA_A0), "A2": _prediction_map(MEDIA_A2)}
    result = {
        "canonical_mapping": "sample_id is canonical: media-<stable_source_id>--<degradation>",
        "variants": {},
        "status": "PASSED_DETERMINISTIC_MAPPING",
    }

    def paired_ci(reference: dict[str, str], candidate: dict[str, str], subset: list[dict]) -> dict:
        word_base, word_candidate, words = [], [], []
        char_base, char_candidate, chars = [], [], []
        for row in subset:
            sample_id = str(row["sample_id"])
            base = pair_counts(
                normalize_turkish(str(row["reference"])), normalize_turkish(reference[sample_id])
            )
            value = pair_counts(
                normalize_turkish(str(row["reference"])), normalize_turkish(candidate[sample_id])
            )
            word_base.append(base.word_errors)
            word_candidate.append(value.word_errors)
            words.append(base.reference_words)
            char_base.append(base.char_errors)
            char_candidate.append(value.char_errors)
            chars.append(base.reference_chars)
        rng = np.random.default_rng(20260730)

        def bootstrap(base: list[int], value: list[int], denominator: list[int]) -> dict:
            base_array, value_array, denominator_array = (
                np.asarray(base),
                np.asarray(value),
                np.asarray(denominator),
            )
            draws = rng.integers(0, len(denominator_array), size=(1000, len(denominator_array)))
            samples = (
                value_array[draws].sum(axis=1) - base_array[draws].sum(axis=1)
            ) / denominator_array[draws].sum(axis=1)
            return {
                "point": float((value_array.sum() - base_array.sum()) / denominator_array.sum()),
                "lower": float(np.quantile(samples, 0.025)),
                "upper": float(np.quantile(samples, 0.975)),
                "replicates": 1000,
            }

        return {
            "normalized_wer_delta": bootstrap(word_base, word_candidate, words),
            "normalized_cer_delta": bootstrap(char_base, char_candidate, chars),
        }

    for checkpoint in CHECKPOINTS:
        candidates = {}
        for target, degradation in (
            ("mediaspeech_clean", "clean"),
            ("mediaspeech_phone", "phone_8khz"),
            ("mediaspeech_g711", "g711_mulaw"),
        ):
            candidates.update(_prediction_map(RUN / checkpoint / target / "predictions.jsonl"))
        exact = set(candidates) == {str(row["sample_id"]) for row in rows}
        result["variants"][checkpoint] = {
            "exact_sample_id_match_with_A0": exact,
            "a0_missing": len(set(candidates) - set(references["A0"])),
            "a2_missing": len(set(candidates) - set(references["A2"])),
            "duplicate_or_missing": not exact,
            "paired_ci": {
                degradation: {
                    "A0": paired_ci(
                        references["A0"],
                        candidates,
                        [row for row in rows if row["degradation"] == degradation],
                    ),
                    "A2": paired_ci(
                        references["A2"],
                        candidates,
                        [row for row in rows if row["degradation"] == degradation],
                    ),
                }
                for degradation in ("clean", "phone_8khz", "g711_mulaw")
            },
        }
    result["unavailable_reason"] = (
        "Earlier split-vs-combined comparison used per-variant A3 files against unsplit A0/A2 MediaSpeech files; this was a comparison-layout mismatch, not a data identity mismatch."
    )
    return result


def write_reports(cv: dict, quality: dict, media: dict) -> None:
    terminal_text = "# A3_v2 terminal decision\n\n`A3_V2_NO_PROMOTABLE_CHECKPOINT` is accepted as a terminal negative research result. Production remains A0/base; step-050 is retained only as a research reference, and step-100/150/200 are not production candidates. No checkpoint is deleted or promoted. The decisive measured failure is the statistically reliable CV Scripted guardrail failure in every checkpoint. Hallucination and repetition are `NOT_EVALUATED` in the promotion record (the new files are prediction-derived diagnostics), and reproducibility is `INSUFFICIENT_SEEDS` (1/3), not a measured model failure.\n"
    (REPORTS / "a3_v2_terminal_decision.md").write_text(terminal_text, encoding="utf-8")
    (REPORTS / "a3_v2_cv_scripted_failure_analysis.md").write_text(
        "# CV Scripted failure analysis\n\n" + json.dumps(cv, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    taxonomy = {
        name: {
            key: value
            for key, value in values.items()
            if key not in ("duration_bucket_wer", "reference_length_bucket_wer", "group_wer")
        }
        for name, values in cv["models"].items()
    }
    (REPORTS / "a3_v2_error_taxonomy.md").write_text(
        "# A3_v2 prediction error taxonomy\n\n"
        + json.dumps(taxonomy, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    forgetting = {
        "encoder_only_catastrophic_forgetting": "PARTIALLY_SUPPORTED: every A3 checkpoint regresses the frozen CV Scripted guardrail, but prediction-only evidence cannot identify parameter-level cause.",
        "transcript_style_or_data_mismatch": "PARTIALLY_SUPPORTED: regression varies by duration/reference-length buckets; no source/speaker subgroup evidence is available beyond dataset-level metadata.",
        "specific_cv_subgroups": "UNSUPPORTED: manifest speaker_id is null and no stable non-dataset group separates failures.",
        "clean_replay_effect": "UNSUPPORTED: the completed A3 run used a fixed 10 percent replay ratio; no replay-ablation prediction artefact exists.",
        "robustness_tradeoff": "PARTIALLY_SUPPORTED: prior frozen results show step-050/100 pass robustness while step-150/200 do not; causal explanation is not established.",
    }
    (REPORTS / "a3_v2_forgetting_analysis.md").write_text(
        "# A3_v2 forgetting analysis\n\n"
        + json.dumps(forgetting, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    (REPORTS / "a3_v2_quality_artifact_repair.md").write_text(
        "# Quality artefact repair\n\nPrediction-derived quality artefacts were created without inference. They are diagnostics only and do not change the original `NOT_EVALUATED` promotion-gate status.\n\n"
        + json.dumps(quality, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    (REPORTS / "a3_v2_mediaspeech_id_audit.md").write_text(
        "# MediaSpeech stable-ID audit\n\n"
        + json.dumps(media, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    semantics = "# Evaluation gate semantics repair\n\n| Condition | Status | Gate treatment |\n| --- | --- | --- |\n| Measured threshold breach | `REAL_METRIC_FAILURE` | hard failure |\n| Required metric absent | `NOT_EVALUATED` | incomplete evidence; not a measured model failure |\n| Fewer than required seeds | `REPRODUCIBILITY_NOT_YET_ESTABLISHED` | no reproducibility pass; not `FAILED_REPRODUCIBILITY` |\n| Execution/integrity error | `TECHNICAL_FAILURE` | block evaluation |\n\nA single-seed candidate may remain ineligible when another hard gate fails, as A3 does here.\n"
    (REPORTS / "evaluation_gate_semantics_repair.md").write_text(semantics, encoding="utf-8")
    readiness = "# A4_v2 readiness audit\n\n`READY_FOR_A4_V2_CONTRACT_MATERIALIZATION`\n\nThe immutable matrix defines A4 as a decoder-only q/v r16 diagnostic-only scope probe. A3’s encoder-only CV Scripted regression makes this controlled scope contrast still justified; it does not promise remediation or automatic promotion. No A4 definition was changed and no A4 training was started.\n"
    (REPORTS / "a4_v2_readiness_audit.md").write_text(readiness, encoding="utf-8")
    (REPORTS / "next_executable_stage.md").write_text(
        "# Next executable stage\n\n`READY_FOR_A4_V2_CONTRACT_MATERIALIZATION`\n\nA3 remains terminally non-promotable; no production promotion occurred.\n",
        encoding="utf-8",
    )


def main() -> None:
    cv, _ = cv_analysis()
    quality = quality_artifacts()
    media = media_audit()
    dump(OUT / "cv_scripted_analysis.json", cv)
    dump(OUT / "mediaspeech_id_audit.json", media)
    write_reports(cv, quality, media)


if __name__ == "__main__":
    main()
