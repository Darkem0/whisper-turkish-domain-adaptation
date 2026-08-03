"""Atomically finalize A5 frozen-evaluation external state after a passed audit."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"
RUN = ROOT / "runs/A5_v2_frozen_evaluation"


def save(path: Path, value: dict) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def main() -> None:
    old = STATE / "a5_v2_frozen_eval_state.json"
    attempt = RUN / "attempts/stale-external-state"
    attempt.mkdir(parents=True, exist_ok=True)
    if old.exists():
        (attempt / "state_before_completion_repair.json").write_bytes(old.read_bytes())
    completion = datetime.now(timezone.utc).isoformat()
    final = {"status": "COMPLETED", "planned_targets": 28, "completed_targets": 28, "current_target": None, "worker_alive": False, "pid": 22344, "canonical_progress_path": "runs/A5_v2_frozen_evaluation/evaluation_progress.json", "completion_timestamp": completion, "integrity_audit": "PASSED", "decode_warning_status": "WARNINGS_COMPARABLE_WITH_PRIOR_EVALUATIONS"}
    save(STATE / "a5_v2_frozen_eval_state.json", final)
    save(STATE / "a5_v2_frozen_eval_heartbeat.json", final)
    save(STATE / "a5_v2_frozen_eval_progress.json", {"status": "COMPLETED", "planned_targets": 28, "completed_targets": 28, "completion_timestamp": completion})


if __name__ == "__main__":
    main()
