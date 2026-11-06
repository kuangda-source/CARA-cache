#!/usr/bin/env python3
"""One bounded CPU invocation; immutable new stage, no polling or GPU submission."""
import base64
import hashlib
import json
import shlex
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FILES=['scripts/run_wc_scout_readonly_cpu_r1.py','src/wcomr/scout_diagnostics_r1.py',
       'plans/scouts_20261018/SCOUT_READONLY_CPU_PLAN.json']
PY='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'


def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--stage',default='/home/gaokuangda/data/gkd/worldcache_omr/.sync/wc-scout-readonly-cpu-r1-20261018')
    a=p.parse_args();assert not a.output.exists()
    rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    data,hashes={},{}
    for name in FILES:
        raw=(ROOT/name).read_bytes()
        assert raw==subprocess.check_output(['git','show',rev+':'+name],cwd=ROOT)
        data[name]=base64.b64encode(raw).decode();hashes[name]=hashlib.sha256(raw).hexdigest()
    packet=dict(stage=a.stage,files=data,registration=dict(source_revision=rev,payload_sha256=hashes,
        kind='ISOLATED_OLD_ASSETS_CPU_ONLY',GPU_submissions=0))
    boot=r'''
import base64,hashlib,json,os,pathlib,sys
v=json.loads(sys.stdin.buffer.read());stage=pathlib.Path(v['stage'])
assert stage.parent.resolve()==pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr/.sync').resolve()
assert stage.name.startswith('wc-scout-readonly-cpu-') and not stage.exists();stage.mkdir()
for name,b in v['files'].items():
 p=pathlib.PurePosixPath(name);assert not p.is_absolute() and '..' not in p.parts
 raw=base64.b64decode(b);assert hashlib.sha256(raw).hexdigest()==v['registration']['payload_sha256'][name]
 q=stage/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(raw)
(stage/'registration.json').write_text(json.dumps(v['registration'],indent=2)+'\n')
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
os.execv(sys.executable,[sys.executable,str(stage/'scripts/run_wc_scout_readonly_cpu_r1.py'),str(stage)])
'''
    started=time.time()
    r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes',
                      'gkd_minchen',PY+' -c '+shlex.quote(boot)],input=json.dumps(packet).encode(),
                     capture_output=True,timeout=180)
    try: result=json.loads(r.stdout)
    except ValueError: result=None
    receipt=dict(status='SCOUT_SAVED_CPU_ONCE_RETURNED',stage=a.stage,source_revision=rev,
        registration=packet['registration'],exit_code=r.returncode,result=result,
        stdout=r.stdout.decode(),stderr=r.stderr.decode(),elapsed_seconds=time.time()-started,
        SSH_calls=1,GPU_submissions=0,ledger_written=False,original_stages_written=False)
    a.output.write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(output=str(a.output),exit_code=r.returncode,
        result_status=(result or {}).get('status'),elapsed_seconds=receipt['elapsed_seconds'])))
    raise SystemExit(r.returncode or (0 if result is not None else 1))


if __name__=='__main__': main()
