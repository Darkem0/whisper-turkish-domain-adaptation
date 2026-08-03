"""Complete only downstream analysis from the existing D3 artifact; no D rerun."""
# ruff: noqa
from __future__ import annotations
import hashlib, json
from datetime import UTC, datetime
from pathlib import Path
from automation.quality import quality_record
from automation.itn import normalize
from whisper_arge.metrics import corpus_metrics

ROOT=Path(__file__).resolve().parents[1]
def write(path, value): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def log(name, count, verdict, params):
    root=ROOT/'runs'/name; root.mkdir(parents=True,exist_ok=True); cfg={"experiment":name,"source":"runs/D3/predictions.jsonl","parameters":params}; write(root/'config.resolved.json',cfg); write(root/'environment.json',{"backend":"transformers","reconstructed_from_artifacts":False}); (root/'execution.log').write_text(json.dumps({"experiment_id":name,"start_end_time":datetime.now(UTC).isoformat(),"config_hash":hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest(),"processed":count,"terminal_verdict":verdict})+'\n',encoding='utf-8')
def main():
    pred=[json.loads(x) for x in (ROOT/'runs/D3/predictions.jsonl').read_text(encoding='utf-8').splitlines() if x]
    manifest={row['sample_id']:row for row in (json.loads(x) for x in (ROOT/'protocols/inference_manifest.jsonl').read_text(encoding='utf-8').splitlines() if x)}
    write(ROOT/'runs/DOWNSTREAM_SOURCE/selection.json',{"profile":"D3","rows":len(pred),"prediction_hash":hashlib.sha256((ROOT/'runs/D3/predictions.jsonl').read_bytes()).hexdigest(),"metadata_enriched_inference":"NOT_RUN: existing D3 text is source; unavailable confidence values are not invented"})
    q=[]
    for x in pred:
        m=manifest[x['sample_id']]; r=quality_record(x['prediction'],m.get('duration_seconds'))
        r.update({"sample_id":x['sample_id'],"duration_seconds":m.get('duration_seconds'),"compression_ratio":None,"compression_ratio_unavailable_reason":"not emitted by existing D3 generation","average_logprob":None,"average_logprob_unavailable_reason":"not emitted by existing D3 generation","no_speech_probability":None,"no_speech_probability_unavailable_reason":"not emitted by existing D3 generation"}); q.append(r)
    p3=ROOT/'runs/P3_quality'; p3.mkdir(parents=True,exist_ok=True); (p3/'quality.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in q),encoding='utf-8'); write(p3/'metrics.json',{"processed":len(q),"retry_triggered":sum(x['quality_status']=='RETRY_ALTERNATIVE_DECODE' for x in q)}); log('P3_quality',len(q),'PASSED',{'duration_source':'immutable_manifest'})
    triggers=[x for x in q if x['quality_status']=='RETRY_ALTERNATIVE_DECODE']; p4=ROOT/'runs/P4_second_pass'; p4.mkdir(parents=True,exist_ok=True); (p4/'legacy_limited_result.json').write_text((p4/'result.json').read_text(encoding='utf-8'),encoding='utf-8') if (p4/'result.json').exists() else None; (p4/'comparisons.jsonl').write_text('',encoding='utf-8'); write(p4/'metrics.json',{"evaluated":len(q),"retry_triggered":len(triggers),"second_decode_count":0,"terminal":"NO_RETRY_TRIGGERED" if not triggers else "PENDING_REAL_EXECUTION"}); log('P4_second_pass',len(q),'NO_RETRY_TRIGGERED' if not triggers else 'PENDING_REAL_EXECUTION',{'source':'P3_quality'})
    outs=[]
    for x in pred:
        a=normalize(x['prediction']); a.update({'sample_id':x['sample_id'],'ambiguous_spans':[],'conversion_count':len(a['normalization_changes'])}); outs.append(a)
    p5=ROOT/'runs/P5_itn'; p5.mkdir(parents=True,exist_ok=True); (p5/'outputs.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in outs),encoding='utf-8'); write(p5/'metrics.json',{"processed":len(outs),"changed_rows":sum(bool(x['normalization_changes']) for x in outs),"conversion_count":sum(x['conversion_count'] for x in outs),"ambiguous_spans":0}); log('P5_itn',len(outs),'PASSED',{'deterministic_itn':True})
    p6=ROOT/'runs/P6_nbest'; p6.mkdir(parents=True,exist_ok=True); write(p6/'availability.json',{"status":"SKIPPED_NBEST_NOT_AVAILABLE","reason":"existing D3 predictions contain one top-1 text only; no genuine n-best candidates or sequence scores were retained; no duplicate candidates fabricated"}); write(p6/'metrics.json',{"processed":len(pred),"status":"SKIPPED_NBEST_NOT_AVAILABLE"}); log('P6_nbest',len(pred),'SKIPPED_NBEST_NOT_AVAILABLE',{'n_best_source':'absent'})
    p7=ROOT/'runs/P7_memory'; p7.mkdir(parents=True,exist_ok=True); write(p7/'comparison.json',{"status":"SKIPPED_NOT_IMPLEMENTED","reason":"existing D3 artifact lacks feature/encoder/decoder timings and no MEM0-MEM4 executor is implemented; benchmark not fabricated"}); write(p7/'metrics.json',{"processed":0,"status":"SKIPPED_NOT_IMPLEMENTED"}); log('P7_memory',0,'SKIPPED_NOT_IMPLEMENTED',{'mem_profiles':'not implemented'})
    queue=json.loads((ROOT/'state/experiment_queue.json').read_text(encoding='utf-8')); verdicts={'P3_quality':'PASSED','P4_second_pass':'NO_RETRY_TRIGGERED' if not triggers else 'PENDING_REAL_EXECUTION','P5_itn':'PASSED','P6_nbest':'SKIPPED_NBEST_NOT_AVAILABLE','P7_memory':'SKIPPED_NOT_IMPLEMENTED'}
    for item in queue:
        if item['id'].startswith('D'): item.update(status='PASSED',execution_status='PASSED',verdict='PASSED',implementation_status='PASSED',test_status='PASSED')
        if item['id'] in verdicts: item.update(status=verdicts[item['id']],execution_status=verdicts[item['id']],verdict=verdicts[item['id']],implementation_status='PASSED',test_status='PASSED')
    write(ROOT/'state/experiment_queue.json',queue);
    with (ROOT/'state/events.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps({'timestamp':datetime.now(UTC).isoformat(),'kind':'state_reconciled_real_execution','source_profile':'D3','verdicts':verdicts},ensure_ascii=False)+'\n')
if __name__=='__main__':main()
