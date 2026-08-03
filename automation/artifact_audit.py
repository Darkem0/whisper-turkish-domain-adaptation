# ruff: noqa
from __future__ import annotations
from .core import *

def build_reports() -> None:
    REPORTS.mkdir(exist_ok=True)
    files = sorted(p for p in ROOT.rglob("*") if p.is_file() and not any(x in p.parts for x in {".git", ".venv", "__pycache__"}))
    lines = ["# Artifact inventory", "", "Generated without modifying source artifacts.", "", "| Type | Count |", "|---|---:|"]
    for suffix in (".py", ".ps1", ".json", ".yaml", ".yml", ".csv", ".jsonl"):
        lines.append(f"| `{suffix}` | {sum(p.suffix == suffix for p in files)} |")
    lines += ["", "## Relevant A0-A2 paths", ""] + [f"- `{p.relative_to(ROOT)}`" for p in files if any(x.lower() in str(p).lower() for x in ("a0", "a1", "a2"))][:250]
    (REPORTS / "artifact_inventory.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    a0 = read(RUNS / "a0_v2d_final" / "a0_baseline_report_v2d.json", {})
    a2 = read(RUNS / "A2_v2d_eval" / "a2_evaluation_v2d.json", {})
    def values(doc: dict) -> list[str]:
        result=[]
        for group in doc.get("domain_metrics", {}).values():
            for name, metric in group.get("domain_metrics", {}).items(): result.append(f"| {name} | {metric['normalized_wer']:.5f} |")
        return result
    text = "# A0-A2 comparison\n\n## A0 normalized WER\n\n| Test | WER |\n|---|---:|\n" + "\n".join(values(a0.get("metrics", {}))) + "\n\n## A2 normalized WER\n\n| Test | WER |\n|---|---:|\n" + "\n".join(values(a2)) + "\n\nA1 configuration/artifacts are not presented as a completed comparable outcome unless its final immutable report exists.\n"
    (REPORTS / "a0_a1_a2_comparison.md").write_text(text, encoding="utf-8")
    (REPORTS / "missing_artifacts.md").write_text("# Missing artifacts\n\n- `A3_legacy_aborted_step34_invalid`: legacy aborted experiment; never resume or promote.\n- New D-profile prediction bundles: MISSING; not fabricated.\n- New A3_v2/A4_v2/A5_v2/A6_v2 clean training contracts: BLOCKED pending independently materialized recipe inputs.\n", encoding="utf-8")
    env = environment(); write(REPORTS / "environment_report.json", env)
    (REPORTS / "environment_report.md").write_text("# Environment\n\n```json\n"+json.dumps(env,ensure_ascii=False,indent=2)+"\n```\n", encoding="utf-8")
    (REPORTS / "reproducibility_risks.md").write_text("# Reproducibility risks\n\n- A0/A2 have local reports; only their recorded artifacts are treated as evidence.\n- Evaluation v2d is locked; new profile runs require the immutable registry to match.\n- No network retrieval is attempted, so absent model/data artifacts remain BLOCKED.\n- Historical A3 is invalid and quarantined by name.\n", encoding="utf-8")
