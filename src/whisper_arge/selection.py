from __future__ import annotations

import hashlib
from typing import Iterable


def stable_selection_key(
    dataset_id: str,
    dataset_revision: str,
    split: str,
    stable_source_id: str,
    seed: int,
) -> str:
    value = "\0".join(
        (dataset_id, dataset_revision, split, stable_source_id, str(seed))
    ).encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def select_rows(rows: Iterable[dict], limit: int, seed: int) -> list[dict]:
    rows = list(rows)
    for row in rows:
        required = {"dataset_id", "dataset_revision", "split", "stable_source_id"}
        missing = required - row.keys()
        if missing:
            raise ValueError(f"selection row missing {sorted(missing)}")
    ranked = sorted(
        rows,
        key=lambda row: stable_selection_key(
            str(row["dataset_id"]),
            str(row["dataset_revision"]),
            str(row["split"]),
            str(row["stable_source_id"]),
            seed,
        ),
    )
    if limit < 1:
        raise ValueError("limit must be positive")
    return ranked[:limit]

