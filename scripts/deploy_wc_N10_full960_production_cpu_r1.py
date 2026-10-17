#!/usr/bin/env python3
"""One immutable actual full960 contract CPU, preserving all244 model sources."""
import argparse
import gzip
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
PYTHON='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
CONFIG_REF='configs/wc_paper_N10_full960_production_r1_20261018.json'
MODEL_CAPTURE='reports/wc_paper_N10_full_five_model_CPU_R2_collection_20261018_0230.json.gz'
ENTRIES=('scripts/deploy_wc_N10_full960_production_cpu_r1.py','scripts/run_wc_N10_production_cpu_bundle_r1.py',
 'scripts/score_wc_paper_N10_full960_r1.py','scripts/supervise_wc_paper_N10_full960_r1.py',
 'scripts/capture_wc_N10_production_cpu_r1.py','scripts/accept_wc_N10_models_cpu_r1.py')
BOOT=r'''
import hashlib,json,pathlib,os,subprocess,sys,time
sys.dont_write_bytecode=True
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve()
for name in ('base','stage'):
 p=pathlib.PurePosixPath(M[name]);assert not p.is_absolute() and '..' not in p.parts and len(p.parts)==2 and p.parts[0]=='.sync'
base=root/M['base'];stage=root/M['stage']
assert stage.name.startswith('wc-paper-n10-full960-production-cpu-')
pool=json.loads((root/'reports/gpu-budget-v2.json').read_text())
assert not any(j['status']=='RESERVED_OR_RUNNING' for j in pool['jobs'].values()),'Complete contract CPU before any own GPU benchmark'
import io,tarfile
module='src/wcomr/immutable_stage_payload_r1.py'
with tarfile.open(fileobj=io.BytesIO(ARCHIVE),mode='r:gz') as a:
 m=[x for x in a if x.name==module];assert len(m)==1 and m[0].isfile();raw=a.extractfile(m[0]).read()
assert hashlib.sha256(raw).hexdigest()==M['plan']['overlay_sha256'][module]
ns={};exec(compile(raw,'GIT_BOUND_N10_IMMUTABLE_INSTALLER','exec'),ns)
reg=ns['install'](base,stage,ARCHIVE,M['plan'],source_revision=M['revision'],
 cpu_scope='FROZEN_N10_FULL960_PRODUCTION_CPU_PREPARATION_NO_GPU')
raw=(stage/M['config_ref']).read_bytes();assert hashlib.sha256(raw).hexdigest()==M['config_sha256']
assert not (stage/'N10-production-config.json').exists()
(stage/'N10-production-config.json').write_bytes(raw)
reg['payload_sha256']['N10-production-config.json']=M['config_sha256']
reg.update(purpose='N10_COMPLETE160_SIX_DIMENSION960_ORIGINAL_METRIC_SCORING',
 priced_config_source_ref=M['config_ref'],priced_config_alias='N10-production-config.json')
(stage/'registration.json').write_text(json.dumps(reg,indent=2,allow_nan=False)+'\n')
sys.path.insert(0,str(stage/'src'))
from wcomr.gpu_budget_pool_v2 import process_identity
command=[sys.executable,str(stage/'scripts/run_wc_N10_production_cpu_bundle_r1.py'),'--project',str(root),'--stage',str(stage)]
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONPATH=str(stage/'src'),PYTHONDONTWRITEBYTECODE='1',
 OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
with (stage/'production-CPU.log').open('xb') as log:
 child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
identity=process_identity(child.pid);assert identity['state'] not in (None,'Z','X')
assert 'run_wc_N10_production_cpu_bundle_r1.py' in identity['command']
now=time.time();launch=dict(status='N10_FULL960_QUOTED_PRODUCTION_CPU_SINGLE_DISPATCHED',project=str(root),stage=str(stage),
 source_revision=M['revision'],registration_sha256=hashlib.sha256((stage/'registration.json').read_bytes()).hexdigest(),
 config_sha256=M['config_sha256'],identity=identity,command=command,started_unix=now,
 halfway_not_before_unix=now+60,final_not_before_unix=now+150,payload_files=len(reg['payload_sha256']),
 scope_counts=M['scope_counts'],forecast_GPUh=4.915,billed_limit_GPUh=6.25,GPU_submissions=0,ledger_written=False)
with (stage/'N10-production-CPU-launch.json').open('x') as h:json.dump(launch,h,indent=2,allow_nan=False);h.write('\n')
print(json.dumps(launch,allow_nan=False))
'''


def packet():
    from wcomr.immutable_stage_payload_r1 import plan
    from wcomr.automatic_quality_production_cpu_r1 import PATTERNS
    cap=json.loads(gzip.decompress((ROOT/MODEL_CAPTURE).read_bytes()));base=cap['registration']
    value=plan(ROOT,config_roots=[CONFIG_REF],python_entrypoints=ENTRIES,
        extra_files=[MODEL_CAPTURE,'plans/WC_N10_FULL960_ENGINEERING_BUDGET_PREREG_R1_20261018.md']+
            ['tests/'+n for n in PATTERNS]+['tests/test_automatic_quality_r1.py'],base_registration_sha256=cap['registration_sha256'],
        base_source_revision=base['source_revision'],numeric_sources={})
    conflicts=[n for n,h in value['overlay_sha256'].items() if n in base['payload_sha256'] and h!=base['payload_sha256'][n]]
    if conflicts:raise ValueError('Preserve every original244 CPU model source: '+str(conflicts))
    return value,cap


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Never repeat an original CPU dispatch')
    sys.path.insert(0,str(ROOT/'src'))
    from wcomr.immutable_stage_payload_r1 import relative,git_archive,registered_base_reference
    from wcomr.automatic_quality_models_r1 import sha
    relative(a.stage)
    if not a.stage.startswith('.sync/wc-paper-n10-full960-production-cpu-') or len(Path(a.stage).parts)!=2:
        raise ValueError('One fresh independent N10 full960 stage required')
    value,cap=packet();revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    archive=git_archive(ROOT,value,revision);config=json.loads((ROOT/CONFIG_REF).read_text())
    base=registered_base_reference(cap['registration']['stage'],cap['launch']['stage'])
    m=dict(base=base['project_relative'],stage=a.stage,revision=revision,plan=value,config_ref=CONFIG_REF,
        config_sha256=sha(ROOT/CONFIG_REF),scope_counts=config['scope_counts'])
    code='M='+repr(m)+'\nARCHIVE=__import__("sys").stdin.buffer.read()\n'+BOOT
    try:
        call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes',
            'gkd_minchen',PYTHON+' -c '+shlex.quote(code)],input=archive,capture_output=True,timeout=180)
        if call.returncode:raise RuntimeError(call.stderr.decode(errors='replace'))
        launch=json.loads(call.stdout)
    except (OSError,subprocess.TimeoutExpired,RuntimeError,ValueError) as e:
        failure=dict(status='N10_PRODUCTION_CPU_DISPATCH_UNKNOWN_OR_FAILURE_NO_REPLAY',source_revision=revision,
            stage=a.stage,error_type=type(e).__name__,error=str(e),original_task_terminal=False,
            original_recovery_ref=a.stage+'/N10-production-CPU-launch.json',GPU_submissions=0,ledger_written=False)
        with a.output.open('x') as h:json.dump(failure,h,indent=2);h.write('\n')
        raise
    result=dict(launch=launch,source_revision=revision,overlay_plan=value,GPU_submissions=0,ledger_written=False)
    with a.output.open('x') as h:json.dump(result,h,indent=2,allow_nan=False);h.write('\n')
    print(json.dumps(launch))


if __name__=='__main__':main()
