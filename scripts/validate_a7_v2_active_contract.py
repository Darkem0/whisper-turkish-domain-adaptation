import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def h(p):return hashlib.sha256((R/p).read_bytes()).hexdigest()
t=json.loads((R/'contracts/A7_v2_training_contract.yaml').read_text());d=json.loads((R/'contracts/A7_v2_data_manifest.lock.json').read_text());s=json.loads((R/t['data']['schedule_lock']).read_text())
assert t['augmentation_policy']['version']=='A7_AUGMENTATION_POLICY_V3_UNIVERSAL_PEAK_GUARD'
assert h(t['data']['schedule'])==d['schedule']['sha256']==s['schedule_sha256']
assert h(t['data']['augmentation_assignment'])==d['schedule']['v3_assignment_sha256']==s['assignment_sha256']
assert h(t['data']['schedule_lock'])==d['schedule']['v3_lock_sha256']
assert h('src/whisper_arge/a7_augmentation.py')==d['schedule']['v3_implementation_sha256']==s['implementation_sha256']
assert s['schedule_rows']==3200 and sum(s['bucket_counts'].values())==3200
assert h('runs/A2_v2d_200/adapter/adapter_model.safetensors')==t['initialization']['parent_adapter_sha256']
print(json.dumps({'status':'PASSED','policy':t['augmentation_policy']['version']}))
