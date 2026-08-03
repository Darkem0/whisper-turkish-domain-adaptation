from __future__ import annotations

import json
import os
from pathlib import Path

from whisper_arge.local_continuation import build_inference_manifest, reconcile_queue


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SNAPSHOT = Path.home() / ".cache/huggingface/hub/models--openai--whisper-large-v3-turbo/snapshots/41f01f3fe87f28c78e2fbf8b568835947dd65ed9"


def main() -> None:
    reconciliation = reconcile_queue(ROOT)
    manifest = build_inference_manifest(ROOT)
    (ROOT / "configs/local_paths.yaml").write_text(
        json.dumps({"schema_version": 1, "workspace_root": str(ROOT), "root_mappings": {"materialized_data": str(ROOT / "data/materialized"), "hf_model_cache": str(Path(os.environ.get("WHISPER_ARGE_MODEL_SNAPSHOT", DEFAULT_SNAPSHOT))), "ffmpeg_executable": "MISSING: user must provide absolute ffmpeg.exe path; no download performed"}, "path_policy": "Fill only a missing root mapping; do not change manifests or evaluation locks."}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "state_reconciliation.md").write_text(f"# State reconciliation\n\nChanged: {', '.join(reconciliation['changed'])}. Progress is **{reconciliation['progress']}%** and counts `execution_status == PASSED` only. Prototype and test success are recorded separately and do not pass P3-P7.\n", encoding="utf-8")
    (reports / "inference_manifest_report.md").write_text(f"# Immutable inference manifest\n\n- Real local audio rows: {manifest['rows']}\n- Gold-reference rows: {manifest['gold_rows']}\n- SHA-256: `{manifest['manifest_sha256']}`\n- Manifest: `{manifest['manifest']}`\n", encoding="utf-8")
    blockers = "\n".join(f"- `{p}`" for p in manifest['missing_paths']) or "- No selected audio path is missing."
    (reports / "inference_manifest_blockers.md").write_text(f"# Inference manifest blockers\n\n{blockers}\n\nFFmpeg executable is not discoverable on PATH. `configs/local_paths.yaml:root_mappings.ffmpeg_executable` must be filled with an existing local executable before non-WAV source conversion is attempted.\n", encoding="utf-8")
    print(json.dumps({"reconciliation": reconciliation, "manifest": manifest}, ensure_ascii=False))


if __name__ == "__main__":
    main()
