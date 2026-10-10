"""Read original production CPU handles and immutable sources, never re-execute."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    root=Path(__file__).resolve().parents[1]
    ref='reports/wc_e1_diag8_production_cpu_r1_launch_20261011.json';launch=json.loads((root/ref).read_text())
    packet={'launch':launch}
    code='P='+repr(packet)+'\n'+r'''import base64,gzip,hashlib,json,pathlib,time
L=P['launch'];s=pathlib.Path(L['stage']);root=s.parents[1]
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(4<<20),b''):h.update(chunk)
 return h.hexdigest()
r=json.loads((s/'production-CPU-receipt.json').read_text());pids=[r['pid'],r.get('child_pid')]
live=[p for p in pids if p and pathlib.Path('/proc/'+str(p)).exists()]
if live:print(json.dumps({'capture':{'status':'ORIGINAL_E1_PRODUCTION_CPU_LIVE','PIDs':live},'native':{}}));raise SystemExit(0)
assert r['pid']==L['supervisor_pid'] and r['source_revision']==L['source_revision']
c=json.loads((s/'e1-diag8-config.json').read_text());reg=json.loads((s/'registration.json').read_text())
assert sha(s/'e1-diag8-config.json')==L['config_sha256'] and sha(s/'registration.json')==L['registration_sha256']
assert {n:sha(s/n) for n in c['payload_sha256']}==c['payload_sha256']==r['payload_after_sha256']
assert {n:sha(root/c['parent_stage']/n) for n in c['parent_import_source_sha256']}==c['parent_import_source_sha256']
assert r['budget_before_sha256']==r['budget_after_sha256']==sha(root/'reports/budget.json')
assert r['GPU_submissions']==0 and not r['ledger_written'] and not c['GPU_execution_selected']
if r['exit_code']==0:
 assert r['child_exit_code']==0 and r['status']=='E1_DIAG8_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU'
 v=r['actual_entry_result'];assert not v['CUDA_initialized'] and len(v['contract_mutation_refusals'])==13
 assert len(v['registered_arm_derivations'])==4 and v['four_guardrail_less_entries_refused']
 assert len(r['admission_refusals'])==8 and len(r['protected_failure_classification_controls']['known_capacity'])==4
 assert len(r['protected_failure_classification_controls']['unexpected_stops_remaining_scope'])==4
 assert v['scope_counts']==c['scope_counts'] and v['payload_sha256']==c['payload_sha256']
capture={'status':'E1_DIAG8_ORIGINAL_ACTUAL_PRODUCTION_CPU_TERMINAL_NOT_GPU','source_revision':L['source_revision'],
 'original_PIDs_absent':pids,'exit_code':r['exit_code'],'CPU_wall_seconds':r['CPU_wall_seconds'],
 'payload_files':len(c['payload_sha256']),'original_parent_import_helpers':len(c['parent_import_source_sha256']),
 'GPU_submissions':0,'ledger_written':False,'budget_sha256':r['budget_after_sha256'],'observed_unix':time.time()}
native={}
for n in ('production-CPU-receipt.json','production-CPU.log','launch.json','driver.log','registration.json','e1-diag8-config.json'):
 raw=(s/n).read_bytes();packed=gzip.compress(raw,compresslevel=6,mtime=0)
 native[n]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'compressed_sha256':hashlib.sha256(packed).hexdigest(),
  'base64':base64.b64encode(packed).decode()}
print(json.dumps({'capture':capture,'native':native}))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],
        input=code,text=True,capture_output=True)
    if call.returncode:raise RuntimeError(call.stderr[-2800:])
    value=json.loads(call.stdout)
    if not value['native']:print(json.dumps(value['capture']));return 2
    prefix=root/'reports/wc_e1_diag8_production_cpu_r1_terminal_20261011_'
    target=Path(str(prefix)+'capture.json');assert not target.exists()
    proof=value['capture'];proof['files']={};objects={}
    for n,v in value['native'].items():
        packed=base64.b64decode(v['base64'],validate=True);raw=gzip.decompress(packed)
        assert hashlib.sha256(raw).hexdigest()==v['sha256'] and len(raw)==v['bytes']
        assert hashlib.sha256(packed).hexdigest()==v['compressed_sha256']
        path=Path(str(prefix)+n+'.native.gz');assert not path.exists();path.write_bytes(packed)
        proof['files'][n]={k:x for k,x in v.items() if k!='base64'};proof['files'][n]['local_path']=str(path.relative_to(root))
        if n.endswith('.json'):objects[n]=json.loads(raw)
    assert objects['launch.json']==launch
    reg=objects['registration.json'];assert reg==json.loads((root/'manifests/wc_e1_diag8_production_cpu_r1_preregistration_20261011.json').read_text())
    c=objects['e1-diag8-config.json'];assert c==json.loads((root/reg['config_ref']).read_text())
    for n in reg['new_local_files']:
        raw=subprocess.check_output(['git','show',launch['source_revision']+':'+n],cwd=root)
        assert hashlib.sha256(raw).hexdigest()==c['payload_sha256'][n],n
    proof['original_source_actual_entry_contract_and_wrapper_independently_verified']=True
    target.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({k:v for k,v in proof.items() if k!='files'}));return 0


if __name__=='__main__':raise SystemExit(main())
