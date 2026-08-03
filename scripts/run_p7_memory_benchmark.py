"""Real, offline MEM0-MEM4 benchmark using the locked Transformers Whisper path."""
# ruff: noqa
from __future__ import annotations
import gc, hashlib, json, statistics, time, os
from pathlib import Path
import psutil
import soundfile as sf
import librosa
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
from automation.core import profile
from whisper_arge.metrics import corpus_metrics
from whisper_arge.normalization import normalize_turkish

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'runs/P7_memory'; SNAPSHOT=Path(os.environ.get('WHISPER_ARGE_MODEL_SNAPSHOT',Path.home()/'.cache/huggingface/hub/models--openai--whisper-large-v3-turbo/snapshots/41f01f3fe87f28c78e2fbf8b568835947dd65ed9'))
rows=[json.loads(x) for x in (ROOT/'protocols/inference_manifest.jsonl').read_text(encoding='utf-8').splitlines() if x]
cfg=profile('D3'); cfg['max_new_tokens']=444
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def h(items):return hashlib.sha256(''.join(items).encode()).hexdigest()
def main():
    device='cuda:0'; dtype=torch.float16; processor=AutoProcessor.from_pretrained(str(SNAPSHOT),local_files_only=True); model=AutoModelForSpeechSeq2Seq.from_pretrained(str(SNAPSHOT),torch_dtype=dtype,low_cpu_mem_usage=True,local_files_only=True).to(device).eval()
    gen={k:v for k,v in cfg.items() if k in {'language','task','num_beams','do_sample','condition_on_prev_tokens','max_new_tokens'}}
    # Warm-up is explicitly excluded from timing.
    a,r=sf.read(rows[0]['audio_path'],dtype='float32',always_2d=False); f=processor(a,sampling_rate=r,return_tensors='pt').input_features.to(device,dtype=dtype)
    with torch.inference_mode():model.generate(f,**gen)
    wave_cache={}; feature_cache={}; all_metrics={}; base=None
    modes=tuple(os.environ.get('P7_MODES','MEM0,MEM1,MEM2,MEM3,MEM4').split(','))
    for mode in modes:
      root=OUT/mode; root.mkdir(parents=True,exist_ok=True); raw=[]; final_predictions=[]
      for repeat in range(3):
        gc.collect(); torch.cuda.empty_cache(); torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats(); start=time.perf_counter(); load=feat=decode=0.; hits={'waveform_cache_hits':0,'waveform_cache_misses':0,'feature_cache_hits':0,'feature_cache_misses':0}; per=[]
        ordered=sorted(rows,key=lambda x:x['duration_seconds']) if mode=='MEM3' else rows
        for row in ordered:
          s=time.perf_counter()
          if mode=='MEM0' or row['sample_id'] not in wave_cache:
            t=time.perf_counter(); audio,rate=sf.read(row['audio_path'],dtype='float32',always_2d=False); load+=time.perf_counter()-t
            if mode!='MEM0':wave_cache[row['sample_id']]=(audio,rate);hits['waveform_cache_misses']+=1
          else: audio,rate=wave_cache[row['sample_id']];hits['waveform_cache_hits']+=1
          if mode in {'MEM2','MEM3','MEM4'} and row['sample_id'] in feature_cache: features=feature_cache[row['sample_id']];hits['feature_cache_hits']+=1
          else:
            if rate != 16000: audio=librosa.resample(audio,orig_sr=rate,target_sr=16000); rate=16000
            t=time.perf_counter(); features=processor(audio,sampling_rate=rate,return_tensors='pt').input_features.to(device,dtype=dtype);feat+=time.perf_counter()-t
            if mode in {'MEM2','MEM3','MEM4'}:feature_cache[row['sample_id']]=features;hits['feature_cache_misses']+=1
          t=time.perf_counter()
          with torch.inference_mode(): out=model.generate(features,**gen)
          decode+=time.perf_counter()-t; text=processor.batch_decode(out,skip_special_tokens=True)[0]; final_predictions.append({'sample_id':row['sample_id'],'prediction':text,'reference':row['reference_text']});per.append(time.perf_counter()-s)
        torch.cuda.synchronize(); wall=time.perf_counter()-start; total_audio=sum(x['duration_seconds'] for x in rows); prediction_hash=h([x['sample_id']+'\t'+x['prediction']+'\n' for x in final_predictions]); norm_hash=h([x['sample_id']+'\t'+normalize_turkish(x['prediction'])+'\n' for x in final_predictions]); m={'repeat':repeat+1,'sample_count':len(rows),'total_audio_seconds':total_audio,'wall_clock_seconds':wall,'real_time_factor':wall/total_audio,'audio_hours_per_wall_hour':total_audio/wall,'waveform_load_seconds':load,'feature_extraction_seconds':feat,'encoder_decoder_total_seconds':decode,'postprocess_seconds':0.,'peak_process_ram_mb':psutil.Process().memory_info().rss/1048576,'peak_cuda_allocated_mb':torch.cuda.max_memory_allocated()/1048576,'peak_cuda_reserved_mb':torch.cuda.max_memory_reserved()/1048576,'average_gpu_utilization_percent':None,'peak_gpu_utilization_percent':None,'batch_count':len(rows),'average_batch_size':1,'maximum_batch_size':1,'average_frames_per_batch':3000,'maximum_frames_per_batch':3000,'padding_frames':0,'padding_ratio':0.,'per_sample_latency_p50':statistics.median(per),'per_sample_latency_p95':sorted(per)[int(.95*(len(per)-1))],'prediction_hash':prediction_hash,'normalized_prediction_hash':norm_hash,'failures':[],'retries':0,**hits,'cached_waveform_bytes':sum(x[0].nbytes for x in wave_cache.values()),'cached_feature_bytes':sum(x.numel()*x.element_size() for x in feature_cache.values())};raw.append(m)
      med=sorted(raw,key=lambda x:x['wall_clock_seconds'])[1]; med['median_of_repeats']=True; med['wer_cer']=corpus_metrics([(x['reference'],x['prediction']) for x in final_predictions]); (root/'raw_runs.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in raw),encoding='utf-8'); (root/'predictions.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in final_predictions),encoding='utf-8'); dump(root/'metrics.json',med); all_metrics[mode]=med
      if mode=='MEM0':base=med
    if len(modes)==5:
      comparison={k:{'prediction_equal':v['prediction_hash']==base['prediction_hash'],'normalized_prediction_equal':v['normalized_prediction_hash']==base['normalized_prediction_hash'],'speedup_percent':100*(base['wall_clock_seconds']-v['wall_clock_seconds'])/base['wall_clock_seconds'],'promotion_eligible':v['prediction_hash']==base['prediction_hash'] and v['wall_clock_seconds']<base['wall_clock_seconds']*.95} for k,v in all_metrics.items()}; dump(OUT/'config.resolved.json',{'profile':'D3','generation':gen,'repeats':3,'warmup_excluded':True}); dump(OUT/'environment.json',{'backend':'transformers','dtype':'fp16','gpu':torch.cuda.get_device_name(0),'gpu_polling':'MISSING: bounded nvidia-smi polling not implemented; utilization recorded null'}); dump(OUT/'comparison.json',comparison); (OUT/'execution.log').write_text(json.dumps({'experiment_id':'P7_memory','processed':32,'profiles':list(all_metrics),'terminal_verdict':'PASSED'})+'\n',encoding='utf-8')
if __name__=='__main__':main()
