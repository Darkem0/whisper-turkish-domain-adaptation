from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

REQUIRED_FIELDS = {
    "sample_id",
    "domain",
    "audio",
    "audio_sha256",
    "reference",
    "dataset_id",
    "dataset_revision",
    "split",
}


def read_jsonl(path: str | Path) -> Iterator[dict]:
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON") from exc


def validate_manifest(path: str | Path) -> dict[str, int | list[str]]:
    seen: set[str] = set()
    domains: set[str] = set()
    rows = 0
    for line_number, row in enumerate(read_jsonl(path), start=1):
        missing = REQUIRED_FIELDS - row.keys()
        if missing:
            raise ValueError(f"{path}:{line_number}: missing {sorted(missing)}")
        sample_id = str(row["sample_id"])
        if sample_id in seen:
            raise ValueError(f"{path}:{line_number}: duplicate sample_id {sample_id}")
        if len(str(row["audio_sha256"])) != 64:
            raise ValueError(f"{path}:{line_number}: audio_sha256 must be 64 hex characters")
        if not str(row["dataset_revision"]).strip():
            raise ValueError(f"{path}:{line_number}: dataset_revision must be pinned")
        seen.add(sample_id)
        domains.add(str(row["domain"]))
        rows += 1
    if not rows:
        raise ValueError(f"{path}: empty manifest")
    return {"rows": rows, "domains": sorted(domains)}

