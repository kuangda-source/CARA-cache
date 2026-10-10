#!/usr/bin/env python3
"""Copy frozen620 into a selected CPU stage only after exact complete64 approval."""
import hashlib,json
from pathlib import Path
import subprocess

DRIVER = "import hashlib,json,os,pathlib,subprocess,sys,time\nstage=pathlib.Path(sys.argv[1]);root=stage.parent.parent\nsha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()\nc=json.loads((stage/'current-birth-full64-config.json').read_text())\nassert c['GPU_execution_selected'] and isinstance(c['single_job_exception_authority'],dict)\nr={'status':'CURRENT_BIRTH_FULL64_SELECTED_CPU_RUNNING_NOT_GPU','pid':os.getpid(),\n 'source_revision':sys.argv[2],'started_unix':time.time(),'GPU_submissions':0,\n 'CUDA_initialized':False,'ledger_written':False,'GPU_lock_acquired':False,\n 'budget_before_sha256':sha(root/'reports/budget.json'),'payload_sha256':c['payload_sha256']}\ndef save():\n p=stage/'receipt.json';t=p.with_suffix('.tmp');t.write_text(json.dumps(r,indent=2)+chr(10));t.replace(p)\nassert not (stage/'receipt.json').exists();save();start=time.perf_counter()\ntry:\n assert {n:sha(stage/n) for n in c['payload_sha256']}==c['payload_sha256']\n env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_CACHE=str(root/'hfhub'),HF_HUB_OFFLINE='1',\n  TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')\n cmd=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python',\n  str(stage/'scripts/run_wc_current_birth_full64_r1.py'),'--project',str(root),'--stage',str(stage),'--cpu-check']\n with (stage/'test.log').open('x') as log:\n  child=subprocess.Popen(cmd,cwd=root/'runtime',env=env,stdout=log,stderr=subprocess.STDOUT)\n  r['child_pid']=child.pid;save();r['child_exit_code']=child.wait()\n assert r['child_exit_code']==0\n candidates=[]\n for line in (stage/'test.log').read_text().splitlines():\n  if line.startswith('{'):\n   try:v=json.loads(line)\n   except ValueError:continue\n   if v.get('status')=='CURRENT_BIRTH_FULL64_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU':candidates.append(v)\n assert len(candidates)==1;v=candidates[0]\n assert not v['CUDA_initialized'] and v['GPU_submissions']==0\n assert v['registered_scope']==c['preregistration']['scope_counts'] and v['payload_sha256']==c['payload_sha256']\n assert v['complete_method_parameter_sets']==16 and v['guardrail_less_entry_refused_both_strategies']\n (stage/'result.json').write_text(json.dumps(v,indent=2)+chr(10))\n r.update(status='CURRENT_BIRTH_FULL64_SELECTED_CPU_PASS_NOT_GPU',exit_code=0,\n  result_sha256=sha(stage/'result.json'),config_binding_sha256=v['config_binding_sha256'],\n  production_contract_mutation_refusals=v['production_contract_mutation_refusals'])\nexcept BaseException as error:r.update(status='CURRENT_BIRTH_FULL64_SELECTED_CPU_FAILED_COMPLETE_SCOPE_RETAINED',\n exit_code=1,error_type=type(error).__name__,error=str(error))\nfinally:\n r.update(CPU_wall_seconds=time.perf_counter()-start,ended_unix=time.time(),\n  budget_after_sha256=sha(root/'reports/budget.json'),payload_after_sha256={n:sha(stage/n) for n in c['payload_sha256']})\n if r['payload_after_sha256']!=c['payload_sha256']:r.update(status='FULL64_PRODUCTION_CPU_SOURCE_CHANGED',exit_code=1)\n if r['budget_after_sha256']!=r['budget_before_sha256']:r.update(status='FULL64_PRODUCTION_CPU_BUDGET_CHANGED',exit_code=1)\n save()\nraise SystemExit(r['exit_code'])\n"


def main():
    config_ref=Path('configs/wc_current_birth_full64_selected_r1_20261010.json')
    if not config_ref.exists():
        print(json.dumps({'status':'WAIT_EXACT_FULL64_AUTHORITY_AND_SELECTION_NO_DEPLOYMENT','GPU_submissions':0}));return 2
    c=json.loads(config_ref.read_text());assert c['GPU_execution_selected']
    source_ref=c['single_job_exception_authority']['ref'];source=Path(source_ref)
    authorized=json.loads(source.read_text())
    assert authorized['direct_user_authorization'] and authorized['card']==c['preregistration']['card']
    assert authorized['run_id']==c['execution_run_id'] and authorized['scope_counts']==c['preregistration']['scope_counts']
    assert authorized['preregistration_sha256']==c['preregistration_sha256']
    assert authorized['forecast_complete_GPUh']==c['preregistration']['forecast']['forecast_complete_GPUh']
    assert hashlib.sha256(source.read_bytes()).hexdigest()==c['single_job_exception_authority']['sha256']
    revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    for path in (config_ref,source):assert path.read_bytes()==subprocess.check_output(['git','show',revision+':'+str(path)])
    proof=json.loads(Path('reports/wc_current_birth_full64_production_cpu_r1_terminal_20261010_capture.json').read_text())
    assert proof['exit_code']==0 and proof['independent_complete_source_contract_and_fixed_inputs_verified']
    launch_ref=Path('reports/wc_current_birth_full64_selected_cpu_r1_launch_20261010.json');assert not launch_ref.exists()
    packet={'config':config_ref.read_text(),'config_sha256':hashlib.sha256(config_ref.read_bytes()).hexdigest(),
        'authority_ref':source_ref,'authority':source.read_text(),'authority_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'source_revision':revision,'driver':DRIVER,'driver_sha256':hashlib.sha256(DRIVER.encode()).hexdigest(),
        'original_production_receipt_sha256':c['production_cpu_receipt_sha256'],'payload_sha256':c['payload_sha256']}
    code='P='+repr(packet)+'\n'+r"""
import hashlib,json,os,pathlib,subprocess,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');old=root/'.sync/wc-current-birth-full64-production-cpu-r1-20261010'
stage=root/'.sync/wc-current-birth-full64-selected-cpu-r1-20261010';assert not stage.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((old/'receipt.json').read_text())
assert sha(old/'receipt.json')==P['original_production_receipt_sha256'] and r['exit_code']==0
assert all(not pathlib.Path('/proc/'+str(r[k])).exists() for k in ('pid','child_pid'))
assert {n:sha(old/n) for n in P['payload_sha256']}==P['payload_sha256']
a=pathlib.PurePosixPath(P['authority_ref']);assert not a.is_absolute() and '..' not in a.parts
stage.mkdir()
for n,value in P['payload_sha256'].items():
 raw=(old/n).read_bytes();assert hashlib.sha256(raw).hexdigest()==value
 target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
(stage/'current-birth-full64-config.json').write_text(P['config'])
target=stage/P['authority_ref'];assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True);target.write_text(P['authority'])
(stage/'driver.py').write_text(P['driver'])
assert sha(stage/'current-birth-full64-config.json')==P['config_sha256']
assert sha(target)==P['authority_sha256'] and sha(stage/'driver.py')==P['driver_sha256']
with (stage/'driver.log').open('x') as log:
 child=subprocess.Popen(['python3',str(stage/'driver.py'),str(stage),P['source_revision']],stdout=log,stderr=subprocess.STDOUT,
  start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
v={'stage':str(stage),'supervisor_pid':child.pid,'source_revision':P['source_revision'],
 'driver_sha256':P['driver_sha256'],'config_sha256':P['config_sha256'],'payload_files':len(P['payload_sha256']),
 'GPU_submissions':0,'ledger_written':False,'observed_unix':time.time()}
(stage/'launch.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
"""
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],
        input=code,text=True,capture_output=True,timeout=55)
    if call.returncode:raise RuntimeError(call.stderr[-2000:])
    v=json.loads(call.stdout);launch_ref.write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v));return 0


if __name__=='__main__':raise SystemExit(main())
