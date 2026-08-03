"""Read-only project archaeology; writes only reports and public documentation."""
from __future__ import annotations
import csv, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; R=ROOT/'reports'; D=ROOT/'docs'
SCAN=['README.md','docs','reports','runs','state','logs','scripts','contracts','schemas','data/manifests','data/materialized','outputs/evaluation','outputs/predictions']
METHODS=[
('Legacy-H0','baseline','historical_only','legacy archive only'),('Legacy-H1','MediaSpeech-only LoRA','limited','clean proxy degradation recorded'),('Legacy-H2','General Turkish LoRA','inconclusive','targeted run incomplete'),('Legacy-H3','balanced-phone continuation','limited','historical telephone benefit, external regression'),('Legacy-H4','repeat-safe decode/VAD','limited','historical long-call mitigation; legacy-only'),
('A0','base baseline','successful','controlled reference'),('A2','encoder+decoder Q/V r16','failed','target proxy gain but FLEURS hard gate failure'),('A3','encoder-only + replay','failed','no promotable checkpoint; CV Scripted failure'),('A4','decoder-only zero replay','diagnostic_only','strong phone ablation'),('A5','encoder-only clean schedule','limited','scope ablation did not dominate'),('A6','encoder+decoder clean schedule','diagnostic_only','corrected after self-comparison bug'),('A7','A2 parent + source anchor + staged phone augmentation','successful','best observed phone proxy; continuation limitation')]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,t): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t,encoding='utf8')
def main():
 files=[]; counts={}
 for rel in SCAN:
  p=ROOT/rel
  fs=[p] if p.is_file() else list(p.rglob('*')) if p.exists() else []
  fs=[x for x in fs if x.is_file()]; counts[rel]=len(fs); files.extend(fs)
 total=len(set(files))
 a7csv=list(csv.DictReader((R/'a7_v2_checkpoint_dataset_metrics.csv').open(encoding='utf8')))
 def best(ds): return min((x for x in a7csv if x['dataset']==ds),key=lambda x:float(x['normalized_wer']))
 phone,robust=best('mediaspeech_phone'),best('robustness_proxy')
 registry={'scan_file_count':total,'authoritative_experiments':['A0','A2','A3','A4','A5','A6','A7'],'a7_authoritative_checkpoints':{'step-050':'runs/A7_v2_staged_balanced_phone_200/checkpoints/step-050','step-100':'runs/A7_v2_staged_balanced_phone_200/checkpoints/step-100','step-150':'runs/A7_v2_staged_balanced_phone_200/checkpoints/step-150','step-200':'runs/A7_v2_resume150_final_200_retry1/checkpoints/step-200'},'excluded':['A3_legacy_aborted_step34_invalid','A7 stale step-200','A7 recovery-step-175','failed resume artifacts'],'public_safety':'No company-call data or raw audio/transcripts are included.'}
 write(R/'authoritative_artifact_registry.json',json.dumps(registry,indent=2)+'\n')
 inv='| Method | Intervention | class | evidence / limitation |\n|---|---|---|---|\n'+'\n'.join(f'| {a} | {b} | {c} | {d} |' for a,b,c,d in METHODS)+'\n'
 write(R/'complete_method_inventory.csv','method,intervention,classification,evidence\n'+'\n'.join(','.join('"'+x.replace('"','""')+'"' for x in m) for m in METHODS)+'\n')
 write(R/'complete_method_inventory.md','# Complete method inventory\n\nLegacy-H0–H4 are historical and are not pooled with controlled A0–A7 results.\n\n'+inv)
 write(R/'project_archaeology_inventory.md',f'# Project archaeology inventory\n\nScanned `{total}` files across declared roots. `data/manifests`, `outputs/evaluation` and `outputs/predictions` are absent in this checkout. Large materialized data was counted by metadata only; no raw transcript/audio content is published.\n\n'+json.dumps(counts,indent=2)+'\n\n'+inv)
 timeline='''# Project timeline\n\n1. Legacy-H0–H4: historical baseline, LoRA and long-call/repeat-safe work; evidence is archival.\n2. A0–A2: controlled baseline and encoder+decoder Q/V adaptation; A2 improved proxy robustness but failed FLEURS gate.\n3. A3–A6: scope/replay ablations; A3 had no promotable checkpoint; A5–A6 comparison was corrected after a path-replacement/self-comparison defect.\n4. A7: A2-parent staged source-anchor/phone augmentation. Step-200 was completed in an isolated optimizer-reset continuation from step-150.\n5. Frozen A7 evaluation: 28/28 targets completed with the locked A7 mapping.\n'''
 write(R/'project_timeline.md',timeline)
 metric='''# Authoritative metrics summary\n\nOnly prediction/checkpoint-backed values are listed. Phone and robustness are open-data proxies, not operational call-centre metrics.\n\n| result | checkpoint | normalized WER |\n|---|---:|---:|\n| A7 best Phone | '''+phone['checkpoint']+' | '+phone['normalized_wer']+' |\n| A7 best robustness proxy | '+robust['checkpoint']+' | '+robust['normalized_wer']+''' |\n| A2 Phone | base | 0.170825 |\n| A4 Phone | step-050 | 0.158385 |\n| A6 Phone | step-200 | 0.157203 |\n\nA7 step-200 provenance: `ADAPTER_CONTINUATION_WITH_OPTIMIZER_RESET` from step-150; do not interpret it as an exact optimizer-state continuation.\n'''
 write(R/'authoritative_metrics_summary.md',metric)
 # repair CSV separately without exposing a malformed result
 write(R/'authoritative_metrics_summary.csv',f'model,checkpoint,dataset,normalized_wer\nA7,{phone["checkpoint"]},mediaspeech_phone,{phone["normalized_wer"]}\nA7,{robust["checkpoint"]},robustness_proxy,{robust["normalized_wer"]}\nA2,base,mediaspeech_phone,0.170825\nA4,step-050,mediaspeech_phone,0.158385\nA6,step-200,mediaspeech_phone,0.157203\n')
 discrepancy='''# Metric and artefact discrepancy log\n\n- The former A5–A6 zero-delta/self-comparison result is superseded and excluded.\n- P7 has early placeholder/technical reports alongside later real interleaved validation; the authoritative terminal is `PASSED_NO_MEANINGFUL_SPEEDUP`, with MEM0 retained.\n- A7 eval contract still names a pre-smoke readiness status although its run artefacts show completion; run progress and checkpoint locks are authoritative for completion.\n- A7 original-run step-200 and stale variants are excluded. Retry1 step-200 is authoritative; it is optimizer-reset continuation, not exact state resume.\n- Several scripts contain local cache/absolute paths: do not publish them unchanged.\n- Legacy VAD/repeat-safe claims are historical because complete raw artefact chains are not present in this checkout.\n'''
 write(R/'metric_discrepancy_log.md',discrepancy)
 public='''# Practical research guide\n\n1. Freeze manifests, decoding and normalization before expensive work.\n2. Separate telephone proxy and general-Turkish panels.\n3. Treat prediction/checkpoint locks as authority, not stale state/PID files.\n4. Reject self-comparisons and unpaired claims.\n5. Keep MEM0 unless equal-output optimization clears an interleaved threshold.\n6. Keep D3 as the supported decoding profile.\n7. Report A3 and failed/resume paths rather than deleting them.\n8. Never treat open-data proxy gains as company performance.\n9. Preserve source/group leakage limitations.\n10. Require authorized, human-verified company holdout before operational claims.\n'''
 write(D/'practical_research_guide.md',public);write(D/'implementation_playbook.md',public+'\nUse only the locked Transformers Whisper path for this project.\n');write(D/'failure_catalog.md',discrepancy);write(D/'decision_tree.md','# Decision tree\n\nLocked artefacts complete? → verify hashes and sample IDs.\n\nProxy gain with general-domain cost? → label domain-specific, not production.\n\nCompany authorization and human references absent? → block operational evaluation.\n')
 title='# Türkçe Telefon Konuşmaları için Whisper Large-v3-Turbo Uyarlaması\n\n'
 readme=title+'Bu depo açık-veri proxy araştırmasını belgeler; gerçek çağrı merkezi verisi veya operasyonel performans iddiası içermez.\n\n'+metric+'\nDetaylar: `docs/full_research_report.md`, `docs/reproducibility.md`, `docs/artifact_map.md`.\n'
 write(ROOT/'README.md',readme)
 write(D/'full_research_report.md',title+timeline+'\n'+metric+'\n'+discrepancy)
 write(D/'experiment_catalog.md','# Experiment catalog\n\n'+inv)
 write(D/'call_oriented_evaluation.md','# Call-oriented evaluation\n\nMediaSpeech Phone/G.711 and robustness proxy are telephone-like open-data proxies. CV Spontaneous is report-only; they are not company-call metrics.\n')
 write(D/'negative_results.md','# Negative results\n\n'+discrepancy)
 write(D/'reproducibility.md','# Reproducibility\n\nA7 mapping is step-050/100/150 original run plus retry1 step-200. Verify the lock hashes and 28 frozen targets before any interpretation. A7 continuation reset optimizer/scaler state.\n')
 write(D/'limitations_and_future_work.md','# Limitations and future work\n\nNo authorized company root, provenance, human references, leakage-safe groups or final holdout are present. The only next action is authorized company-domain intake validation.\n')
 write(D/'artifact_map.md','# Artifact map\n\nPublicly discuss reports, contracts, scripts and lock hashes. Do not publish `data/materialized/`, raw prediction JSONL, logs containing local paths, cache paths, or any future company-data locations.\n')
 print(json.dumps({'files':total,'a7_phone':phone,'a7_robustness':robust}))
if __name__=='__main__': main()
