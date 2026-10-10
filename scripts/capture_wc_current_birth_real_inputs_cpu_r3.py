#!/usr/bin/env python3
"""Capture one metadata CPU terminal and original byte/source bindings."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    launch = json.loads(Path('reports/wc_current_birth_real_inputs_cpu_r3_launch_20261010.json').read_text())
    code = 'L=' + repr(launch) + '\n' + r'''
import base64,gzip,hashlib,json,pathlib,time
stage=pathlib.Path(L['stage']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((stage/'receipt.json').read_text());pids=[r['pid'],r.get('child_pid')]
live=[p for p in pids if p and pathlib.Path('/proc/'+str(p)).exists()]
if live:
 print(json.dumps({'capture':{'status':'METADATA_CPU_STILL_LIVE','PIDs':live},'native':{}}));raise SystemExit(0)
assert r['pid']==L['supervisor_pid'] and r['source_revision']==L['source_revision']
assert sha(stage/'driver.py')==L['driver_sha256'] and sha(stage/'registration.json')==L['registration_sha256']
reg=json.loads((stage/'registration.json').read_text())
assert {n:sha(stage/n) for n in reg['source_sha256']}==r['payload_after_sha256']==reg['source_sha256']
assert sha(stage/'manifests/wc_current_birth_real_inputs_cpu_r3_preregistration_20261010.json')==L['registration_sha256']
assert r['GPU_submissions']==0 and not r['ledger_written'] and not r['CUDA_initialized']
assert r['budget_before_sha256']==r['budget_after_sha256']==sha(stage.parent.parent/'reports/budget.json')
names=['receipt.json','registration.json','driver.py','driver.log','test.log','launch.json']
result='reports/wc_current_birth_real_inputs_cpu_r3_results_20261010.json'
if (stage/result).exists():names.append(result)
native={}
for n in names:
 raw=(stage/n).read_bytes();packed=gzip.compress(raw,compresslevel=1,mtime=0)
 native[n]={'path':str(stage/n),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
  'compressed_sha256':hashlib.sha256(packed).hexdigest(),'base64':base64.b64encode(packed).decode()}
print(json.dumps({'capture':{'source_revision':L['source_revision'],'original_PIDs_absent':pids,
 'CPU_result_accepted':r['exit_code']==0,'exit_code':r['exit_code'],'GPU_submissions':0,'observed_unix':time.time()},'native':native}))
'''
    call = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', 'gkd_minchen', 'python3 -'],
        input=code, text=True, capture_output=True, timeout=55)
    if call.returncode:
        raise RuntimeError(call.stderr[-1500:])
    packet = json.loads(call.stdout)
    if not packet['native']:
        print(json.dumps(packet['capture'])); return 2
    prefix = 'reports/wc_current_birth_real_inputs_cpu_r3_terminal_20261010_'
    dest = Path(prefix + 'capture.json'); assert not dest.exists()
    proof = packet['capture']; proof['files'] = {}; objects = {}
    for name, item in packet['native'].items():
        packed = base64.b64decode(item['base64'], validate=True); raw = gzip.decompress(packed)
        assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
        assert hashlib.sha256(packed).hexdigest()==item['compressed_sha256']
        target = Path(prefix + name.replace('/', '__') + '.native.gz'); assert not target.exists()
        target.write_bytes(packed)
        proof['files'][name] = {k:v for k,v in item.items() if k!='base64'}
        proof['files'][name]['local_path'] = str(target)
        if name.endswith('.json'): objects[name] = json.loads(raw)
    reg = objects['registration.json']
    assert objects['launch.json']==launch
    original = subprocess.check_output(['git', 'show', launch['source_revision'] + ':manifests/wc_current_birth_real_inputs_cpu_r3_preregistration_20261010.json'])
    assert json.loads(original)==reg and hashlib.sha256(original).hexdigest()==launch['registration_sha256']
    for name, digest in reg['source_sha256'].items():
        assert hashlib.sha256(subprocess.check_output(['git','show',launch['source_revision']+':'+name])).hexdigest()==digest
    if proof['CPU_result_accepted']:
        value=objects['reports/wc_current_birth_real_inputs_cpu_r3_results_20261010.json']
        assert value['source_sha256']==reg['source_sha256']
        assert (value['complete_method_parameter_sets'],value['actual_Native_file_sizes_and_hashes_verified'])==(16,4)
        assert len(value['fixture_API_required_exports_verified'])==7
        assert value['evidence']['complete_cost_rows']==48 and value['evidence']['timed_values']==144
        assert value['Torch_imported'] and not value['CUDA_initialized'] and not value['model_or_controller_installed']
        assert value['GPU_submissions']==0 and value['new_trajectory_compatibility_pending']
        proof['CPU_wall_seconds']=value['CPU_wall_seconds']
        proof['complete_source_scope_and_real_files_verified']=True
    dest.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({k:v for k,v in proof.items() if k!='files'})); return 0


if __name__=='__main__': raise SystemExit(main())
