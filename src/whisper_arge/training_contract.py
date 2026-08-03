from __future__ import annotations

import json
import importlib.metadata
import random
from collections import Counter, defaultdict
from pathlib import Path

from .hashing import sha256_bytes, sha256_file
from .manifests import read_jsonl
from .normalization import normalize_turkish


SOURCES = {
    "tsc": ("data/materialized/tsc_v2a/tsc_train_v2a.jsonl", "CC-BY-4.0", "official_train"),
    "mediaspeech": (
        "data/materialized/mediaspeech_v2d/mediaspeech_train_v2d.jsonl",
        "CC-BY-4.0",
        "deterministic_train",
    ),
    "cv_spontaneous": (
        "data/materialized/cv_spontaneous_v2c/cv_spontaneous_train_v2c.jsonl",
        "CC0-1.0",
        "speaker_disjoint_train",
    ),
}
EVALUATION_MANIFESTS = [
    "data/materialized/mediaspeech_v2d/paired/mediaspeech_holdout_paired_v2d.jsonl",
    "data/materialized/hf_v2d/cv_scripted_test_v2d.jsonl",
    "data/materialized/fleurs_tr_v2d/fleurs_tr_test_v2d.jsonl",
    "data/materialized/cv_spontaneous_v2c/cv_spontaneous_holdout_v2c.jsonl",
    "data/materialized/tsc_v2a/tsc_full_v2a.jsonl",
]
SAMPLING = {"tsc": 0.6316, "mediaspeech": 0.3158, "cv_spontaneous": 0.0526}


def _load_sources() -> tuple[list[dict], dict[str, list[dict]]]:
    rows, grouped = [], defaultdict(list)
    for corpus, (path, license_name, source_split) in SOURCES.items():
        for item in read_jsonl(path):
            row = {
                "stable_id": f"{corpus}:{item['stable_source_id']}",
                "corpus": corpus,
                "audio_path": item["audio"],
                "transcript": item["reference"],
                "duration": float(item["duration_seconds"]),
                "audio_sha256": item["audio_sha256"],
                "transcript_sha256": sha256_bytes(str(item["reference"]).encode("utf-8")),
                "source_split": source_split,
                "license": license_name,
                "training_eligible": True,
                "source_sample_id": item["sample_id"],
                "source_stable_id": item["stable_source_id"],
            }
            rows.append(row)
            grouped[corpus].append(row)
    return rows, grouped


def _leakage(rows: list[dict]) -> dict:
    eval_rows = [row for path in EVALUATION_MANIFESTS for row in read_jsonl(path)]
    training_stable = {(str(row["corpus"]), str(row["source_stable_id"])) for row in rows}
    training_audio = {str(row["audio_sha256"]) for row in rows}
    corpus_for_dataset = {
        "issai/Turkish_Speech_Corpus": "tsc",
        "openslr/SLR108/MediaSpeech/TR": "mediaspeech",
        "mozilla/common_voice_spontaneous_tr": "cv_spontaneous",
    }
    evaluation_stable = {
        (
            corpus_for_dataset.get(str(row.get("dataset_id")), str(row.get("dataset_id"))),
            str(row.get("stable_source_id") or ""),
        )
        for row in eval_rows
    }
    evaluation_audio = {str(row.get("audio_sha256") or "") for row in eval_rows}
    stable_overlap = sorted(training_stable & evaluation_stable)
    audio_overlap = sorted(training_audio & evaluation_audio)
    cv_holdout = [row for row in eval_rows if row.get("domain") == "cv_spontaneous_holdout"]
    cv_speakers = {str(row.get("speaker_id")) for row in cv_holdout}
    source_cv_rows = list(read_jsonl(SOURCES["cv_spontaneous"][0]))
    cv_train_speakers = {str(row.get("speaker_id")) for row in source_cv_rows}
    media_train = {str(row["source_stable_id"]) for row in rows if row["corpus"] == "mediaspeech"}
    media_holdout = {
        str(row.get("stable_source_id"))
        for row in eval_rows
        if str(row.get("domain", "")).startswith("mediaspeech_holdout")
    }
    tsc_train = {str(row["source_stable_id"]) for row in rows if row["corpus"] == "tsc"}
    tsc_test = {
        str(row.get("stable_source_id"))
        for row in eval_rows
        if row.get("domain") == "tsc_official_test_exploratory"
    }
    normalized = Counter(normalize_turkish(str(row["transcript"])) for row in rows)
    return {
        "hard_fail": bool(
            stable_overlap
            or audio_overlap
            or (cv_train_speakers & cv_speakers)
            or (media_train & media_holdout)
            or (tsc_train & tsc_test)
        ),
        "stable_id_overlap": [
            {"corpus": value[0], "stable_id": value[1]} for value in stable_overlap
        ],
        "audio_sha256_overlap": audio_overlap,
        "cv_spontaneous_holdout_speaker_overlap": sorted(cv_train_speakers & cv_speakers),
        "mediaspeech_train_holdout_stable_overlap": sorted(media_train & media_holdout),
        "tsc_train_test_stable_overlap": sorted(tsc_train & tsc_test),
        "normalized_transcript_duplicate_groups": sum(
            1 for value in normalized.values() if value > 1
        ),
        "normalized_transcript_duplicate_rows": sum(
            value for value in normalized.values() if value > 1
        ),
        "normalized_transcript_policy": "reported_only; no row removed solely for transcript match",
    }


def create_training_contract(
    output_root: str | Path, *, seed: int = 20260730, steps: int = 200
) -> dict:
    root = Path(output_root)
    rows, grouped = _load_sources()
    leakage = _leakage(rows)
    if leakage["hard_fail"]:
        raise ValueError(
            "training leakage audit hard fail: " + json.dumps(leakage, ensure_ascii=False)
        )
    manifest = root / "target_train_v2d.jsonl"
    root.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    rng = random.Random(seed)
    corpus_names = list(SAMPLING)
    weights = [SAMPLING[name] for name in corpus_names]
    microbatches = steps * 16
    schedule = []
    for microstep in range(microbatches):
        corpus = rng.choices(corpus_names, weights=weights, k=1)[0]
        row = grouped[corpus][rng.randrange(len(grouped[corpus]))]
        schedule.append(
            {
                "microstep": microstep,
                "stable_id": row["stable_id"],
                "corpus": corpus,
                "augmentation": "none",
            }
        )
    schedule_path = root / "sample_schedule_v2d_200.jsonl"
    schedule_path.write_text(
        "".join(json.dumps(item, sort_keys=True) + "\n" for item in schedule), encoding="utf-8"
    )
    source_hashes = {corpus: sha256_file(path) for corpus, (path, _, _) in SOURCES.items()}
    contract = {
        "schema_version": 1,
        "immutable": True,
        "seed": seed,
        "model": "openai/whisper-large-v3-turbo",
        "model_revision": "41f01f3fe87f28c78e2fbf8b568835947dd65ed9",
        "tokenizer_processor_revision": "41f01f3fe87f28c78e2fbf8b568835947dd65ed9",
        "target_manifest": str(manifest),
        "target_manifest_sha256": sha256_file(manifest),
        "source_manifest_sha256": source_hashes,
        "schedule": {
            "path": str(schedule_path),
            "sha256": sha256_file(schedule_path),
            "steps": steps,
            "microbatches": microbatches,
            "prefix_rule": "any 750-step schedule must use this exact 200-step prefix",
        },
        "sampling": {
            "strategy": "prelocked_target_ratios",
            "probabilities": SAMPLING,
            "sampler_seed": seed,
        },
        "optimizer": {
            "name": "AdamW",
            "learning_rate": 0.00001,
            "betas": [0.9, 0.999],
            "weight_decay": 0.01,
        },
        "scheduler": {"name": "linear", "warmup_steps": 20},
        "effective_batch_size": 16,
        "per_device_batch_size": 1,
        "gradient_accumulation_steps": 16,
        "precision": "fp16",
        "gradient_checkpointing": True,
        "augmentation": {"kind": "none", "probability": 0.0},
        "random_seeds": {"python": seed, "numpy": seed, "torch": seed},
        "environment": {
            "torch": importlib.metadata.version("torch"),
            "transformers": importlib.metadata.version("transformers"),
            "peft": importlib.metadata.version("peft"),
            "accelerate": importlib.metadata.version("accelerate"),
        },
    }
    contract_path = root / "training_contract_v2d.json"
    contract_path.write_text(
        json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    report = {
        "rows": len(rows),
        "hours_by_corpus": {
            name: sum(row["duration"] for row in items) / 3600 for name, items in grouped.items()
        },
        "rows_by_corpus": {name: len(items) for name, items in grouped.items()},
        "sampling_probabilities": SAMPLING,
        "leakage_audit": leakage,
        "manifest_sha256": sha256_file(manifest),
        "schedule_sha256": sha256_file(schedule_path),
    }
    report_path = root / "training_report_v2d.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lock = {
        "schema_version": 1,
        "lock_status": "finalized",
        "files": {
            str(manifest.relative_to(root.parent)).replace("\\", "/"): sha256_file(manifest),
            str(schedule_path.relative_to(root.parent)).replace("\\", "/"): sha256_file(schedule_path),
            str(contract_path.relative_to(root.parent)).replace("\\", "/"): sha256_file(contract_path),
            str(report_path.relative_to(root.parent)).replace("\\", "/"): sha256_file(report_path),
        },
        "model": contract["model"],
        "model_revision": contract["model_revision"],
        "tokenizer_processor_revision": contract["tokenizer_processor_revision"],
        "optimizer": contract["optimizer"],
        "scheduler": contract["scheduler"],
        "effective_batch_size": contract["effective_batch_size"],
        "gradient_accumulation_steps": contract["gradient_accumulation_steps"],
        "precision": contract["precision"],
        "gradient_checkpointing": contract["gradient_checkpointing"],
        "augmentation": contract["augmentation"],
        "random_seeds": contract["random_seeds"],
        "environment": {"python": __import__("sys").version.split()[0], **contract["environment"]},
    }
    lock_path = root / "TRAINING_LOCK_v2d.json"
    lock_path.write_text(
        json.dumps(lock, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {
        "contract": str(contract_path),
        "report": str(report_path),
        "lock": str(lock_path),
        "rows": len(rows),
        "manifest_sha256": sha256_file(manifest),
        "schedule_sha256": sha256_file(schedule_path),
    }
