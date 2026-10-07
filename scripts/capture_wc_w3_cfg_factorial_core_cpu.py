#!/usr/bin/env python3
"""Capture the original single CPU run, including any refusal; never launch."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    manifest = Path('manifests/wc_w3_cfg_factorial_core_cpu_r1_20261008.json')
    m = json.loads(manifest.read_text())
    remote = 'STAGE=' + repr(m['stage']) + '\n' + r'''
import base64,gzip,hashlib,json,pathlib,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/STAGE
r=json.loads((stage/'receipt.json').read_text())
assert r['status']!='CFG_FACTORIAL_CORE_CPU_RUNNING_NOT_GPU','Original CPU is still running'
assert all(not pathlib.Path('/proc/'+str(r[k])).exists() for k in ('pid','child_pid'))
files={}
for name in ('receipt.json','result.json','result.failure.json','check.log','driver.log','manifest.json','launch.json'):
 p=stage/name
 if p.exists():
  raw=p.read_bytes();data=gzip.compress(raw,mtime=0)
  files[name]={'raw_sha256':hashlib.sha256(raw).hexdigest(),'raw_bytes':len(raw),'gzip_base64':base64.b64encode(data).decode()}
print(json.dumps({'observed_unix':time.time(),'files':files,'driver_sha256':hashlib.sha256((stage/'driver.py').read_bytes()).hexdigest(),'live_budget_sha256':hashlib.sha256((root/'reports/budget.json').read_bytes()).hexdigest(),'PIDs_absent':[r[k] for k in ('pid','child_pid')]}))
'''
    response = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', 'gkd_minchen', 'python3 -'],
        input=remote, text=True, capture_output=True, timeout=50)
    if response.returncode:
        raise RuntimeError(response.stderr[-3000:])
    v = json.loads(response.stdout)
    out = {'status': 'CFG_FACTORIAL_ORIGINAL_CPU_TERMINAL_CAPTURE_NOT_GPU',
           'observed_unix': v['observed_unix'], 'original_PIDs_absent': v['PIDs_absent'],
           'original_driver_sha256': v['driver_sha256'], 'archives': {}, 'GPU_submissions': 0}
    native = {}
    for name, item in v['files'].items():
        data = base64.b64decode(item['gzip_base64']); raw = gzip.decompress(data)
        assert len(raw) == item['raw_bytes'] and hashlib.sha256(raw).hexdigest() == item['raw_sha256']
        dest = Path('reports/wc_w3_cfg_factorial_core_cpu_r1_20261008_' + name.replace('.', '_') + '_native.gz')
        with dest.open('xb') as f: f.write(data)
        out['archives'][str(dest)] = {'raw_bytes': len(raw), 'raw_sha256': item['raw_sha256'],
                                     'gzip_sha256': hashlib.sha256(data).hexdigest()}
        if name.endswith('.json'): native[name] = json.loads(raw)
    r = native['receipt.json']; launch = native['launch.json']
    assert v['driver_sha256'] == launch['driver_sha256']
    assert r['new_payload_after_sha256'] == m['payload_sha256']
    assert r['base_payload_after_sha256'] == r['staged_base_after_sha256'] == m['base_payload_sha256']
    assert r['budget_before_sha256'] == r['budget_after_sha256'] == v['live_budget_sha256'] == m['budget_sha256_before']
    out.update(source_revision=r['source_revision'], original_exit_code=r['exit_code'],
               budget_unchanged=True, actual_CPU_status=r['status'], original_CPU_wall_seconds=r['CPU_wall_seconds'])
    if r['exit_code'] == 0:
        assert hashlib.sha256(gzip.decompress(Path(next(n for n in out['archives'] if n.endswith('_result_json_native.gz'))).read_bytes())).hexdigest() == r['result_sha256']
    p = Path('reports/wc_w3_cfg_factorial_core_cpu_r1_20261008_terminal_capture.json')
    with p.open('x') as f: f.write(json.dumps(out, indent=2) + '\n')
    print(json.dumps({k: out[k] for k in ('status', 'original_exit_code', 'actual_CPU_status', 'original_CPU_wall_seconds')}))


if __name__ == '__main__': main()
