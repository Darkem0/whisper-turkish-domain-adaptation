"""Single-process MEM0/MEM2 cold/warm interleaved validation."""
# ruff: noqa
from __future__ import annotations
import gc,hashlib,json,os,statistics,time
from pathlib import Path
import psutil,soundfile as sf,librosa,torch
from transformers import AutoModelForSpeechSeq2Seq,AutoProcessor
from automation.core import profile
from whisper_arge.metrics import corpus_metrics
from whisper_arge.normalization import normalize_turkish
R=Path(__file__).resolve().parents[1];O=R/'runs/P7_memory/attempts/p7-mem2-interleaved';S=Path(os.environ.get('WHISPER_ARGE_MODEL_SNAPSHOT',Path.home()/'.cache/huggingface/hub/models--openai--whisper-large-v3-turbo/snapshots/41f01f3fe87f28c78e2fbf8b568835947dd65ed9'));rows=[json.loads(x) for x in (R/'protocols/inference_manifest.jsonl').read_text(encoding='utf-8').splitlines() if x]
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def dh(xs,n=False):return hashlib.sha256(''.join(x['sample_id']+'\t'+(normalize_turkish(x['prediction']) if n else x['prediction'])+'\n' for x in xs).encode()).hexdigest()
def main():
 O.mkdir(parents=True,exist_ok=True);g={k:v for k,v in profile('D3').items() if k in {'language','task','num_beams','do_sample','condition_on_prev_tokens'}};g['max_new_tokens']=444;p=AutoProcessor.from_pretrained(str(S),local_files_only=True);m=AutoModelForSpeechSeq2Seq.from_pretrained(str(S),torch_dtype=torch.float16,local_files_only=True).to('cuda').eval(); wave={};feat={};raw=[];order=['MEM0','MEM2_COLD','MEM2_WARM','MEM2_WARM','MEM2_COLD','MEM0','MEM2_WARM','MEM0','MEM2_COLD','MEM0','MEM2_WARM','MEM2_COLD']
 def prep(cache=True):
  for x in rows:
   if x['sample_id'] not in wave:
    a,sr=sf.read(x['audio_path'],dtype='float32');
    if sr!=16000:a=librosa.resample(a,orig_sr=sr,target_sr=16000);sr=16000
    wave[x['sample_id']]=(a,sr)
   if x['sample_id'] not in feat:feat[x['sample_id']]=p(wave[x['sample_id']][0],sampling_rate=16000,return_tensors='pt').input_features
 # separate warm-up, excluded
 prep();
 with torch.inference_mode():m.generate(feat[rows[0]['sample_id']].to('cuda',dtype=torch.float16),**g)
 for idx,kind in enumerate(order,1):
  gc.collect();torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();cold=kind=='MEM2_COLD';
  if cold:wave.clear();feat.clear()
  if kind=='MEM2_WARM':prep()
  t0=time.perf_counter();load=fe=transfer=gen=0.;out=[];wh=wm=fh=fm=0
  for x in rows:
   if kind=='MEM0' or x['sample_id'] not in wave:
    t=time.perf_counter();a,sr=sf.read(x['audio_path'],dtype='float32');
    if sr!=16000:a=librosa.resample(a,orig_sr=sr,target_sr=16000);sr=16000
    load+=time.perf_counter()-t
    if kind!='MEM0':wave[x['sample_id']]=(a,sr);wm+=1
   else:a,sr=wave[x['sample_id']];wh+=1
   if kind!='MEM0' and x['sample_id'] in feat:f=feat[x['sample_id']];fh+=1
   else:
    t=time.perf_counter();f=p(a,sampling_rate=sr,return_tensors='pt').input_features;fe+=time.perf_counter()-t
    if kind!='MEM0':feat[x['sample_id']]=f;fm+=1
   t=time.perf_counter();f=f.to('cuda',dtype=torch.float16);transfer+=time.perf_counter()-t;t=time.perf_counter()
   with torch.inference_mode():z=m.generate(f,**g)
   gen+=time.perf_counter()-t;out.append({'sample_id':x['sample_id'],'prediction':p.batch_decode(z,skip_special_tokens=True)[0],'reference':x['reference_text']})
  torch.cuda.synchronize();wall=time.perf_counter()-t0;audio=sum(x['duration_seconds'] for x in rows);raw.append({'run_order':idx,'profile':kind,'cold_or_warm':kind,'wall_clock_seconds':wall,'waveform_load_seconds':load,'feature_extraction_seconds':fe,'cpu_to_gpu_transfer_seconds':transfer,'model_generate_seconds':gen,'postprocess_seconds':0,'real_time_factor':wall/audio,'throughput':audio/wall,'peak_vram_mb':torch.cuda.max_memory_allocated()/1048576,'process_ram_mb':psutil.Process().memory_info().rss/1048576,'waveform_cache_hits':wh,'waveform_cache_misses':wm,'feature_cache_hits':fh,'feature_cache_misses':fm,'prediction_hash':dh(out),'normalized_prediction_hash':dh(out,True),'wer_cer':corpus_metrics([(x['reference'],x['prediction']) for x in out])})
  (O/'execution.log').open('a',encoding='utf-8').write(f'{idx} {kind} {wall}\n')
 (O/'raw_runs.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in raw),encoding='utf-8'); groups={k:[x for x in raw if x['profile']==k] for k in set(order)};base=statistics.median(x['wall_clock_seconds'] for x in groups['MEM0']);comp={}
 for k,v in groups.items():
  med=statistics.median(x['wall_clock_seconds'] for x in v);equal=all(x['normalized_prediction_hash']==groups['MEM0'][0]['normalized_prediction_hash'] and x['wer_cer']==groups['MEM0'][0]['wer_cer'] for x in v);comp[k]={'count':len(v),'median_wall':med,'mean_wall':statistics.mean(x['wall_clock_seconds'] for x in v),'stddev':statistics.stdev(x['wall_clock_seconds'] for x in v),'min':min(x['wall_clock_seconds'] for x in v),'max':max(x['wall_clock_seconds'] for x in v),'median_rtf':statistics.median(x['real_time_factor'] for x in v),'median_throughput':statistics.median(x['throughput'] for x in v),'speedup_percent':100*(base-med)/base,'prediction_equal':equal};dump(O/k/'metrics.json',comp[k])
 dump(O/'comparison.json',comp);dump(O/'environment.json',{'model_loads':1,'cuda_empty_cache_called':False});
if __name__=='__main__':main()
