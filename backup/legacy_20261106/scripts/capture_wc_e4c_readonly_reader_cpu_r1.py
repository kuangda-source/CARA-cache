"""Independent original handles, source and complete CPU receipt capture."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    root=Path(__file__).resolve().parents[1]
    launch=json.loads((root/'reports/wc_e4c_readonly_reader_cpu_r1_launch_20261011.json').read_text())
    code='P='+repr(launch)+'\n'+r'''import base64,gzip,hashlib,json,pathlib,time
s=pathlib.Path(P['stage']);r=json.loads((s/'receipt.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pids=[r['pid'],r['child_pid']];live=[i for i in pids if pathlib.Path('/proc/'+str(i)).exists()]
if live:print(json.dumps({'status':'WAIT_ORIGINAL_READONLY_CPU_HANDLES','live':live}));raise SystemExit(0)
assert r['pid']==P['supervisor_pid'] and r['source_revision']==P['source_revision']
assert r['exit_code']==r['child_exit_code']==0 and r['original_source_unchanged']
assert r['budget_before_sha256']==r['budget_after_sha256'] and not r['GPU_submissions'] and not r['ledger_written']
assert sha(s/'registration.json')==P['registration_sha256'] and sha(s/'result.json')==r['result_sha256']
reg=json.loads((s/'registration.json').read_text());old=s.parents[1]/reg['original_stage']
assert {n:sha(s/n) for n in reg['new_payload_sha256']}==reg['new_payload_sha256']==r['source_after_sha256']
assert {n:sha(old/n) for n in reg['original_payload_sha256']}==reg['original_payload_sha256']
assert sha(old/'receipt.json')==reg['original_receipt_sha256'] and sha(old/'result.json')==reg['original_result_sha256']
v=json.loads((s/'result.json').read_text())
assert (v['actual_files_reloaded'],v['actual_tensors_reloaded'],v['actual_direct_tensor_comparisons'],v['actual_points_summarized'])==(88,776,324,48)
assert len(v['checks'])==2 and all(len(c['summary']['matched_birth_age_comparisons'])==12 and len(c['summary']['points'])==24 and len(c['scope_refusals'])==4 for c in v['checks'])
assert not v['CUDA_initialized'] and not v['physical_sampling_or_native_meta_rerun']
native={}
for n in ('receipt.json','registration.json','result.json','CPU.log','supervisor.log','launch.json'):
 raw=(s/n).read_bytes();z=gzip.compress(raw,mtime=0)
 native[n]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'compressed_sha256':hashlib.sha256(z).hexdigest(),'base64':base64.b64encode(z).decode()}
print(json.dumps({'status':'E4C_READONLY_CPU_READER_ORIGINAL_TERMINAL_INDEPENDENTLY_CAPTURED','original_handles_absent':pids,
 'receipt':r,'observed_unix':time.time(),'native':native}))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen',
        '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'],input=code,text=True,capture_output=True)
    if call.returncode:raise RuntimeError(call.stderr[-3000:])
    v=json.loads(call.stdout)
    if 'native' not in v:print(json.dumps(v));return 2
    target=root/'reports/wc_e4c_readonly_reader_cpu_r1_terminal_20261011_capture.json';assert not target.exists();v['files']={}
    for n,item in v.pop('native').items():
        z=base64.b64decode(item.pop('base64'),validate=True);raw=gzip.decompress(z)
        assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'] and hashlib.sha256(z).hexdigest()==item['compressed_sha256']
        p=root/'reports'/('wc_e4c_readonly_reader_cpu_r1_terminal_20261011_'+n+'.native.gz');assert not p.exists();p.write_bytes(z)
        v['files'][n]={**item,'local_path':str(p.relative_to(root))}
    target.write_text(json.dumps(v,indent=2)+'\n')
    print(json.dumps({'status':v['status'],'exit_code':v['receipt']['exit_code'],'CPU_wall_seconds':v['receipt']['CPU_wall_seconds']}));return 0


if __name__=='__main__':raise SystemExit(main())
