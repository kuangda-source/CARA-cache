#!/usr/bin/env python3
"""One CPU-only read of the preregistered six saved warm artifacts."""
import argparse
import base64
import hashlib
import json
import shlex
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY = '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
REMOTE = '/home/gaokuangda/data/gkd/worldcache_omr/.sync/'
WORKER = 'scripts/analyze_wc_drop1_saved_warm21_cpu_r1.py'
FILES = [WORKER, 'src/wcomr/drop1_warm21_analysis_r1.py',
         'plans/WC_N12_SAVED_WARM_STEP21_CPU_ANALYSIS_20261017.md',
         'manifests/wc_drop1_saved_warm_step21_CPU_plan_20261017.json',
         'reports/wc_drop1_full18_terminal_collection_20261018_0001.json.gz',
         'reports/wc_drop1_full18_independent_acceptance_20261018.json',
         'reports/wc_drop1_saved_warm21_math_local_CPU_preparation_20261017.json']


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--stage', default=REMOTE + 'wc-drop1-saved-warm21-cpu-r1-20261018')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    assert a.stage.startswith(REMOTE) and Path(a.stage).name.startswith('wc-drop1-saved-warm21-cpu-')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    data, hashes = {}, {}
    for name in FILES:
        raw = (ROOT / name).read_bytes()
        committed = subprocess.check_output(['git', 'show', revision + ':' + name], cwd=ROOT)
        assert raw == committed, name + ' is not the committed source'
        hashes[name] = hashlib.sha256(raw).hexdigest()
        data[name] = base64.b64encode(raw).decode()
    registration = dict(status='SAVED_WARM21_READONLY_CPU_SOURCE', source_revision=revision,
                        payload_sha256=hashes, GPU_submissions=0, ledger_written=False,
                        original_stage_written=False, new_generator_runs=0)
    packet = dict(stage=a.stage, registration=registration, files=data)
    boot = r'''
import base64,hashlib,json,os,pathlib,sys
v=json.loads(sys.stdin.buffer.read());stage=pathlib.Path(v['stage'])
assert stage.parent.resolve()==pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr/.sync').resolve()
assert not stage.exists();stage.mkdir()
for name,b in v['files'].items():
 p=pathlib.PurePosixPath(name);assert not p.is_absolute() and '..' not in p.parts
 raw=base64.b64decode(b);assert hashlib.sha256(raw).hexdigest()==v['registration']['payload_sha256'][name]
 out=stage/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw)
(stage/'registration.json').write_text(json.dumps(v['registration'],indent=2)+'\n')
os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='2')
os.execv(sys.executable,[sys.executable,str(stage/'scripts/analyze_wc_drop1_saved_warm21_cpu_r1.py'),'--stage',str(stage)])
'''
    start = time.time()
    r = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', '-o', 'ClearAllForwardings=yes',
                        'gkd_minchen', PY + ' -c ' + shlex.quote(boot)],
                       input=json.dumps(packet).encode(), capture_output=True, timeout=180)
    receipt = dict(status='SAVED_WARM21_SINGLE_CPU_READ_PROCESS_RETURNED', source_revision=revision,
                   stage=a.stage, registration=registration, exit_code=r.returncode,
                   stdout=r.stdout.decode(), stderr=r.stderr.decode(), elapsed_seconds=time.time() - start,
                   SSH_calls=1, GPU_submissions=0, ledger_written=False, original_stage_written=False)
    try:
        receipt['result'] = json.loads(r.stdout)
    except ValueError:
        receipt['result'] = None
    a.output.write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    result = receipt['result'] or {}
    print(json.dumps(dict(output=str(a.output), exit_code=r.returncode, accepted=result.get('accepted'),
                         errors=result.get('errors'), rounds=result.get('rounds'),
                         CPU_wall_seconds=result.get('CPU_wall_seconds')), allow_nan=False))
    raise SystemExit(r.returncode or (0 if result.get('accepted') else 1))


if __name__ == '__main__':
    main()
