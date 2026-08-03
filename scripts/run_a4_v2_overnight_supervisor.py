"""A4 single-experiment supervisor design. It is intentionally not a training launcher."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "A4_v2_training_contract.yaml"
STAGES = ["contract_hash_preflight", "resource_smoke_2_steps", "smoke_audit", "training_200_steps", "checkpoint_validation", "training_integrity", "frozen_evaluation", "quality_artifacts", "paired_ci", "promotion_gate_audit", "terminal_report"]

def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract["status"] != "READY_FOR_A4_V2_RESOURCE_SMOKE":
        raise SystemExit("BLOCKED_CONTRACT: materialize and hash a group-disjoint validation manifest before any worker can start")
    raise SystemExit("DESIGN_ONLY: this supervisor is not authorized to launch from this task")

if __name__ == "__main__":
    raise SystemExit(main())
