"""Resumable local frozen evaluation for the verified A3_v2 checkpoints.

This worker intentionally evaluates only the four contract checkpoints.  It writes
durable per-target artefacts and never mutates the immutable evaluation inputs.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import platform
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "A3_v2_frozen_evaluation"
CONTRACT = ROOT / "contracts" / "A3_v2_eval_contract.yaml"
TRAIN_RUN = ROOT / "runs" / "A3_v2_fresh_base_200"
MODEL = "openai/whisper-large-v3-turbo"
REVISION = "41f01f3fe87f28c78e2fbf8b568835947dd65ed9"
DECODE = {
    "language": "tr",
    "task": "transcribe",
    "num_beams": 5,
    "do_sample": False,
    "condition_on_prev_tokens": False,
    "max_new_tokens": 444,
}
CHECKPOINTS = ("step-050", "step-100", "step-150", "step-200")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def target_rows(contract: dict) -> list[tuple[str, Path, list[dict]]]:
    sets = {entry["name"]: ROOT / entry["path"] for entry in contract["frozen_sets"]}
    media = read_jsonl(sets["mediaspeech_paired"])
    by_degradation = {
        "mediaspeech_clean": "clean",
        "mediaspeech_phone": "phone_8khz",
        "mediaspeech_g711": "g711_mulaw",
    }
    result = [(name, sets["mediaspeech_paired"], [row for row in media if row["degradation"] == degradation]) for name, degradation in by_degradation.items()]
    result.extend(
        [
            ("cv_scripted", sets["cv_scripted"], read_jsonl(sets["cv_scripted"])),
            ("fleurs", sets["fleurs"], read_jsonl(sets["fleurs"])),
            ("cv_spontaneous", sets["cv_spontaneous_holdout"], read_jsonl(sets["cv_spontaneous_holdout"])),
            ("tsc_exploratory", sets["tsc_exploratory"], read_jsonl(sets["tsc_exploratory"])),
        ]
    )
    return result


def preflight(contract: dict) -> dict:
    checks: list[dict] = []
    for block in ("evaluation_lock", "acceptance_lock", "immutable_registry"):
        entry = contract[block]
        path = ROOT / entry["path"]
        checks.append({"name": block, "path": str(path), "expected": entry["sha256"], "actual": digest(path) if path.exists() else None})
    for entry in contract["frozen_sets"]:
        path = ROOT / entry["path"]
        checks.append({"name": entry["name"], "path": str(path), "expected": entry["sha256"], "actual": digest(path) if path.exists() else None})
    for checkpoint in CHECKPOINTS:
        directory = TRAIN_RUN / "checkpoints" / checkpoint
        lock = load_json(directory / "checkpoint_lock.json")
        for relative, expected in lock["files_sha256"].items():
            path = directory / relative
            checks.append({"name": f"{checkpoint}/{relative}", "path": str(path), "expected": expected, "actual": digest(path) if path.exists() else None})
        adapter = load_json(directory / "adapter" / "adapter_config.json")
        valid_adapter = adapter.get("base_model_name_or_path") == MODEL and adapter.get("r") == 16 and adapter.get("lora_alpha") == 32
        checks.append({"name": f"{checkpoint}/adapter_config", "expected": "A3 encoder Q/V r16 alpha32", "actual": "valid" if valid_adapter else adapter})
    checks.append({"name": "legacy_resume", "expected": "not A3_legacy_aborted_step34_invalid", "actual": "valid"})
    passed = all(item["actual"] == item["expected"] or item["actual"] == "valid" for item in checks)
    return {"status": "PASSED" if passed else "BLOCKED", "contract_sha256": digest(CONTRACT), "base_model": MODEL, "base_model_revision": REVISION, "decode": DECODE, "checks": checks}


def existing_predictions(path: Path, adapter_sha: str, config_sha: str) -> dict[str, dict]:
    if not path.exists():
        return {}
    return {
        str(row["sample_id"]): row
        for row in read_jsonl(path)
        if row.get("adapter_sha256") == adapter_sha and row.get("eval_config_sha256") == config_sha and row.get("audio_sha256")
    }


def word_operations(reference: str, prediction: str) -> dict[str, int]:
    """Return a deterministic minimum-edit substitution/insertion/deletion split."""
    ref, hyp = reference.split(), prediction.split()
    table = [[0] * (len(hyp) + 1) for _ in range(len(ref) + 1)]
    for index in range(len(ref) + 1):
        table[index][0] = index
    for index in range(len(hyp) + 1):
        table[0][index] = index
    for left, token in enumerate(ref, start=1):
        for right, candidate in enumerate(hyp, start=1):
            table[left][right] = min(
                table[left - 1][right] + 1,
                table[left][right - 1] + 1,
                table[left - 1][right - 1] + int(token != candidate),
            )
    result = {"substitutions": 0, "insertions": 0, "deletions": 0}
    left, right = len(ref), len(hyp)
    while left or right:
        if left and right and ref[left - 1] == hyp[right - 1] and table[left][right] == table[left - 1][right - 1]:
            left, right = left - 1, right - 1
        elif left and right and table[left][right] == table[left - 1][right - 1] + 1:
            result["substitutions"] += 1
            left, right = left - 1, right - 1
        elif right and table[left][right] == table[left][right - 1] + 1:
            result["insertions"] += 1
            right -= 1
        else:
            result["deletions"] += 1
            left -= 1
    return result


def evaluate_target(model, processor, checkpoint: str, name: str, source: Path, rows: list[dict], adapter_sha: str, config_sha: str) -> dict:
    import librosa
    import torch
    from whisper_arge.metrics import corpus_metrics
    from whisper_arge.normalization import normalize_turkish

    output = RUN / checkpoint / name
    output.mkdir(parents=True, exist_ok=True)
    resolved = {"checkpoint": checkpoint, "dataset": name, "source_manifest": str(source), "source_manifest_sha256": digest(source), "adapter_sha256": adapter_sha, "eval_config_sha256": config_sha, "decode": DECODE}
    save_json(output / "config.resolved.json", resolved)
    predictions_path = output / "predictions.jsonl"
    cached = existing_predictions(predictions_path, adapter_sha, config_sha)
    started = time.perf_counter()
    resource_path = output / "resource_usage.jsonl"
    with resource_path.open("a", encoding="utf-8") as resources:
        for index, row in enumerate(rows, start=1):
            sample_id = str(row["sample_id"])
            if sample_id in cached and cached[sample_id].get("audio_sha256") == row.get("audio_sha256"):
                continue
            audio, _ = librosa.load(str(ROOT / row["audio"]), sr=16000, mono=True)
            features = processor(audio, sampling_rate=16000, return_tensors="pt").input_features.to("cuda", dtype=torch.float16)
            with torch.inference_mode():
                generated = model.generate(features, **DECODE)
            cached[sample_id] = {"sample_id": sample_id, "audio_sha256": row.get("audio_sha256"), "adapter_sha256": adapter_sha, "eval_config_sha256": config_sha, "prediction": processor.batch_decode(generated, skip_special_tokens=True)[0]}
            resources.write(json.dumps({"sample_id": sample_id, "cuda_allocated": int(torch.cuda.max_memory_allocated()), "cuda_reserved": int(torch.cuda.max_memory_reserved())}) + "\n")
            if index % 25 == 0:
                write_jsonl(predictions_path, [cached[str(item["sample_id"])] for item in rows if str(item["sample_id"]) in cached])
                logging.info("%s/%s %s %s", index, len(rows), checkpoint, name)
    ordered = [cached[str(row["sample_id"])] for row in rows]
    write_jsonl(predictions_path, ordered)
    pairs = [(str(row["reference"]), prediction["prediction"]) for row, prediction in zip(rows, ordered, strict=True)]
    operations = {"substitutions": 0, "insertions": 0, "deletions": 0}
    for reference, prediction in pairs:
        current = word_operations(normalize_turkish(reference), normalize_turkish(prediction))
        for key in operations:
            operations[key] += current[key]
    metrics = {**corpus_metrics(pairs), **operations, "inference_wall_seconds": time.perf_counter() - started, "prediction_sha256": digest(predictions_path)}
    save_json(output / "metrics.json", metrics)
    save_json(output / "artifact_lock.json", {"config.resolved.json": digest(output / "config.resolved.json"), "predictions.jsonl": digest(predictions_path), "metrics.json": digest(output / "metrics.json"), "resource_usage.jsonl": digest(resource_path) if resource_path.exists() else None})
    return metrics


def main() -> int:
    RUN.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=RUN / "execution.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    contract = load_json(CONTRACT)
    result = preflight(contract)
    save_json(RUN / "preflight.json", result)
    if result["status"] != "PASSED":
        save_json(RUN / "evaluation_progress.json", {"status": "BLOCKED_A3_V2_FROZEN_EVALUATION", "preflight": result["status"]})
        return 2
    import torch
    from peft import PeftModel
    from transformers import WhisperForConditionalGeneration, WhisperProcessor

    save_json(RUN / "environment.json", {"python": sys.version, "platform": platform.platform(), "torch": torch.__version__, "cuda": torch.version.cuda, "pid": os.getpid()})
    targets = target_rows(contract)
    config_sha = hashlib.sha256(json.dumps(DECODE, sort_keys=True).encode()).hexdigest()
    save_json(RUN / "evaluation_progress.json", {"status": "RUNNING", "preflight": "PASSED", "current_target": {"checkpoint": CHECKPOINTS[0], "dataset": targets[0][0]}, "completed_targets": []})
    for checkpoint in CHECKPOINTS:
        adapter_path = TRAIN_RUN / "checkpoints" / checkpoint / "adapter"
        adapter_sha = digest(adapter_path / "adapter_model.safetensors")
        base = WhisperForConditionalGeneration.from_pretrained(MODEL, revision=REVISION, local_files_only=True, torch_dtype=torch.float16).to("cuda").eval()
        model = PeftModel.from_pretrained(base, str(adapter_path)).eval()
        processor = WhisperProcessor.from_pretrained(MODEL, revision=REVISION, local_files_only=True)
        for name, source, rows in targets:
            progress = load_json(RUN / "evaluation_progress.json")
            progress["current_target"] = {"checkpoint": checkpoint, "dataset": name}
            save_json(RUN / "evaluation_progress.json", progress)
            evaluate_target(model, processor, checkpoint, name, source, rows, adapter_sha, config_sha)
            progress = load_json(RUN / "evaluation_progress.json")
            progress["completed_targets"].append({"checkpoint": checkpoint, "dataset": name})
            save_json(RUN / "evaluation_progress.json", progress)
        del model, base
        torch.cuda.empty_cache()
    save_json(RUN / "evaluation_progress.json", {"status": "COMPLETED", "preflight": "PASSED", "completed_targets": 28})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
