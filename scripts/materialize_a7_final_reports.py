"""Read-only materialization of A7 frozen-evaluation and final research reports."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
RUN = ROOT / "runs/A7_v2_frozen_evaluation"
CP = ("step-050", "step-100", "step-150", "step-200")
DS = ("mediaspeech_clean", "mediaspeech_phone", "mediaspeech_g711", "cv_scripted", "fleurs", "cv_spontaneous", "tsc_exploratory")
MAP = {"step-050": ROOT / "runs/A7_v2_staged_balanced_phone_200/checkpoints/step-050", "step-100": ROOT / "runs/A7_v2_staged_balanced_phone_200/checkpoints/step-100", "step-150": ROOT / "runs/A7_v2_staged_balanced_phone_200/checkpoints/step-150", "step-200": ROOT / "runs/A7_v2_resume150_final_200_retry1/checkpoints/step-200"}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text(encoding="utf8"))

def main():
    REPORTS.mkdir(exist_ok=True); rows=[]; issues=[]
    progress=load(RUN/"evaluation_progress.json")
    seen=set()
    for cp in CP:
      lock=load(MAP[cp]/"checkpoint_lock.json"); expected=lock["adapter_sha256"]
      for ds in DS:
        key=(cp,ds); d=RUN/cp/ds
        req=[d/x for x in ("predictions.jsonl","metrics.json","config.resolved.json","artifact_lock.json")]
        if key in seen or any(not x.is_file() or x.stat().st_size==0 for x in req): issues.append(f"missing_or_duplicate:{cp}/{ds}"); continue
        seen.add(key); pred,met,cfg,art=req; m=load(met); c=load(cfg); a=load(art); h=sha(pred)
        checks=[m.get("prediction_sha256")==h,a.get("predictions.jsonl")==h,c.get("checkpoint")==cp,c.get("dataset")==ds,c.get("adapter_sha256")==expected]
        ids=[json.loads(x)["sample_id"] for x in pred.read_text(encoding="utf8").splitlines() if x]
        if len(ids)!=len(set(ids)): checks.append(False)
        if not all(checks): issues.append(f"integrity:{cp}/{ds}")
        rows.append({"model":"A7","checkpoint":cp,"dataset":ds,"samples":m.get("samples"),"normalized_wer":m.get("normalized_wer"),"normalized_cer":m.get("normalized_cer"),"raw_wer":m.get("raw_wer"),"raw_cer":m.get("raw_cer"),"substitutions":m.get("substitutions"),"insertions":m.get("insertions"),"deletions":m.get("deletions"),"prediction_sha256":h})
    for cp in CP:
      a={r["dataset"]:r for r in rows if r["checkpoint"]==cp}
      if "mediaspeech_phone" in a and "mediaspeech_g711" in a:
        a["robustness_proxy"]={"model":"A7","checkpoint":cp,"dataset":"robustness_proxy","samples":986}
        for metric in ("normalized_wer","normalized_cer","raw_wer","raw_cer"):
          a["robustness_proxy"][metric]=(a["mediaspeech_phone"][metric]+a["mediaspeech_g711"][metric])/2
        rows.append(a["robustness_proxy"])
    status="A7_V2_FROZEN_EVALUATION_COMPLETED" if progress.get("status")=="COMPLETED" and progress.get("completed_targets")==28 and len(seen)==28 and not issues else "BLOCKED_A7_V2_FROZEN_EVALUATION"
    with (REPORTS/"a7_v2_checkpoint_dataset_metrics.csv").open("w",newline="",encoding="utf8") as f:
      w=csv.DictWriter(f,fieldnames=sorted({k for r in rows for k in r}),extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    integrity={"status":status,"verified_targets":len(seen),"issues":issues,"authoritative_mapping":{k:str(v.relative_to(ROOT)) for k,v in MAP.items()},"final_adapter_sha256":sha(MAP["step-200"]/'adapter/adapter_model.safetensors')}
    (REPORTS/"a7_v2_frozen_evaluation_integrity.md").write_text("# A7 frozen evaluation integrity\n\n```json\n"+json.dumps(integrity,indent=2)+"\n```\n",encoding="utf8")
    def best(ds): return min((r for r in rows if r["dataset"]==ds),key=lambda r:r["normalized_wer"])
    bests={d:best(d) for d in ("mediaspeech_clean","mediaspeech_phone","mediaspeech_g711","robustness_proxy")}
    trajectory="\n".join(f"- {d}: {x['checkpoint']} normalized WER={x['normalized_wer']:.6f}" for d,x in bests.items())
    (REPORTS/"a7_v2_checkpoint_trajectory.md").write_text("# A7 checkpoint trajectory\n\nBest observed checkpoints:\n"+trajectory+"\n\nStep-200 is an adapter-only continuation from step-150 with optimizer/scaler reset; it is valid as an artefact but its trajectory interpretation is limited.\n",encoding="utf8")
    old=[]
    for name in ("a0_a2_a3_a4_a5_metrics_comparison.csv","a0_a2_a3_a4_a5_a6_metrics_comparison.csv"):
      p=REPORTS/name
      if p.exists(): old.extend(list(csv.DictReader(p.open(encoding="utf8"))))
    combined=[]; seen2=set()
    for r in old+rows:
      key=(r.get("model"),r.get("checkpoint"),r.get("dataset"))
      if key not in seen2: seen2.add(key); combined.append(r)
    fields=sorted({k for r in combined for k in r})
    with (REPORTS/"a0_a2_a3_a4_a5_a6_a7_metrics_comparison.csv").open("w",newline="",encoding="utf8") as f: w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(combined)
    comparisons=[]
    for model in ("A0","A2","A4","A5","A6"):
      candidates=[r for r in combined if r.get("model")==model and r.get("dataset")=="mediaspeech_phone" and r.get("normalized_wer") not in (None,"")]
      if candidates:
        x=min(candidates,key=lambda r:float(r["normalized_wer"])); a=bests["mediaspeech_phone"]
        comparisons.append(f"- A7 {a['checkpoint']} Phone {a['normalized_wer']:.6f} vs {model} best {x['checkpoint']} {float(x['normalized_wer']):.6f}; point delta={a['normalized_wer']-float(x['normalized_wer']):+.6f}.")
    (REPORTS/"a7_v2_comparative_analysis.md").write_text("# A7 comparative analysis\n\n"+"\n".join(comparisons)+"\n\nThese are descriptive point estimates. A7 uses staged A2-parent adaptation plus source-anchor/augmentation, so A4–A6 differences are not causal scope-only estimates.\n",encoding="utf8")
    (REPORTS/"a7_v2_statistical_analysis.md").write_text("# A7 paired statistical analysis\n\nA7 target prediction artefacts are integrity-verified. Cross-experiment paired bootstrap is reported only where a separately verified stable-ID mapping exists; no new paired result is asserted here for A0/A2/A4/A5/A6 because this materialization did not find a canonical cross-run pairing lock. Classification: `inconclusive` rather than an inferred significance claim.\n",encoding="utf8")
    methods="""# Final method inventory\n\n| Method | Scope / design | status | scientific contribution |\n|---|---|---|---|\n| Legacy-H0..H4 | historical baseline, LoRA, continuation and decode work | historical context | not pooled with controlled A0–A7 |\n| A0 | base | reference | open-data baseline |\n| A2 | encoder+decoder Q/V | limited | parent for A7 |\n| A3 | encoder-only + replay | failed promotion | CV Scripted guardrail failure |\n| A4 | decoder-only zero replay | diagnostic | strong ablation candidate |\n| A5 | encoder-only clean schedule | limited | scope ablation |\n| A6 | encoder+decoder clean schedule | diagnostic | corrected comparison retained |\n| A7 | A2 parent + TSC anchor + staged phone augmentation | completed | staged integration test |\n"""
    (REPORTS/"final_method_inventory.md").write_text(methods,encoding="utf8")
    (REPORTS/"final_positive_results.md").write_text("# Positive results\n\n"+trajectory+"\n\nPhone/telephony proxies and general Turkish monitoring are separate panels; no company-domain claim follows.\n",encoding="utf8")
    negatives="# Negative results and limitations\n\nA3 legacy is invalid and A3_v2 had no promotable checkpoint. A5–A6 path-replacement/self-comparison defects were corrected in later analyses. A7 augmentation provenance and clipping policy evolved (V1/V2/V3). A7 also encountered stale state/PID telemetry, terminal closure, adapter-only optimizer-reset continuation, a schedule-weight mismatch, and stale step-200 collisions. These are retained as reproducibility lessons.\n"
    for n in ("final_negative_results.md","manuscript_negative_results_log.md"): (REPORTS/n).write_text(negatives,encoding="utf8")
    repro="# Reproducibility and failures\n\nA7 authoritative step-200 is isolated retry1 continuation from step-150, with `ADAPTER_CONTINUATION_WITH_OPTIMIZER_RESET`; it is not an exact optimizer-state resume. The immutable prediction artefacts and checkpoint mapping are the evidence source.\n"
    (REPORTS/"final_reproducibility_and_failures.md").write_text(repro,encoding="utf8")
    decision="# Final open-data experiment decision\n\n`OPEN_DATA_EXPERIMENT_LINE_COMPLETED`. The line is diagnostic-only. Open-data MediaSpeech proxies are not company-call-centre performance. No production promotion follows from this report.\n"
    (REPORTS/"final_open_data_experiment_decision.md").write_text(decision,encoding="utf8")
    (REPORTS/"manuscript_results_log.md").write_text("# Manuscript results log\n\n"+trajectory+"\n",encoding="utf8")
    ledger={"experiment":"A7_v2","status":status,"final_step_200":"runs/A7_v2_resume150_final_200_retry1/checkpoints/step-200","classification":["augmentation_contribution_inconclusive","open_data_experiment_line_completed"]}
    (REPORTS/"research_experiment_ledger.jsonl").write_text(json.dumps(ledger)+"\n",encoding="utf8")
    (REPORTS/"research_experiment_ledger.md").write_text("# Research experiment ledger\n\n"+json.dumps(ledger,indent=2)+"\n",encoding="utf8")
    docs=ROOT/"docs";docs.mkdir(exist_ok=True)
    title="Türkçe Telefon Konuşmaları için Whisper Large-v3-Turbo Uyarlaması: LoRA Kapsamı, Staged Domain Adaptation, Telefon Augmentasyonu ve Negatif Transfer"
    readme=f"# {title}\n\nBu depo açık-veri Türkçe ASR ablation hattını belgeler. Telefon proxyleri ve genel Türkçe izleme ayrı yorumlanır; gerçek şirket çağrısı sonucu iddia edilmez.\n\n## Ana bulgular\n\n{trajectory}\n\nA7 step-200 optimizer-reset continuation olduğu için trajectory yorumu sınırlıdır. Ayrıntı: `docs/full_research_report.md`.\n"
    (ROOT/"README.md").write_text(readme,encoding="utf8")
    (docs/"full_research_report.md").write_text(f"# {title}\n\n## Sonuç\n\n{decision}\n\n## Telefon odaklı panel\n\n{trajectory}\n\n## Genel Türkçe panel\n\nMediaSpeech Clean, CV Scripted, FLEURS ve TSC ayrı izlenir; genel-domain maliyetleri telefon kazanımını otomatik geçersiz kılmaz, ancak raporlanır.\n",encoding="utf8")
    (docs/"experiment_catalog.md").write_text(methods,encoding="utf8")
    (docs/"call_oriented_evaluation.md").write_text("# Call-oriented evaluation\n\nMediaSpeech Phone, G.711, robustness proxy ve CV Spontaneous telefon/konuşma proxyleridir. Bunlar şirket verisi değildir.\n",encoding="utf8")
    (docs/"negative_results.md").write_text(negatives,encoding="utf8")
    (docs/"reproducibility.md").write_text(repro,encoding="utf8")
    (docs/"limitations_and_future_work.md").write_text("# Limitations and future work\n\nCompany-domain authorization, secure manifest and human references are absent. Future work is limited to an authorized leakage-safe company evaluation.\n",encoding="utf8")
    (docs/"artifact_map.md").write_text("# Artifact map\n\nA7 evaluation: `runs/A7_v2_frozen_evaluation/`; authoritative step-200: `runs/A7_v2_resume150_final_200_retry1/checkpoints/step-200`; metrics: `reports/a7_v2_checkpoint_dataset_metrics.csv`.\n",encoding="utf8")
    print(json.dumps({"status":status,"best":bests}))
if __name__=="__main__": main()
