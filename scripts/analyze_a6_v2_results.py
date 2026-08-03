"""Read-only explicit-path A5 versus A6 frozen-prediction analysis."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from rapidfuzz.distance import Levenshtein

from whisper_arge.normalization import normalize_turkish


ROOT = Path(__file__).resolve().parents[1]
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
PREDICTION_ROOTS = {
    "A5": ROOT / "runs" / "A5_v2_frozen_evaluation",
    "A6": ROOT / "runs" / "A6_v2_frozen_evaluation",
}


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def prediction_path(experiment: str, checkpoint: str, dataset: str) -> Path:
    return PREDICTION_ROOTS[experiment] / checkpoint / dataset / "predictions.jsonl"


def source_rows(config: dict, dataset: str) -> list[dict]:
    source = Path(config["source_manifest"])
    values = rows(source)
    degradation = {
        "mediaspeech_clean": "clean",
        "mediaspeech_phone": "phone_8khz",
        "mediaspeech_g711": "g711_mulaw",
    }.get(dataset)
    return [row for row in values if degradation is None or row["degradation"] == degradation]


def counts(reference_rows: list[dict], predictions: dict[str, str]) -> tuple[np.ndarray, ...]:
    values = [[], [], [], []]
    for row in reference_rows:
        reference = normalize_turkish(str(row["reference"]))
        prediction = normalize_turkish(predictions[str(row["sample_id"])])
        values[0].append(Levenshtein.distance(reference.split(), prediction.split()))
        values[1].append(len(reference.split()))
        values[2].append(Levenshtein.distance(reference.replace(" ", ""), prediction.replace(" ", "")))
        values[3].append(len(reference.replace(" ", "")))
    return tuple(np.asarray(value, dtype=np.int64) for value in values)


def paired_ci(base: tuple[np.ndarray, ...], candidate: tuple[np.ndarray, ...], metric: int, seed: int) -> dict:
    errors, denominator = metric, metric + 1
    rng = np.random.default_rng(seed)
    draw = rng.integers(0, len(base[denominator]), size=(200, len(base[denominator])))
    values = (candidate[errors][draw].sum(axis=1) - base[errors][draw].sum(axis=1)) / base[denominator][draw].sum(axis=1)
    return {
        "point": float((candidate[errors].sum() - base[errors].sum()) / base[denominator].sum()),
        "lower": float(np.quantile(values, 0.025)),
        "upper": float(np.quantile(values, 0.975)),
        "replicates": 200,
    }


def classification(value: dict) -> str:
    if value["upper"] < 0:
        return "statistically_supported_a6_gain"
    if value["lower"] > 0:
        return "statistically_supported_a6_regression"
    return "inconclusive"


def main() -> None:
    packed: dict[tuple[str, str, str], tuple[np.ndarray, ...]] = {}
    metrics_rows, parity_rows, ci_rows = [], [], []
    for checkpoint_index, checkpoint in enumerate(CHECKPOINTS):
        for dataset_index, dataset in enumerate(DATASETS):
            target: dict[str, tuple[list[dict], dict[str, str], dict, str]] = {}
            for experiment in ("A5", "A6"):
                path = prediction_path(experiment, checkpoint, dataset)
                config = read_json(path.parent / "config.resolved.json")
                prediction_rows = rows(path)
                predictions = {str(row["sample_id"]): str(row["prediction"]) for row in prediction_rows}
                references = source_rows(config, dataset)
                if set(predictions) != {str(row["sample_id"]) for row in references}:
                    raise RuntimeError(f"sample-id mismatch: {experiment}/{checkpoint}/{dataset}")
                metrics = read_json(path.parent / "metrics.json")
                packed[(experiment, checkpoint, dataset)] = counts(references, predictions)
                target[experiment] = (references, predictions, metrics, hashlib.sha256(path.read_bytes()).hexdigest())
                metrics_rows.append({
                    "model": experiment,
                    "checkpoint": checkpoint,
                    "dataset": dataset,
                    "samples": len(references),
                    "normalized_wer": metrics["normalized_wer"],
                    "normalized_cer": metrics["normalized_cer"],
                    "prediction_sha256": target[experiment][3],
                })
            parity_rows.append({
                "checkpoint": checkpoint,
                "dataset": dataset,
                "sample_id_parity": True,
                "different_predictions": sum(target["A5"][1][key] != target["A6"][1][key] for key in target["A5"][1]),
                "a5_prediction_sha256": target["A5"][3],
                "a6_prediction_sha256": target["A6"][3],
            })
            if dataset in DATASETS[:5]:
                for metric, name in ((0, "normalized_WER"), (2, "normalized_CER")):
                    value = paired_ci(packed[("A5", checkpoint, dataset)], packed[("A6", checkpoint, dataset)], metric, 20260820 + checkpoint_index * 100 + dataset_index * 10 + metric)
                    ci_rows.append({"checkpoint": checkpoint, "dataset": dataset, "reference": "A5", "candidate": "A6", "metric": name, **value, "classification": classification(value)})
    for checkpoint_index, checkpoint in enumerate(CHECKPOINTS):
        rng = np.random.default_rng(20260920 + checkpoint_index)
        draws = rng.integers(0, 493, size=(200, 493))
        samples, point = [], 0.0
        for dataset, weight in (("mediaspeech_clean", 0.5), ("mediaspeech_phone", 0.25), ("mediaspeech_g711", 0.25)):
            base, candidate = packed[("A5", checkpoint, dataset)], packed[("A6", checkpoint, dataset)]
            samples.append(weight * (candidate[0][draws].sum(axis=1) - base[0][draws].sum(axis=1)) / base[1][draws].sum(axis=1))
            point += weight * (candidate[0].sum() - base[0].sum()) / base[1].sum()
        value = {"point": float(point), "lower": float(np.quantile(sum(samples), 0.025)), "upper": float(np.quantile(sum(samples), 0.975)), "replicates": 200}
        ci_rows.append({"checkpoint": checkpoint, "dataset": "robustness_proxy", "reference": "A5", "candidate": "A6", "metric": "normalized_WER", "proxy_definition": "0.5 clean + 0.25 phone + 0.25 g711", **value, "classification": classification(value)})
    REPORTS.mkdir(exist_ok=True)
    with (REPORTS / "a0_a2_a3_a4_a5_a6_metrics_comparison.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=metrics_rows[0].keys())
        writer.writeheader()
        writer.writerows(metrics_rows)
    (REPORTS / "a5_a6_prediction_parity.json").write_text(json.dumps(parity_rows, indent=2) + "\n", encoding="utf-8")
    (REPORTS / "a6_v2_paired_bootstrap_ci.json").write_text(json.dumps(ci_rows, indent=2) + "\n", encoding="utf-8")
    trajectory = ["# A6_v2 corrected checkpoint trajectory", "", "| checkpoint | clean | phone | G.711 | proxy |", "| --- | ---: | ---: | ---: | ---: |"]
    for checkpoint in CHECKPOINTS:
        values = {row["dataset"]: row["normalized_wer"] for row in metrics_rows if row["model"] == "A6" and row["checkpoint"] == checkpoint}
        proxy = 0.5 * values["mediaspeech_clean"] + 0.25 * values["mediaspeech_phone"] + 0.25 * values["mediaspeech_g711"]
        trajectory.append(f"| {checkpoint} | {values['mediaspeech_clean']:.4f} | {values['mediaspeech_phone']:.4f} | {values['mediaspeech_g711']:.4f} | {proxy:.4f} |")
    (REPORTS / "a6_v2_checkpoint_trajectory.md").write_text("\n".join(trajectory) + "\n", encoding="utf-8")
    table = ["# A6_v2 corrected statistical analysis", "", "Delta is A6 minus A5; negative favours A6. Derived only from explicit, distinct locked prediction roots.", "", "| checkpoint | dataset | metric | delta | 95% CI | classification |", "| --- | --- | --- | ---: | --- | --- |"]
    for row in ci_rows:
        table.append(f"| {row['checkpoint']} | {row['dataset']} | {row['metric']} | {row['point']:.4f} | [{row['lower']:.4f}, {row['upper']:.4f}] | {row['classification']} |")
    (REPORTS / "a6_v2_statistical_analysis.md").write_text("\n".join(table) + "\n", encoding="utf-8")
    totals = sum(row["different_predictions"] for row in parity_rows)
    (REPORTS / "a6_v2_comparative_analysis.md").write_text(f"# A6_v2 corrected comparative analysis\n\nA5 and A6 are not prediction-identical: {totals} raw predictions differ across 28 matched targets. The prior all-zero comparison is superseded due to a reference-path bug. Corrected target metrics, CIs and trajectory are in the companion reports; this remains diagnostic-only and is not a production decision.\n", encoding="utf-8")
    (REPORTS / "a4_a5_a6_matched_ablation_analysis.md").write_text("# A4/A5/A6 matched-ablation analysis\n\n`SUPERSEDED_DUE_TO_REFERENCE_PATH_BUG`: the former A5--A6 all-zero conclusion used the A6 root for both sides. See `a6_v2_statistical_analysis.md` and `a5_a6_prediction_parity.json` for the corrected explicit-root analysis. A4 comparisons are not regenerated by this script.\n", encoding="utf-8")
    print(json.dumps({"status": "PASSED", "targets": len(parity_rows), "different_predictions": totals, "ci_rows": len(ci_rows)}))


if __name__ == "__main__":
    main()
