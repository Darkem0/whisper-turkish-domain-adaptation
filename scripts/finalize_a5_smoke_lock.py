"""Add the authorized A5 contract and output hashes to a passed smoke lock."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "runs/A5_v2_resource_smoke"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    metrics = json.loads((SMOKE / "metrics.json").read_text(encoding="utf-8"))
    if metrics.get("status") != "PASSED" or metrics.get("exit_code") != 0:
        raise RuntimeError("cannot finalize a failed A5 smoke")
    lock = json.loads((SMOKE / "artifact_lock.json").read_text(encoding="utf-8"))
    lock["contract_sha256"] = {str(path.relative_to(ROOT)).replace("\\", "/"): sha(path) for path in (ROOT / "contracts/A5_v2_training_contract.yaml", ROOT / "contracts/A5_v2_data_manifest.lock.json", ROOT / "contracts/A5_v2_eval_contract.yaml")}
    lock["outputs_sha256"] = {str(path.relative_to(SMOKE)).replace("\\", "/"): sha(path) for path in (SMOKE / "metrics.json", SMOKE / "training_progress.jsonl", SMOKE / "adapter/adapter_model.safetensors", SMOKE / "adapter/adapter_config.json")}
    (SMOKE / "artifact_lock.json").write_text(json.dumps(lock, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
