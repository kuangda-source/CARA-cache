#!/usr/bin/env python3
"""Fresh immutable production CPU stage after real N09 config/quote selection."""
import argparse
import gzip
import io
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
PYTHON = '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
ENTRYPOINTS = (
    'scripts/deploy_wc_drop1_window24_cpu_r1.py', 'scripts/run_wc_drop1_window24_cpu_bundle_r1.py',
    'scripts/run_wc_drop1_window24_r1.py', 'scripts/postprocess_wc_drop1_window24_r1.py',
    'scripts/supervise_wc_drop1_window24_r1.py', 'scripts/watch_wc_drop1_window24_post_cpu_r1.py',
    'scripts/capture_wc_drop1_window24_cpu_r1.py', 'src/wcomr/drop1_window24_production_r1.py',
)
EXTRA = (
    'scripts/run_wc_drop1_full18_r1.py', 'scripts/postprocess_wc_drop1_full18_r1.py',
    'scripts/capture_wc_drop1_window88_cpu_r1.py',
    'manifests/wc_paper_N09_runtime_profile40_scope_r1_20261016.json',
    'plans/WC_DROP1_WINDOW24_PRODUCTION_PRICING_AND_ACCEPTANCE_20261018.md',
)


def packet_plan(root, config_ref, numeric_capture):
    from wcomr.immutable_stage_payload_r1 import plan
    from wcomr.drop1_window24_cpu_acceptance_r1 import PATTERNS
    base = numeric_capture['registration']
    value = plan(root, config_roots=[config_ref], python_entrypoints=ENTRYPOINTS,
        extra_files=list(EXTRA)+['tests/'+p for p in PATTERNS],
        base_registration_sha256=numeric_capture['registration_sha256'],
        base_source_revision=base['source_revision'], numeric_sources={})
    changed = [n for n,h in value['overlay_sha256'].items()
               if n in base['payload_sha256'] and h != base['payload_sha256'][n]]
    if changed:
        raise ValueError('Never overwrite a registered numerical88 base file: '+str(changed))
    return value


BOOT = r'''
import hashlib,io,json,os,pathlib,subprocess,sys,tarfile,time
sys.dont_write_bytecode=True
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve()
for key in ('base','stage'):
 p=pathlib.PurePosixPath(M[key]);assert not p.is_absolute() and '..' not in p.parts and len(p.parts)==2 and p.parts[0]=='.sync'
base=root/M['base'];stage=root/M['stage']
pool=json.loads((root/'reports/gpu-budget-v2.json').read_text())
assert not any(k=='wc-paper-n09-runtime-profile40-r1' and v['status']=='RESERVED_OR_RUNNING' for k,v in pool['jobs'].items()),'No heavy CPU during N09 profiling'
module='src/wcomr/immutable_stage_payload_r1.py'
with tarfile.open(fileobj=io.BytesIO(ARCHIVE),mode='r:gz') as a:
 matches=[m for m in a if m.name==module];assert len(matches)==1 and matches[0].isfile()
 raw=a.extractfile(matches[0]).read()
assert hashlib.sha256(raw).hexdigest()==M['plan']['overlay_sha256'][module]
ns={};exec(compile(raw,'GIT_BOUND_WINDOW24_IMMUTABLE_INSTALLER','exec'),ns)
reg=ns['install'](base,stage,ARCHIVE,M['plan'],source_revision=M['revision'],cpu_scope='FULL24_REAL_PRODUCTION_WITH_UNCHANGED_COMPLETE88')
old=root/'.sync/wc-drop1-production-r1-20261017'
assert hashlib.sha256((old/'registration.json').read_bytes()).hexdigest()=='2532bde9cc5ba858ac3018f3bbe82e88be2e459b8e5e985734c78659f42bc134'
assert json.loads((old/'registration.json').read_text())['source_revision']=='e76b4f8b934bb07bf045e6083f36eddb4711640d'
aux={}
for n in ('simple26d-sampling-CPU-result.json','simple26d-memory-sampling-CPU-result.json'):
 raw=(old/n).read_bytes();assert not (stage/n).exists();(stage/n).write_bytes(raw)
 aux[n]=dict(source_stage=str(old),sha256=hashlib.sha256(raw).hexdigest())
 reg['payload_sha256'][n]=aux[n]['sha256']
reg['read_only_auxiliary_CPU_proofs']=aux
(stage/'registration.json').write_text(json.dumps(reg,indent=2,allow_nan=False)+'\n')
sys.path.insert(0,str(stage/'src'))
from wcomr.gpu_budget_pool_v2 import process_identity
with (stage/'window24-CPU-launch-request.json').open('x') as h:json.dump(dict(source_revision=M['revision'],requested_unix=time.time()),h)
command=[sys.executable,str(stage/'scripts/run_wc_drop1_window24_cpu_bundle_r1.py'),'--project',str(root),'--stage',str(stage)]
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
with (stage/'window24-CPU-bundle.log').open('xb') as log:
 child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=env)
identity=process_identity(child.pid);assert identity['state'] not in (None,'Z','X') and 'run_wc_drop1_window24_cpu_bundle_r1.py' in identity['command']
now=time.time()
value=dict(status='WINDOW24_REAL_PRODUCTION_CPU_SINGLE_DISPATCHED',source_revision=M['revision'],project=str(root),stage=str(stage),identity=identity,
 registration_sha256=hashlib.sha256((stage/'registration.json').read_bytes()).hexdigest(),payload_files=len(reg['payload_sha256']),
 command=command,started_unix=now,halfway_not_before_unix=now+180,final_not_before_unix=now+360,
 scope_counts=M['counts'],original_stage_written=False,GPU_submissions=0,ledger_written=False)
with (stage/'window24-CPU-launch.json').open('x') as h:json.dump(value,h,indent=2,allow_nan=False);h.write('\n')
print(json.dumps(value,allow_nan=False))
'''


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Never replay the original CPU dispatch')
    sys.path.insert(0,str(ROOT/'src'))
    from wcomr.drop1_window24_production_r1 import CONFIG, COUNTS, validate_contract
    from wcomr.immutable_stage_payload_r1 import relative, git_archive, registered_base_reference
    relative(a.stage)
    if len(Path(a.stage).parts)!=2 or not a.stage.startswith('.sync/wc-drop1-window24-production-cpu-'):
        raise ValueError('Fresh independent window24 production CPU stage required')
    config=json.loads((ROOT/CONFIG).read_text());validate_contract(config)
    numeric_ref=config['references']['numeric_capture'];raw=(ROOT/numeric_ref['ref']).read_bytes()
    assert __import__('hashlib').sha256(raw).hexdigest()==numeric_ref['sha256']
    numeric=json.loads(gzip.decompress(raw));value=packet_plan(ROOT,CONFIG,numeric)
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    archive=git_archive(ROOT,value,revision)
    base=registered_base_reference(numeric['registration']['stage'],numeric['launch']['stage'])
    meta=dict(base=base['project_relative'],stage=a.stage,revision=revision,plan=value,counts=COUNTS)
    code='M='+repr(meta)+'\nARCHIVE=__import__("sys").stdin.buffer.read()\n'+BOOT
    try:
        call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes',
            'gkd_minchen',PYTHON+' -c '+shlex.quote(code)],input=archive,capture_output=True,timeout=180)
        if call.returncode:raise RuntimeError(call.stderr.decode(errors='replace'))
        launch=json.loads(call.stdout)
    except (OSError,subprocess.TimeoutExpired,RuntimeError,ValueError) as e:
        result=dict(status='WINDOW24_CPU_DISPATCH_UNKNOWN_OR_FAILURE_NO_AUTOMATIC_REPLAY',stage=a.stage,
            source_revision=revision,error_type=type(e).__name__,error=str(e),original_task_terminal=False,
            original_recovery_ref=a.stage+'/window24-CPU-launch.json',GPU_submissions=0,ledger_written=False)
        with a.output.open('x') as h:json.dump(result,h,indent=2);h.write('\n')
        raise
    result=dict(status='WINDOW24_PRODUCTION_CPU_DISPATCH_RESPONSE',launch=launch,overlay_plan=value,
        source_revision=revision,GPU_submissions=0,ledger_written=False)
    with a.output.open('x') as h:json.dump(result,h,indent=2,allow_nan=False);h.write('\n')
    print(json.dumps(launch))


if __name__=='__main__':main()
