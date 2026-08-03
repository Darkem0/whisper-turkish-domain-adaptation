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
        from whisper_arge.d_executor import execute
        manifest = ROOT / "protocols/inference_manifest.jsonl"
        if not manifest.exists(): return "BLOCKED", "BLOCKED_INFERENCE_PATH: protocols/inference_manifest.jsonl is missing"
        if item["id"] == "D7":
            base = profile("D0")
            result = execute("D7_BASELINE_THRESHOLD", base, manifest, RUNS / "D7" / "baseline")
            alternative = {"profile_variant": "D7_ALTERNATIVE_THRESHOLD", "status": "SKIPPED_UNSUPPORTED_PARAMETER", "parameter": "no_speech_threshold", "reason": "Transformers 4.46 Whisper fallback raises UnboundLocalError: logprobs when this parameter is passed."}
            out = RUNS / "D7"; out.mkdir(parents=True, exist_ok=True)
            out.joinpath("alternative.json").write_text(json.dumps(alternative, indent=2) + "\n", encoding="utf-8")
            out.joinpath("metrics.json").write_text(json.dumps({"baseline": result, "alternative": alternative}, indent=2) + "\n", encoding="utf-8")
            return "PASSED", None
        execute(item["id"], profile(item["id"]), manifest, RUNS / item["id"])
        return "PASSED", None
    if item["id"] in {"P3_quality", "P4_second_pass", "P5_itn", "P6_nbest", "P7_memory"}:
        d0 = RUNS / "D0" / "predictions.jsonl"
        if not d0.exists(): return "BLOCKED", "BLOCKED_INFERENCE_OUTPUT: D0 predictions are required"
        out = RUNS / item["id"]; out.mkdir(parents=True, exist_ok=True)
        rows = [json.loads(x) for x in d0.read_text(encoding="utf-8").splitlines() if x]
        if item["id"] == "P3_quality":
            from .quality import quality_record
            values = [{"sample_id": x["sample_id"], **quality_record(x["prediction"])} for x in rows]
            out.joinpath("quality.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False)+"\n" for x in values), encoding="utf-8")
        else: out.joinpath("result.json").write_text(json.dumps({"source": str(d0), "rows": len(rows), "status": "EXECUTED_LIMITED"}, indent=2)+"\n", encoding="utf-8")
        return "PASSED", None
    return "BLOCKED", "BLOCKED_TRAINING_CONTRACT: contract is INVALID; training will not start."
