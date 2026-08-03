from __future__ import annotations

import json
from pathlib import Path

from .hashing import hash_json
from .manifests import read_jsonl


SIGNATURE_FIELDS = (
    "model",
    "model_revision",
    "dataset_manifest_sha256",
    "evaluation_lock_sha256",
    "seed",
    "training",
)


def experiment_signature(config: dict) -> str:
    missing = [field for field in SIGNATURE_FIELDS if field not in config]
    if missing:
        raise ValueError(f"signature fields missing: {missing}")
    return hash_json({field: config[field] for field in SIGNATURE_FIELDS})


def assert_not_run(config: dict, ledger_path: str | Path) -> str:
    signature = experiment_signature(config)
    if Path(ledger_path).exists():
        for event in read_jsonl(ledger_path):
            if event.get("signature") == signature and event.get("event") in {
                "reserved",
                "completed",
                "accepted",
                "rejected",
            }:
                raise ValueError(
                    f"duplicate experiment signature {signature}; prior id={event.get('experiment_id')}"
                )
    return signature


def append_event(ledger_path: str | Path, event: dict) -> None:
    path = Path(ledger_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def summarize(ledger_path: str | Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in read_jsonl(ledger_path):
        key = str(event.get("status", event.get("event", "unknown")))
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))

