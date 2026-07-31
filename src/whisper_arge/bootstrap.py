from __future__ import annotations

import random
from collections.abc import Callable, Iterable


def percentile(values: list[float], probability: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = (len(ordered) - 1) * probability
    lower, upper = int(index), min(int(index) + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def bootstrap_ci(
    rows: Iterable[dict], metric: Callable[[list[dict]], float], *, block_key: str | None,
    replicates: int = 2000, seed: int = 20260730,
) -> dict[str, float | int | str | None]:
    """Percentile CI using source/speaker blocks when an available key is supplied."""
    items = list(rows)
    if not items:
        return {"point": 0.0, "lower": 0.0, "upper": 0.0, "replicates": replicates, "block_key": block_key}
    groups: dict[str, list[dict]] = {}
    for index, row in enumerate(items):
        key = str(row.get(block_key, index)) if block_key else str(index)
        groups.setdefault(key, []).append(row)
    blocks = list(groups.values())
    rng = random.Random(seed)
    samples = [metric([row for block in (rng.choice(blocks) for _ in blocks) for row in block]) for _ in range(replicates)]
    return {"point": metric(items), "lower": percentile(samples, 0.025), "upper": percentile(samples, 0.975), "replicates": replicates, "block_key": block_key}
