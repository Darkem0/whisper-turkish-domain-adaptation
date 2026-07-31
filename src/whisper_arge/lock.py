from __future__ import annotations

import json
from pathlib import Path

from .hashing import sha256_file


def verify_lock(lock_path: str | Path) -> list[str]:
    lock_path = Path(lock_path)
    payload = json.loads(lock_path.read_text(encoding="utf-8"))
    root = lock_path.parent.parent
    errors: list[str] = []
    for relative_path, expected in payload["files"].items():
        path = root / relative_path
        if not path.exists():
            errors.append(f"missing: {relative_path}")
            continue
        actual = sha256_file(path)
        if actual != expected:
            errors.append(f"hash mismatch: {relative_path}: expected {expected}, got {actual}")
    return errors

