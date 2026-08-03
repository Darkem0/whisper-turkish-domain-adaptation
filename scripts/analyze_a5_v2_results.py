"""Read-only A5 frozen-evaluation comparison from locked prediction artefacts."""

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
    "mediaspeech_clean": (
        "data/materialized/mediaspeech_v2d/paired/mediaspeech_holdout_paired_v2d.jsonl",
        "clean",
    ),
    "mediaspeech_phone": (
        "data/materialized/mediaspeech_v2d/paired/mediaspeech_holdout_paired_v2d.jsonl",
        "phone_8khz",
    ),
    "mediaspeech_g711": (
        "data/materialized/mediaspeech_v2d/paired/mediaspeech_holdout_paired_v2d.jsonl",
        "g711_mulaw",
    ),
    "cv_scripted": ("data/materialized/hf_v2d/cv_scripted_test_v2d.jsonl", None),
    "fleurs": ("data/materialized/fleurs_tr_v2d/fleurs_tr_test_v2d.jsonl", None),
    "cv_spontaneous": (
        "data/materialized/cv_spontaneous_v2c/cv_spontaneous_holdout_v2c.jsonl",
        None,
    ),
    "tsc_exploratory": ("data/materialized/tsc_v2a/tsc_full_v2a.jsonl", None),
}


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def predictions(path: Path) -> dict[str, str]:
    return {str(row["sample_id"]): str(row["prediction"]) for row in jsonl(path)}


def path(model: str, checkpoint: str | None, dataset: str) -> Path:
    if model == "A0":
        root = "runs/a0_v2d_smoke" if dataset == "cv_spontaneous" else "runs/a0_v2d_full"
        name = "mediaspeech_paired" if dataset.startswith("mediaspeech_") else dataset
        return ROOT / root / name / "predictions.jsonl"
    if model == "A2":
        return (
            ROOT
            / "runs/A2_v2d_eval"
            / ("mediaspeech_paired" if dataset.startswith("mediaspeech_") else dataset)
            / "predictions.jsonl"
        )
    assert checkpoint
    root = {
        "A3": "runs/A3_v2_frozen_evaluation",
        "A4": "runs/A4_v2_frozen_evaluation",
        "A5": "runs/A5_v2_frozen_evaluation",
    }[model]
    return ROOT / root / checkpoint / dataset / "predictions.jsonl"


def counts(
    rows: list[dict], pred: dict[str, str]
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    values = [[], [], [], []]
    for row in rows:
        ref = normalize_turkish(str(row["reference"]))
        hyp = normalize_turkish(pred[str(row["sample_id"])])
        words, hwords = ref.split(), hyp.split()
        chars, hchars = ref.replace(" ", ""), hyp.replace(" ", "")
        values[0].append(Levenshtein.distance(words, hwords))
        values[1].append(len(words))
        values[2].append(Levenshtein.distance(chars, hchars))
        values[3].append(len(chars))
    return tuple(np.asarray(value, dtype=np.int64) for value in values)  # type: ignore[return-value]


def ci(
    base: tuple[np.ndarray, ...], candidate: tuple[np.ndarray, ...], metric: int, seed: int
) -> dict:
    error, denom = metric, metric + 1
    rng = np.random.default_rng(seed)
    draw = rng.integers(0, len(base[denom]), size=(200, len(base[denom])))
    values = (candidate[error][draw].sum(axis=1) - base[error][draw].sum(axis=1)) / base[denom][
        draw
    ].sum(axis=1)
    return {
        "point": float((candidate[error].sum() - base[error].sum()) / base[denom].sum()),
        "lower": float(np.quantile(values, 0.025)),
        "upper": float(np.quantile(values, 0.975)),
        "replicates": 200,
    }


def label(value: dict, dataset: str) -> str:
    if dataset == "cv_spontaneous":
        return "report_only"
    if dataset == "tsc_exploratory":
        return "exploratory"
    if value["upper"] < 0:
        return "statistically_supported_gain"
    if value["lower"] > 0:
        return "statistically_supported_regression"
    return "inconclusive"


def f(value: float) -> str:
    return f"{value:.4f}"


def main() -> None:
    rows = {}
    for name, (relative, degradation) in SETS.items():
        values = jsonl(ROOT / relative)
        rows[name] = [
            row for row in values if not degradation or row.get("degradation") == degradation
        ]
    cache: dict[tuple[str, str | None, str], dict[str, str]] = {}

    def get(model: str, checkpoint: str | None, dataset: str) -> dict[str, str]:
        key = (model, checkpoint, dataset)
        if key not in cache:
            cache[key] = predictions(path(model, checkpoint, dataset))
        expected = {str(row["sample_id"]) for row in rows[dataset]}
        if not expected <= set(cache[key]):
            raise RuntimeError(f"unmatched prediction IDs: {model}/{checkpoint}/{dataset}")
        return cache[key]

    metric_rows = []
    packed = {}
    for model, cps in (
        ("A0", (None,)),
        ("A2", (None,)),
        ("A3", CHECKPOINTS),
        ("A4", CHECKPOINTS),
        ("A5", CHECKPOINTS),
    ):
        for checkpoint in cps:
            for dataset, subset in rows.items():
                c = counts(subset, get(model, checkpoint, dataset))
                packed[(model, checkpoint, dataset)] = c
                metric_rows.append(
                    {
                        "model": model,
                        "checkpoint": checkpoint or "base",
                        "dataset": dataset,
                        "samples": len(subset),
                        "normalized_wer": c[0].sum() / c[1].sum(),
                        "normalized_cer": c[2].sum() / c[3].sum(),
                    }
                )
    lookup = {(r["model"], r["checkpoint"], r["dataset"]): r for r in metric_rows}
    for r in metric_rows:
        for model, cp in (("A0", "base"), ("A2", "base"), ("A3", "step-050"), ("A4", "step-050")):
            ref = lookup[(model, cp, r["dataset"])]
            r[f"wer_delta_vs_{model}"] = r["normalized_wer"] - ref["normalized_wer"]
            r[f"cer_delta_vs_{model}"] = r["normalized_cer"] - ref["normalized_cer"]
    with (REPORTS / "a0_a2_a3_a4_a5_metrics_comparison.csv").open(
        "w", encoding="utf-8", newline=""
    ) as out:
        writer = csv.DictWriter(out, fieldnames=metric_rows[0].keys())
        writer.writeheader()
        writer.writerows(metric_rows)
    ci_rows = []
    for cp_i, cp in enumerate(CHECKPOINTS):
        for ds_i, dataset in enumerate(
            ("mediaspeech_clean", "mediaspeech_phone", "mediaspeech_g711", "cv_scripted", "fleurs")
        ):
            candidate = packed[("A5", cp, dataset)]
            for ref_i, (model, r_cp) in enumerate((("A0", None), ("A4", cp), ("A3", cp))):
                base = packed[(model, r_cp, dataset)]
                for index, name in ((0, "normalized_WER"), (2, "normalized_CER")):
                    value = ci(base, candidate, index, 20260810 + cp_i * 100 + ds_i * 10 + ref_i)
                    ci_rows.append(
                        {
                            "checkpoint": cp,
                            "dataset": dataset,
                            "reference": model,
                            "metric": name,
                            **value,
                            "classification": label(value, dataset),
                        }
                    )
    # Weighted robustness proxy: bootstrap the same stable MediaSpeech positions across variants.
    for cp_i, cp in enumerate(CHECKPOINTS):
        for ref_i, (model, r_cp) in enumerate((("A0", None), ("A4", cp), ("A3", cp))):
            rng = np.random.default_rng(20260910 + cp_i * 10 + ref_i)
            draws = rng.integers(0, 493, size=(200, 493))
            samples = []
            point = 0.0
            for ds, weight in (
                ("mediaspeech_clean", 0.5),
                ("mediaspeech_phone", 0.25),
                ("mediaspeech_g711", 0.25),
            ):
                base, candidate = packed[(model, r_cp, ds)], packed[("A5", cp, ds)]
                samples.append(
                    weight
                    * (
                        (candidate[0][draws].sum(axis=1) - base[0][draws].sum(axis=1))
                        / base[1][draws].sum(axis=1)
                    )
                )
                point += weight * ((candidate[0].sum() - base[0].sum()) / base[1].sum())
            value = {
                "point": float(point),
                "lower": float(np.quantile(sum(samples), 0.025)),
                "upper": float(np.quantile(sum(samples), 0.975)),
                "replicates": 200,
            }
            ci_rows.append(
                {
                    "checkpoint": cp,
                    "dataset": "robustness_proxy",
                    "reference": model,
                    "metric": "normalized_WER",
                    "proxy_definition": "0.5 clean + 0.25 phone + 0.25 g711",
                    "**": None,
                    **value,
                    "classification": label(value, "mediaspeech_phone"),
                }
            )
    (REPORTS / "a5_v2_paired_bootstrap_ci.json").write_text(
        json.dumps(ci_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    a5 = {cp: {ds: lookup[("A5", cp, ds)]["normalized_wer"] for ds in SETS} for cp in CHECKPOINTS}
    proxy = {
        cp: 0.5 * a5[cp]["mediaspeech_clean"]
        + 0.25 * a5[cp]["mediaspeech_phone"]
        + 0.25 * a5[cp]["mediaspeech_g711"]
        for cp in CHECKPOINTS
    }
    best = {ds: min(CHECKPOINTS, key=lambda cp: a5[cp][ds]) for ds in SETS}
    best["robustness_proxy"] = min(proxy, key=proxy.get)
    general = {
        cp: (a5[cp]["cv_scripted"] - lookup[("A0", "base", "cv_scripted")]["normalized_wer"])
        + (a5[cp]["fleurs"] - lookup[("A0", "base", "fleurs")]["normalized_wer"])
        for cp in CHECKPOINTS
    }
    best["lowest_general_regression"] = min(general, key=general.get)
    table = [
        "# A5_v2 checkpoint trajectory",
        "",
        "| checkpoint | clean | phone | G.711 | proxy | CV Scripted | FLEURS |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for cp in CHECKPOINTS:
        table.append(
            f"| {cp} | {f(a5[cp]['mediaspeech_clean'])} | {f(a5[cp]['mediaspeech_phone'])} | {f(a5[cp]['mediaspeech_g711'])} | {f(proxy[cp])} | {f(a5[cp]['cv_scripted'])} | {f(a5[cp]['fleurs'])} |"
        )
    table += ["", *[f"- Best {name}: `{cp}`." for name, cp in best.items()]]
    (REPORTS / "a5_v2_checkpoint_trajectory.md").write_text(
        "\n".join(table) + "\n", encoding="utf-8"
    )
    ci_table = [
        "# A5_v2 statistical analysis",
        "",
        "Delta is A5 minus reference. Paired stable sample IDs, 200 deterministic bootstrap replicates; negative favors A5.",
        "",
        "| checkpoint | dataset | ref | metric | delta | 95% CI | classification |",
        "| --- | --- | --- | --- | ---: | --- | --- |",
    ]
    for r in ci_rows:
        ci_table.append(
            f"| {r['checkpoint']} | {r['dataset']} | {r['reference']} | {r['metric']} | {f(r['point'])} | [{f(r['lower'])}, {f(r['upper'])}] | {r['classification']} |"
        )
    (REPORTS / "a5_v2_statistical_analysis.md").write_text(
        "\n".join(ci_table) + "\n", encoding="utf-8"
    )
    comparative = f"""# A5_v2 comparative analysis

A5 is diagnostic-only. Best Phone checkpoint: `{best['mediaspeech_phone']}`; best robustness proxy: `{best['robustness_proxy']}`; lowest combined A0-relative CV Scripted/FLEURS regression: `{best['lowest_general_regression']}`. The full WER/CER deltas are in `a0_a2_a3_a4_a5_metrics_comparison.csv`.

Production-relevant open-data indicators are MediaSpeech Phone, G.711 and the proxy. CV Scripted/FLEURS are scientific monitoring, not automatic production-rejection gates. Agent/customer, banking terminology, number/name correctness, real call noise/crosstalk and critical operational error rates are `MISSING` without company data.
"""
    (REPORTS / "a5_v2_comparative_analysis.md").write_text(comparative, encoding="utf-8")
    matched = """# A3/A4/A5 matched-ablation analysis

## A5 vs A4 — matched layer-scope contrast

A5 and A4 are fresh-base, zero-replay, same seed, 3,200 acoustic microbatches, optimizer, validation and frozen suite. Their checkpoint-matched deltas in the comparison CSV are the strongest available encoder-only versus decoder-only evidence. Phone, G.711, Clean, CV Scripted and FLEURS conclusions must use their paired-CI labels rather than point estimates alone.

## A5 vs A3 — replay contrast

Both are encoder-only Q/V, but A3 uses 10% clean replay and has a different locked population/schedule. Therefore any replay attribution is a **hypothesis**, not a fully controlled causal estimate. A5 directly answers the previously missing zero-replay encoder-only ablation; it does not by itself establish the counterfactual effect of replay.

## A2 relationship

A2 encoder+decoder comparisons remain partly hypothesis-level because its data/schedule differ. Its FLEURS behaviour cannot be assigned uniquely to the decoder or to an encoder-decoder interaction. Additivity is not established by these runs.
"""
    (REPORTS / "a3_a4_a5_matched_ablation_analysis.md").write_text(matched, encoding="utf-8")
    decision = """# A6 decision gate

`A6_ENCODER_DECODER_COMBINATION_EXPERIMENT_RECOMMENDED`

A5 resolves the missing matched zero-replay encoder-only comparator against A4. The principal remaining open-data question is whether a selective encoder+decoder scope yields a better target/general trade-off than either single-side adaptation. The pre-existing A6 idea is not materialized or started here. Its information gain is limited by the lack of a company-domain test set; another open-data ablation remains scientifically useful only as a diagnostic comparison, never as production evidence.
"""
    (REPORTS / "a6_decision_gate.md").write_text(decision, encoding="utf-8")
    (REPORTS / "next_executable_stage.md").write_text(
        "# Next executable stage\n\n`A5_V2_FROZEN_EVALUATION_COMPLETED`\n\nA6 decision is prepared but A6 contract/training is not authorized by this completion.\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {"status": "A5_V2_FROZEN_EVALUATION_COMPLETED", "best": best, "proxy": proxy},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
