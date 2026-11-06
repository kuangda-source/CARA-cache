#!/usr/bin/env python3
"""Capture the one original CPU terminal and native bytes; never launch work."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys

LAUNCH = Path('reports/wc_cfg_measurement_cpu_r1_launch_20261009.json')
PREFIX = 'reports/wc_cfg_measurement_cpu_r1_terminal_20261009_'


def main():
    launch = json.loads(LAUNCH.read_text())
    source = 'L=' + repr(launch) + '\n' + r'''
import base64,gzip,hashlib,json,pathlib,time
stage=pathlib.Path(L['stage']);root=stage.parent.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((stage/'receipt.json').read_text())
pids=[r['pid'],r.get('child_pid'),r.get('audit_child_pid')]
live=[p for p in pids if p and pathlib.Path('/proc/'+str(p)).exists()]
if live:
 print(json.dumps({'capture':{'status':'ORIGINAL_CPU_HANDLES_STILL_LIVE_NO_CAPTURE','live_PIDs':live,'CPU_status':r['status'],'GPU_submissions':0},'native':{}}));raise SystemExit(0)
assert r['pid']==L['supervisor_pid'] and r['source_revision']==L['source_revision']
reg=json.loads((stage/'collector-preregistration.json').read_text())
payload={name:sha(stage/name) for name in reg['payload_sha256']}
runtime={name:sha(root/'runtime'/name) for name in reg['runtime_source_sha256']}
assert len(payload)==44 and payload==reg['payload_sha256']==r['payload_after_sha256']
assert runtime==reg['runtime_source_sha256']==r['runtime_after_sha256']
assert r['GPU_submissions']==0 and r['CUDA_visible_devices']==''
assert r['budget_before_sha256']==r['budget_after_sha256']==L['budget_before_sha256']
assert sha(root/'reports/budget.json')==r['budget_after_sha256']
success=r['exit_code']==0
if success:
 assert r['status']=='MEASUREMENT_COLLECTOR_AND_INDEPENDENT_CPU_AUDIT_COMPLETE_NOT_GPU'
 assert r['core_exit_code']==r['audit_exit_code']==0
 assert sha(stage/'result.json')==r['result_sha256'] and sha(stage/'audit.json')==r['audit_sha256']
 result=json.loads((stage/'result.json').read_text());audit=json.loads((stage/'audit.json').read_text())
 assert result['successful_CFG_pairs']==audit['successful_CFG_pairs']==80
 assert audit['raw_tensors_reconstructed']==240 and audit['strict_repeat_groups']==40
 assert audit['separate_net_input_condition_witnesses_verified']==448 and audit['separate_solver_space_witnesses_verified']==152
 assert not result['CUDA_initialized'] and not audit['CUDA_initialized']
files={name:stage/name for name in ('receipt.json','launch.json','deployment.json','collector-preregistration.json','driver.log','core.log')}
for name in ('core-receipt.json','result.json','result.failure.json','audit.json','audit.log'):
 if (stage/name).exists():files[name]=stage/name
native={}
for name,p in files.items():
 raw=p.read_bytes();compressed=gzip.compress(raw,mtime=0)
 native[name]={'remote_path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'compressed_sha256':hashlib.sha256(compressed).hexdigest(),'gzip_base64':base64.b64encode(compressed).decode()}
capture={'status':'MEASUREMENT_ORIGINAL_CPU_TERMINAL_SUCCESS_NATIVE_CAPTURE' if success else 'MEASUREMENT_ORIGINAL_CPU_TERMINAL_FAILURE_SCOPE_RETAINED_NATIVE_CAPTURE','observed_unix':time.time(),'original_PIDs_absent':[p for p in pids if p],'source_revision':L['source_revision'],'stage':str(stage),'CPU_wall_seconds':r['CPU_wall_seconds'],'exit_code':r['exit_code'],'planned_full_scope':r['planned_full_scope'],'payload_files':44,'payload_after_sha256':payload,'runtime_after_sha256':runtime,'budget_sha256_unchanged':r['budget_after_sha256'],'GPU_submissions':0,'real_model_or_video_quality_claim':False}
print(json.dumps({'capture':capture,'native':native}))
'''
    call = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', 'gkd_minchen', 'python3 -'],
                          input=source, text=True, capture_output=True, timeout=55)
    if call.returncode:
        raise RuntimeError(call.stderr[-4000:])
    remote = json.loads(call.stdout)
    if not remote['native']:
        print(json.dumps(remote['capture'])); return 2
    capture = remote['capture']; dest = Path(PREFIX + 'capture.json')
    assert not dest.exists()
    verified = {}
    for name, item in remote['native'].items():
        compressed = base64.b64decode(item['gzip_base64'], validate=True)
        raw = gzip.decompress(compressed)
        assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256']
        assert hashlib.sha256(compressed).hexdigest() == item['compressed_sha256']
        target = Path(PREFIX + name + '.native.gz'); assert not target.exists()
        verified[name] = target, compressed
    capture['files'] = {}
    for name, (path, raw) in verified.items():
        path.write_bytes(raw)
        capture['files'][name] = {k: v for k, v in remote['native'][name].items() if k != 'gzip_base64'}
        capture['files'][name]['local_path'] = str(path)
    dest.write_text(json.dumps(capture, indent=2) + '\n')
    print(json.dumps({k: capture[k] for k in ('status','original_PIDs_absent','exit_code','CPU_wall_seconds','payload_files','GPU_submissions')}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
