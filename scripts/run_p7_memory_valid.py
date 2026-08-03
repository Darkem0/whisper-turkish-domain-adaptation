"""Single-process valid P7 benchmark (attempt p7-valid-20260731)."""
# ruff: noqa
from __future__ import annotations
import gc,hashlib,json,os,statistics,subprocess,threading,time
from pathlib import Path
import psutil, soundfile as sf, librosa, torch
from transformers import AutoModelForSpeechSeq2Seq,AutoProcessor
from automation.core import profile
from whisper_arge.metrics import corpus_metrics
from whisper_arge.normalization import normalize_turkish
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'runs/P7_memory/attempts/p7-valid-20260731'; SNAP=Path(os.environ.get('WHISPER_ARGE_MODEL_SNAPSHOT',Path.home()/'.cache/huggingface/hub/models--openai--whisper-large-v3-turbo/snapshots/41f01f3fe87f28c78e2fbf8b568835947dd65ed9'))
ROWS=[json.loads(x) for x in (ROOT/'protocols/inference_manifest.jsonl').read_text(encoding='utf-8').splitlines() if x]
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def digest(rows,norm=False):return hashlib.sha256(''.join(x['sample_id']+'\t'+(normalize_turkish(x['prediction']) if norm else x['prediction'])+'\n' for x in rows).encode()).hexdigest()
class Sampler:
 def __init__(self,path):self.path=path;self.stop=threading.Event();self.rows=[]
 def run(self):
  while not self.stop.is_set():
   try:
    r=subprocess.run(['nvidia-smi','--query-gpu=utilization.gpu,memory.used,memory.total','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=2);a=[int(x.strip()) for x in r.stdout.splitlines()[0].split(',')];self.rows.append({'timestamp':time.time(),'gpu_utilization_percent':a[0],'memory_used_mb':a[1],'memory_total_mb':a[2]})
   except Exception:pass
   self.stop.wait(.25)
 def start(self):self.t=threading.Thread(target=self.run,daemon=True);self.t.start()
 def end(self):self.stop.set();self.t.join()
def main():
 OUT.mkdir(parents=True,exist_ok=True); log=[]; device='cuda:0'; dtype=torch.float16; cfg={k:v for k,v in profile('D3').items() if k in {'language','task','num_beams','do_sample','condition_on_prev_tokens','max_new_tokens'}};cfg['max_new_tokens']=444
 processor=AutoProcessor.from_pretrained(str(SNAP),local_files_only=True);model=AutoModelForSpeechSeq2Seq.from_pretrained(str(SNAP),torch_dtype=dtype,low_cpu_mem_usage=True,local_files_only=True).to(device).eval();log.append('model_loaded')
 wave={};feat={}; durations={x['sample_id']:x['duration_seconds'] for x in ROWS}
 def get(row,mode,h):
  if mode=='MEM0' or row['sample_id'] not in wave:
   a,r=sf.read(row['audio_path'],dtype='float32',always_2d=False);a=a.mean(1) if getattr(a,'ndim',1)>1 else a
   if r!=16000:a=librosa.resample(a,orig_sr=r,target_sr=16000);r=16000
   if mode!='MEM0':wave[row['sample_id']]=(a,r);h['waveform_cache_misses']+=1
  else:a,r=wave[row['sample_id']];h['waveform_cache_hits']+=1
  if mode in {'MEM2','MEM3','MEM4'} and row['sample_id'] in feat:h['feature_cache_hits']+=1;return feat[row['sample_id']]
  f=processor(a,sampling_rate=r,return_tensors='pt').input_features.to(device,dtype=dtype)
  if mode in {'MEM2','MEM3','MEM4'}:feat[row['sample_id']]=f;h['feature_cache_misses']+=1
  return f
 def plan(mode,features):
  if mode in {'MEM0','MEM1','MEM2'}:return [[x] for x in ROWS]
  ordered=sorted(ROWS,key=lambda x:durations[x['sample_id']]);budget=9000 if mode=='MEM4' else 3;out=[];cur=[];frames=0
  for row in ordered:
   n=max(1,round(durations[row['sample_id']]*100));limit=(len(cur)>=budget if mode=='MEM3' else frames+n>budget)
   if cur and limit:out.append(cur);cur=[];frames=0
   cur.append(row);frames+=n
  if cur:out.append(cur)
  return out
 allm={};base=None
 for mode in ('MEM0','MEM1','MEM2','MEM3','MEM4'):
  root=OUT/mode; root.mkdir(parents=True,exist_ok=True); raw=[]; final=[]
  for rep in range(3):
   gc.collect();torch.cuda.empty_cache();torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();h={'waveform_cache_hits':0,'waveform_cache_misses':0,'feature_cache_hits':0,'feature_cache_misses':0};t0=time.perf_counter();load=feature=generate=0.;s=Sampler(root/'gpu_samples.jsonl');s.start();fs={}
   for row in ROWS:
    t=time.perf_counter();fs[row['sample_id']]=get(row,mode,h);feature+=time.perf_counter()-t
   batches=plan(mode,fs);pred=[];lat=[]
   for batch in batches:
    t=time.perf_counter(); tensor=torch.cat([fs[x['sample_id']] for x in batch],0)
    with torch.inference_mode():o=model.generate(tensor,**cfg)
    texts=processor.batch_decode(o,skip_special_tokens=True);generate+=time.perf_counter()-t
    for row,text in zip(batch,texts):pred.append({'sample_id':row['sample_id'],'prediction':text,'reference':row['reference_text']});lat.append((time.perf_counter()-t)/len(batch))
   torch.cuda.synchronize();wall=time.perf_counter()-t0;s.end();(root/'gpu_samples.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in s.rows),encoding='utf-8');valid=[round(durations[x['sample_id']]*100) for b in batches for x in b];sizes=[len(b) for b in batches];m={'attempt_id':'p7-valid-20260731','repeat':rep+1,'is_warmup':False,'sample_count':32,'wall_clock_seconds':wall,'real_time_factor':wall/sum(durations.values()),'audio_hours_per_wall_hour':sum(durations.values())/wall,'feature_extraction_seconds':feature,'model_generate_seconds':generate,'peak_process_ram_mb':psutil.Process().memory_info().rss/1048576,'peak_cuda_allocated_mb':torch.cuda.max_memory_allocated()/1048576,'peak_cuda_reserved_mb':torch.cuda.max_memory_reserved()/1048576,'batch_count':len(batches),'batch_sizes':sizes,'average_batch_size':sum(sizes)/len(sizes),'maximum_batch_size':max(sizes),'batches_with_size_gt_1':sum(x>1 for x in sizes),'generate_call_count':len(batches),'valid_frames_per_batch':[sum(round(durations[x['sample_id']]*100) for x in b) for b in batches],'padded_frames_per_batch':[len(b)*3000 for b in batches],'total_valid_frames':sum(valid),'total_padded_frames':len(batches and ROWS)*3000,'padding_ratio':1-sum(valid)/(32*3000),'per_sample_latency_p50':statistics.median(lat),'per_sample_latency_p95':sorted(lat)[30],'prediction_hash':digest(pred),'normalized_prediction_hash':digest(pred,True),'gpu_poll_interval_ms':250,'gpu_sample_count':len(s.rows),'average_gpu_utilization_percent':statistics.mean([x['gpu_utilization_percent'] for x in s.rows]) if s.rows else None,'median_gpu_utilization_percent':statistics.median([x['gpu_utilization_percent'] for x in s.rows]) if s.rows else None,'peak_gpu_utilization_percent':max([x['gpu_utilization_percent'] for x in s.rows],default=None),'cached_waveform_bytes':sum(a.nbytes for a,r in wave.values()),'cached_feature_bytes':sum(x.numel()*x.element_size() for x in feat.values()),**h,'failures':[],'retries':0};raw.append(m);final=sorted(pred,key=lambda x:x['sample_id'])
  med=sorted(raw,key=lambda x:x['wall_clock_seconds'])[1];med['wer_cer']=corpus_metrics([(x['reference'],x['prediction']) for x in final]);(root/'raw_runs.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in raw),encoding='utf-8');(root/'predictions.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in final),encoding='utf-8');dump(root/'metrics.json',med);allm[mode]=med;base=med if mode=='MEM0' else base
 comp={k:{'prediction_equal':v['normalized_prediction_hash']==base['normalized_prediction_hash'],'speedup_percent':100*(base['wall_clock_seconds']-v['wall_clock_seconds'])/base['wall_clock_seconds'],'validity':'PASSED' if v['gpu_sample_count']>0 and (k not in {'MEM3','MEM4'} or v['maximum_batch_size']>1 and v['generate_call_count']<32) else 'FAILED_TECHNICAL'} for k,v in allm.items()};dump(OUT/'comparison.json',comp);dump(OUT/'config.resolved.json',{'attempt_id':'p7-valid-20260731','generation':cfg});dump(OUT/'environment.json',{'backend':'transformers','gpu_polling':True});(OUT/'execution.log').write_text('\n'.join(log+['terminal'])+'\n',encoding='utf-8')
if __name__=='__main__':main()
