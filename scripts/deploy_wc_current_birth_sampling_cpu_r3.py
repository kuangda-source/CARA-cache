#!/usr/bin/env python3
"""Copy verified frozen payload into a new full256 CPU stage; upload only delta."""
import ast
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

DRIVER = "import hashlib,json,os,pathlib,subprocess,sys,time\nstage=pathlib.Path(sys.argv[1]);root=stage.parent.parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()\nreg=json.loads((stage/'registration.json').read_text());budget=root/'reports/budget.json'\nr={'status':'CURRENT_BIRTH_SAMPLING_CPU_RUNNING_NOT_REAL_CAL','pid':os.getpid(),'source_revision':sys.argv[2],\n 'started_unix':time.time(),'GPU_submissions':0,'ledger_written':False,'GPU_lock_acquired':False,\n 'budget_before_sha256':sha(budget),'planned_scope':reg['CPU_scope'],'payload_sha256':reg['payload_sha256']}\ndef save():\n p=stage/'receipt.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(r,indent=2)+'\\n');tmp.replace(p)\nassert not (stage/'receipt.json').exists();save();start=time.perf_counter()\ntry:\n gate=reg['original_working_CPU_completion_gate']\n original=pathlib.Path(gate['stage'])/'receipt.json'\n while True:\n  g=json.loads(original.read_text())\n  assert g['pid']==gate['supervisor_pid'] and g['source_revision']==gate['source_revision']\n  handles=[g['pid'],g.get('child_pid')]\n  live=[n for n in handles if n and pathlib.Path('/proc/'+str(n)).exists()]\n  r.update(status='CURRENT_BIRTH_CPU_WAITING_ORIGINAL_WORKING_FULL256',original_working_live_PIDs=live,original_working_status=g['status']);save()\n  if live:time.sleep(30);continue\n  assert g['exit_code']==g['child_exit_code']==0\n  old_stage=pathlib.Path(gate['stage']);old_reg=json.loads((old_stage/'registration.json').read_text())\n  assert sha(old_stage/'registration.json')==gate['registration_sha256']\n  assert {n:sha(old_stage/n) for n in old_reg['payload_sha256']}==g['payload_after_sha256']==old_reg['payload_sha256']\n  assert sha(old_stage/'result.json')==g['result_sha256']\n  result=json.loads((old_stage/'result.json').read_text())\n  assert result['status']=='WORKING_EPOCH_FULL_SAMPLER_CPU_PASS_NOT_REAL_MODEL'\n  assert (result['actual_complete_solver_updates'],result['actual_normal_net_calls'],result['actual_all_tensors_reloaded'])==(9216,18432,4736)\n  r['original_working_full_CPU_exit0_and_original_handles_absent_before_heavy_CPU']=True\n  r['queue_budget_sha256']=r['budget_before_sha256'];r['budget_before_sha256']=sha(budget)\n  r['queue_wall_seconds']=time.perf_counter()-start;start=time.perf_counter()\n  r.update(status='CURRENT_BIRTH_SAMPLING_CPU_RUNNING_NOT_REAL_CAL');save();break\n assert {n:sha(stage/n) for n in reg['payload_sha256']}==reg['payload_sha256']\n assert {n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']}==reg['runtime_source_sha256']\n env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')\n cmd=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python',str(stage/'scripts/check_wc_current_birth_sampling_cpu_r3.py'),'--stage',str(stage),'--runtime',str(root/'runtime'),'--output',str(stage/'result.json')]\n with (stage/'test.log').open('x') as log:\n  child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env);r['child_pid']=child.pid;save();r['child_exit_code']=child.wait()\n assert r['child_exit_code']==0\n v=json.loads((stage/'result.json').read_text());assert v['status']=='CURRENT_BIRTH_FULL_SAMPLER_CPU_PASS_NOT_REAL_MODEL'\n assert v['planned_scope']==reg['CPU_scope'] and not v['CUDA_initialized'] and v['GPU_submissions']==0\n assert (v['actual_complete_solver_updates'],v['actual_normal_net_calls'],v['actual_all_tensors_reloaded'])==(9216,18432,4736)\n assert v['current_birth_rule']==reg['current_P_birth_rule'] and v['additional_current_birth_mutation_refusals']==12\n r.update(status='CURRENT_BIRTH_SAMPLING_ACTUAL_CPU_PASS_NOT_REAL_CAL',exit_code=0,result_sha256=sha(stage/'result.json'))\nexcept BaseException as e:r.update(status='CURRENT_BIRTH_SAMPLING_CPU_FAILED_COMPLETE_SCOPE_RETAINED',exit_code=1,error_type=type(e).__name__,error=str(e))\nfinally:\n r.update(CPU_wall_seconds=time.perf_counter()-start,ended_unix=time.time(),budget_after_sha256=sha(budget),payload_after_sha256={n:sha(stage/n) for n in reg['payload_sha256']})\n if r['payload_after_sha256']!=reg['payload_sha256']:r.update(status='CURRENT_BIRTH_SAMPLING_SOURCE_CHANGED',exit_code=1)\n save()\nraise SystemExit(r['exit_code'])\n"


def main():
    ref=Path('manifests/wc_current_birth_sampling_cpu_r3_preregistration_20261010.json')
    reg=json.loads(ref.read_text());revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    launch=Path('reports/wc_current_birth_sampling_cpu_r3_launch_20261010.json');assert not launch.exists()
    assert ref.read_bytes()==subprocess.check_output(['git','show',revision+':'+str(ref)])
    assert reg['CPU_scope']==json.loads(Path('manifests/wc_current_birth_sampling_cpu_r2_preregistration_20261010.json').read_text())['CPU_scope']
    for name,expect in reg['payload_sha256'].items():
        assert sha(name)==expect
        assert Path(name).read_bytes()==subprocess.check_output(['git','show',revision+':'+name])
    failed=reg['preserved_current_birth_R2_failure']
    failure=json.loads(Path(failed['capture_ref']).read_text())
    assert sha(failed['capture_ref'])==failed['capture_sha256'] and failure['exit_code']==1
    assert failure['independent_source_complete_results_and_actual_artifact_hashes_verified']
    meta=reg['accepted_complete_real_input_metadata_CPU']
    proof=json.loads(Path(meta['capture_ref']).read_text())
    assert sha(meta['capture_ref'])==meta['capture_sha256'] and proof['CPU_result_accepted'] and proof['complete_source_scope_and_real_files_verified']
    old=Path('scripts/check_wc_current_birth_sampling_cpu_r2.py').read_text()
    new=Path('scripts/check_wc_current_birth_sampling_cpu_r3.py').read_text()
    assert old.replace('tests/check_source_aware_current_birth_sampling_cpu_r1.py','tests/check_source_aware_current_birth_sampling_cpu_r2.py')==new
    old=Path('tests/check_source_aware_current_birth_sampling_cpu_r1.py').read_text()
    new=Path('tests/check_source_aware_current_birth_sampling_cpu_r2.py').read_text()
    assert old.replace('source_aware_current_birth_sampling_r1','source_aware_current_birth_sampling_r2')==new
    compile(DRIVER,'complete256_current_birth_R3_driver','exec')
    oldreg=json.loads(Path('manifests/wc_current_birth_sampling_cpu_r2_preregistration_20261010.json').read_text())
    copied={n:h for n,h in reg['payload_sha256'].items() if oldreg['payload_sha256'].get(n)==h}
    changed={n:Path(n).read_bytes() for n in reg['payload_sha256'] if n not in copied}
    changed.update({'registration.json':ref.read_bytes(),str(ref):ref.read_bytes(),'driver.py':DRIVER.encode()})
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w:gz') as tar:
        for name,raw in changed.items():
            entry=tarfile.TarInfo(name);entry.size=len(raw);tar.addfile(entry,io.BytesIO(raw))
    raw=buffer.getvalue();stem='wc-current-birth-sampling-cpu-r3-20261010'
    archive=Path('.sync')/(stem+'.tgz');assert not archive.exists();archive.write_bytes(raw)
    remote='/home/gaokuangda/data/gkd/worldcache_omr/.sync/'+stem+'.tgz'
    subprocess.run(['scp','-q','-o','BatchMode=yes','-o','ConnectTimeout=15',str(archive),'gkd_minchen:'+remote],check=True,timeout=600)
    packet={'remote':remote,'archive_bytes':len(raw),'archive_sha256':hashlib.sha256(raw).hexdigest(),
        'source_revision':revision,'driver_sha256':hashlib.sha256(DRIVER.encode()).hexdigest(),
        'stage_name':stem,'copy_sha256':copied,'failed':failed,'meta':meta}
    code='P='+repr(packet)+'\n'+r'''
import hashlib,io,json,os,pathlib,shutil,subprocess,tarfile,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/'.sync'/P['stage_name'];assert not stage.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=root/'.sync/wc-current-birth-sampling-cpu-r2-20261010';r=json.loads((old/'receipt.json').read_text())
assert r['source_revision']==P['failed']['source_revision'] and r['exit_code']==r['child_exit_code']==1
assert not any(pathlib.Path('/proc/'+str(p)).exists() for p in (r['pid'],r['child_pid']))
assert "has no attribute 'valid_P_interval'" in (old/'test.log').read_text()
assert sha(old/'registration.json')==P['failed']['registration_sha256']
previous=json.loads((old/'registration.json').read_text())
assert {n:sha(old/n) for n in previous['payload_sha256']}==r['payload_after_sha256']==previous['payload_sha256']
metastage=root/P['meta']['stage'];mr=json.loads((metastage/'receipt.json').read_text())
assert mr['source_revision']==P['meta']['source_revision'] and mr['exit_code']==mr['child_exit_code']==0
assert not any(pathlib.Path('/proc/'+str(p)).exists() for p in (mr['pid'],mr['child_pid']))
assert sha(pathlib.Path(mr['result_ref']))==P['meta']['result_sha256']==mr['result_sha256']
value=json.loads(pathlib.Path(mr['result_ref']).read_text())
assert (value['complete_method_parameter_sets'],value['actual_Native_file_sizes_and_hashes_verified'])==(16,4)
assert len(value['fixture_API_required_exports_verified'])==7 and not value['CUDA_initialized']
raw=pathlib.Path(P['remote']).read_bytes();assert len(raw)==P['archive_bytes'] and hashlib.sha256(raw).hexdigest()==P['archive_sha256']
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as tar:
 for item in tar.getmembers():
  p=pathlib.PurePosixPath(item.name);assert item.isfile() and not p.is_absolute() and '..' not in p.parts
 stage.mkdir()
 for name,expect in P['copy_sha256'].items():
  assert sha(old/name)==expect
  target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old/name,target)
 tar.extractall(stage)
reg=json.loads((stage/'registration.json').read_text())
assert {n:sha(stage/n) for n in reg['payload_sha256']}==reg['payload_sha256']
assert {n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']}==reg['runtime_source_sha256']
assert sha(stage/'driver.py')==P['driver_sha256']
command=['python3',str(stage/'driver.py'),str(stage),P['source_revision']]
with (stage/'driver.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
v={'stage':str(stage),'supervisor_pid':child.pid,'source_revision':P['source_revision'],'archive_sha256':P['archive_sha256'],
 'registration_sha256':sha(stage/'registration.json'),'driver_sha256':sha(stage/'driver.py'),'command':command,
 'verified_immutable_payload_files_copied':len(P['copy_sha256']),'archive_bytes':P['archive_bytes'],
 'prior_R2_specific_failure_and_handles_absent':True,'metadata_R3_full_scope_and_seven_API_checks_passed':True,
 'GPU_submissions':0,'ledger_written':False,'GPU_lock_acquired':False,'observed_unix':time.time()}
(stage/'launch.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
'''
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],
        input=code,text=True,capture_output=True,timeout=55)
    if result.returncode:raise RuntimeError(result.stderr[-2000:])
    value=json.loads(result.stdout);launch.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))


if __name__=='__main__':main()
