"""Independently capture the original E5 GPU/CPU terminal chain and originals.

Refuses to declare a terminal result while any original GPU or reader handle
exists. It never launches a reader, imports Torch, writes a ledger or restarts
the experiment. The frozen automatic reader owns the actual tensor/frame pass.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess


REMOTE = r'''import base64,gzip,hashlib,json,pathlib,time
project=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr')
stage=project/'.sync/wc-e5-head-complete24-selected-r1-20261011'
root=project/'outputs/wc-e5-native-wrapped-head-full24-r1'
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for block in iter(lambda:stream.read(4<<20),b''):h.update(block)
 return h.hexdigest()
config=json.loads((stage/'e5-head-complete24-config.json').read_text())
launch=json.loads((stage/'GPU-launch.json').read_text())
sup=json.loads((root/'supervisor.json').read_text())
cpu=json.loads((stage/'terminal-CPU-supervisor.json').read_text())
source='eff2b71bbd888f4576a2c1c159c394d72ba62fe9'
assert sup['source_revision']==launch['source_revision']==cpu['source_revision']==source
assert sup['pid']==launch['GPU_supervisor_pid']==cpu['original_GPU_supervisor_pid']==4103103
assert cpu['pid']==launch['terminal_CPU_supervisor_pid']==4103104
ids=[sup['pid'],cpu['pid']]+[a['pid'] for a in sup['arms'] if 'pid' in a]
if 'child_pid' in cpu:ids.append(cpu['child_pid'])
live=[pid for pid in ids if pathlib.Path('/proc/'+str(pid)).exists()]
if live:
 print(json.dumps({'status':'WAIT_ORIGINAL_E5_GPU_OR_TERMINAL_CPU','original_live_pids':live,
  'GPU_status':sup['status'],'CPU_status':cpu['status'],'new_GPU_submissions':0,'observed_unix':time.time()}))
 raise SystemExit(0)
assert sha(stage/'e5-head-complete24-config.json')==launch['selected_config_sha256']==sup['config_sha256']
assert {n:sha(stage/n) for n in config['payload_sha256']}==config['payload_sha256']
assert len(config['payload_sha256'])==456
assert sha(stage/'production-CPU-receipt.json')==config['production_CPU_receipt_sha256']==sup['production_CPU_receipt_sha256']
assert cpu['exit_code']==0 and cpu['status']=='E5_TERMINAL_CPU_EXIT0_REQUIRES_INDEPENDENT_CAPTURE'
assert cpu['audit_source_sha256']==sha(stage/'scripts/audit_wc_e5_head_complete24_terminal_cpu_r1.py')
audit_path=stage/'real-GPU-audit.json'
assert sha(audit_path)==cpu['result_sha256']
audit=json.loads(audit_path.read_text());ledger=json.loads((project/'reports/budget.json').read_text())
assert audit['source_revision']==source and audit['original_supervisor']==sup
assert audit['registered_paths']==len(audit['path_slots'])==24
assert audit['CUDA_initialized'] is False and audit['new_GPU_submissions']==0
assert audit['clean_latency_or_quality_frontier_claim'] is False
assert cpu['GPU_submissions']==0 and cpu['ledger_written'] is False
assert cpu['budget_before_sha256']==cpu['budget_after_sha256']==audit['current_ledger_sha256']
assert audit['current_ledger']==sup['budget_after']
assert abs(audit['billed_GPUh']-sup['wall_seconds']/3600)<1e-12
assert abs(sup['budget_after']['used_gpu_hours']-sup['budget_before']['used_gpu_hours']-audit['billed_GPUh'])<1e-10
assert audit['billed_GPUh']<=8 and not any('inflight' in k for k in sup['budget_after'])
complete=audit['status']=='E5_WHOLE24_REAL_HEAD_EQUIVALENCE_CPU_AUDITED'
if complete:
 assert sup['complete_original_model_process_attempted'] and all(a['exit_code']==0 for a in sup['arms'])
 assert len(audit['actual_vector_files'])==24
 assert audit['actual_loaded_tensors']==888 and audit['actual_old_new_tensor_equalities']==444
 assert len(audit['same_version_order_repeats'])==12
 assert sum(x['actual_order_repeat_tensor_equalities'] for x in audit['same_version_order_repeats'])==444
 assert len(audit['actual_head_and_instrumented_wall_pairs'])==12
 for pair in audit['actual_head_and_instrumented_wall_pairs']:
  assert pair['actual_native_head_counts'][0]-pair['actual_native_head_counts'][1]==pair['saved_native_heads']
  assert pair['saved_native_heads']==0 if pair['mode']=='OFF' else pair['saved_native_heads']>0
else:
 assert audit['status']=='E5_PARTIAL_REAL_ATTEMPT_RETAINED_NOT_WHOLE_ACCEPTED'
for artifact in audit['actual_vector_files']+audit['actual_complete_videos']:
 p=pathlib.Path(artifact['path']).resolve();assert p.is_relative_to(root.resolve())
 assert p.stat().st_size==artifact['bytes'] and sha(p)==artifact['sha256']
originals={
 'GPU_supervisor':root/'supervisor.json','CPU_supervisor':stage/'terminal-CPU-supervisor.json',
 'audit':audit_path,'GPU_launch':stage/'GPU-launch.json',
 'selected_config':stage/'e5-head-complete24-config.json',
 'production_CPU_receipt':stage/'production-CPU-receipt.json'}
for arm in sup['arms']:
 p=root/arm['id']/'receipt.json'
 if p.exists():
  assert sha(p)==arm['receipt_sha256'];originals[arm['id']+'_receipt']=p
blobs={}
for name,path in originals.items():
 raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==sha(path)
 blobs[name]={'remote_path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
  'gzip_base64':base64.b64encode(gzip.compress(raw,mtime=0)).decode()}
assert sha(audit_path)==cpu['result_sha256']
print(json.dumps({'status':'E5_ORIGINAL_TERMINAL_CHAIN_INDEPENDENTLY_CAPTURED','source_revision':source,
 'original_PIDs_absent':ids,'whole24_equivalence_accepted':complete,'frozen_payload_files_unchanged':456,
 'actual_loaded_tensors':audit['actual_loaded_tensors'],'actual_old_new_tensor_equalities':audit['actual_old_new_tensor_equalities'],
 'actual_complete_videos':len(audit['actual_complete_videos']),
 'head_and_instrumented_wall_pairs':audit['actual_head_and_instrumented_wall_pairs'],
 'billed_GPUh':audit['billed_GPUh'],'settled_ledger':audit['current_ledger'],
 'current_ledger_observation':ledger,'observed_unix':time.time(),
 'new_GPU_submissions':0,'ledger_written':False,'originals':blobs}))
'''


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();assert not args.output.exists()
    root=Path(__file__).resolve().parents[1]
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen',
        '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'],
        input=REMOTE,text=True,capture_output=True)
    if result.returncode:raise RuntimeError(result.stderr[-3500:])
    value=json.loads(result.stdout)
    if value['status'].startswith('WAIT_'):
        print(json.dumps(value));return
    folder=root/'reports'/args.output.stem;assert not folder.exists();folder.mkdir()
    import gzip
    for name,entry in value['originals'].items():
        raw=base64.b64decode(entry.pop('gzip_base64'));plain=gzip.decompress(raw)
        assert len(plain)==entry['bytes'] and hashlib.sha256(plain).hexdigest()==entry['sha256']
        target=folder/(name+'.json.gz');target.write_bytes(raw)
        entry['local_path']=str(target);entry['local_gzip_sha256']=hashlib.sha256(raw).hexdigest()
    args.output.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:value[k] for k in ('status','whole24_equivalence_accepted','actual_loaded_tensors',
        'actual_old_new_tensor_equalities','actual_complete_videos','billed_GPUh')}))


if __name__=='__main__':main()
