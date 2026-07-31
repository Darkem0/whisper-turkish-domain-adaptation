# ruff: noqa
from __future__ import annotations
from .core import *

def run(item: dict) -> tuple[str, str | None]:
    if item["id"] == "P0_artifact_audit":
        from .artifact_audit import build_reports
        build_reports(); return "PASSED", None
    if item["id"] == "P1_immutable_lock":
        (ROOT / "protocols").mkdir(exist_ok=True)
        write(ROOT / "protocols" / "immutable_test_registry.json", immutable_registry())
        (ROOT / "protocols" / "promotion_gates.yaml").write_text(gate_registry(), encoding="utf-8")
        write(ROOT / "protocols" / "evaluation_lock.json", {"source_lock": "evaluation/EVAL_LOCK_v2d.json", "source_lock_sha256": sha(ROOT / "evaluation/EVAL_LOCK_v2d.json"), "registry": "protocols/immutable_test_registry.json"})
        return "PASSED", None
    if item["id"].startswith("D"):
        p = profile(item["id"]); out = RUNS / item["id"] / "config.resolved.yaml"; out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(p, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        return "BLOCKED", "No bounded immutable decoding manifest was supplied for a new profile run; existing A0/A2 predictions are preserved and no model/data download is permitted."
    if item["id"] in {"P3_quality", "P4_second_pass", "P5_itn", "P6_nbest", "P7_memory"}:
        return "BLOCKED", "Prototype is implemented and unit-tested, but no new immutable inference output is available to run this experiment family."
    return "BLOCKED", "WAITING_FOR_TRAINING_HOST: training recipe/data contract is not yet independently materialized for this v2 series."
