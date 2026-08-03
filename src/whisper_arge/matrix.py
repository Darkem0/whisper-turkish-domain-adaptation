from __future__ import annotations

from pathlib import Path

from .manifests import read_jsonl


def validate_matrix(path: str | Path) -> dict[str, int]:
    rows = list(read_jsonl(path))
    ids = {str(row["id"]) for row in rows}
    if len(ids) != len(rows):
        raise ValueError("matrix contains duplicate ids")
    stages: dict[str, int] = {}
    for row in rows:
        required = {
            "id",
            "parent",
            "stage",
            "budget_steps",
            "hypothesis",
            "change",
            "promotion_rule",
        }
        missing = required - row.keys()
        if missing:
            raise ValueError(f"{row.get('id', '<unknown>')}: missing {sorted(missing)}")
        parent = str(row["parent"])
        if parent != "ROOT" and parent not in ids:
            raise ValueError(f"{row['id']}: unknown parent {parent}")
        change = row["change"]
        if set(change) != {"path", "from", "to"} or change["from"] == change["to"]:
            raise ValueError(f"{row['id']}: change must contain one differing path/from/to")
        if int(row["budget_steps"]) not in {200, 750, 1000}:
            raise ValueError(f"{row['id']}: unsupported initial matrix budget")
        stage = str(row["stage"])
        stages[stage] = stages.get(stage, 0) + 1
    return {"experiments": len(rows), **dict(sorted(stages.items()))}
