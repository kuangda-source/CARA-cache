#!/usr/bin/env python3
"""Run the full committed A/P0 CPU scope after independent P0 acceptance."""
import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile


DRIVER = "import hashlib,json,os,pathlib,subprocess,sys,time\nstage=pathlib.Path(sys.argv[1]);root=stage.parent.parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()\nreg=json.loads((stage/'registration.json').read_text());budget=root/'reports/budget.json'\nr={'status':'A_P0_SAMPLING_CPU_RUNNING_NOT_REAL_CAL','pid':os.getpid(),'source_revision':sys.argv[2],\n 'started_unix':time.time(),'GPU_submissions':0,'ledger_written':False,'GPU_lock_acquired':False,\n 'budget_before_sha256':sha(budget),'planned_scope':reg['CPU_scope'],'payload_sha256':reg['payload_sha256']}\ndef save():\n p=stage/'receipt.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(r,indent=2)+'\\n');tmp.replace(p)\nassert not (stage/'receipt.json').exists();save();start=time.perf_counter()\ntry:\n assert {n:sha(stage/n) for n in reg['payload_sha256']}==reg['payload_sha256']\n assert {n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']}==reg['runtime_source_sha256']\n env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')\n cmd=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python',str(stage/'scripts/check_wc_a_p0_sampling_cpu_r2.py'),'--stage',str(stage),'--runtime',str(root/'runtime'),'--output',str(stage/'result.json')]\n with (stage/'test.log').open('x') as log:\n  child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env);r['child_pid']=child.pid;save();r['child_exit_code']=child.wait()\n assert r['child_exit_code']==0\n v=json.loads((stage/'result.json').read_text());assert v['status']=='A_P0_FULL_SAMPLER_ACTUAL_CPU_PASS_NOT_REAL_MODEL'\n assert v['planned_scope']==reg['CPU_scope'] and not v['CUDA_initialized'] and v['GPU_submissions']==0\n assert (v['actual_complete_solver_updates'],v['actual_normal_net_calls'],v['actual_all_tensors_reloaded'])==(10368,20736,5328)\n r.update(status='A_P0_SAMPLING_ACTUAL_CPU_PASS_NOT_REAL_CAL',exit_code=0,result_sha256=sha(stage/'result.json'))\nexcept BaseException as e:r.update(status='A_P0_SAMPLING_CPU_FAILED_COMPLETE_SCOPE_RETAINED',exit_code=1,error_type=type(e).__name__,error=str(e))\nfinally:\n r.update(CPU_wall_seconds=time.perf_counter()-start,ended_unix=time.time(),budget_after_sha256=sha(budget),payload_after_sha256={n:sha(stage/n) for n in reg['payload_sha256']})\n if r['payload_after_sha256']!=reg['payload_sha256']:r.update(status='A_P0_SAMPLING_SOURCE_CHANGED',exit_code=1)\n save()\nraise SystemExit(r['exit_code'])\n"


def main():
    ref=Path('manifests/wc_a_p0_sampling_cpu_r2_preregistration_20261010.json')
    reg=json.loads(ref.read_text());revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    launch=Path('reports/wc_a_p0_sampling_cpu_r2_launch_20261010.json');assert not launch.exists()
    prerequisite=reg['accepted_P0_prerequisite']
    original=json.loads(Path(prerequisite['capture_ref']).read_text())
    assert original['source_revision']==prerequisite['source_revision'] and original['exit_code']==0
    assert original['independent_source_complete_results_and_actual_artifact_hashes_verified']
    assert original['independent_tensor_reload']['actual_tensors']==3848
    assert original['independent_tensor_reload']['full_partial_references']==32
    assert original['GPU_submissions']==0 and not original['ledger_written']
    assert ref.read_bytes()==subprocess.check_output(['git','show',revision+':'+str(ref)])
    archive=io.BytesIO()
    with tarfile.open(fileobj=archive,mode='w:gz') as tar:
        files={n:Path(n).read_bytes() for n in reg['payload_sha256']}
        for n,raw in files.items():
            assert hashlib.sha256(raw).hexdigest()==reg['payload_sha256'][n]
            assert raw==subprocess.check_output(['git','show',revision+':'+n])
        files.update({'registration.json':ref.read_bytes(),'driver.py':DRIVER.encode()})
        for n,raw in files.items():
            item=tarfile.TarInfo(n);item.size=len(raw);tar.addfile(item,io.BytesIO(raw))
    raw=archive.getvalue();packet={'archive':base64.b64encode(raw).decode(),'archive_sha256':hashlib.sha256(raw).hexdigest(),'source_revision':revision}
    code='P='+repr(packet)+'\n'+r'''
import base64,hashlib,io,json,os,pathlib,subprocess,tarfile,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/'.sync/wc-a-p0-sampling-cpu-r2-20261010'
assert not stage.exists();raw=base64.b64decode(P['archive']);assert hashlib.sha256(raw).hexdigest()==P['archive_sha256']
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as tar:
 for item in tar.getmembers():
  p=pathlib.PurePosixPath(item.name);assert item.isfile() and not p.is_absolute() and '..' not in p.parts
 stage.mkdir();tar.extractall(stage)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reg=json.loads((stage/'registration.json').read_text());prerequisite=reg['accepted_P0_prerequisite']
old=root/prerequisite['stage'];previous=json.loads((old/'receipt.json').read_text())
assert previous['exit_code']==previous['child_exit_code']==0
assert previous['source_revision']==prerequisite['source_revision']
assert not any(pathlib.Path('/proc/'+str(p)).exists() for p in (previous['pid'],previous['child_pid']))
assert sha(old/'result.json')==previous['result_sha256']
previous_reg=json.loads((old/'registration.json').read_text())
assert {n:sha(old/n) for n in previous_reg['payload_sha256']}==previous_reg['payload_sha256']==previous['payload_after_sha256']
command=['python3',str(stage/'driver.py'),str(stage),P['source_revision']]
with (stage/'driver.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),start_new_session=True)
value={'stage':str(stage),'supervisor_pid':child.pid,'source_revision':P['source_revision'],'archive_sha256':P['archive_sha256'],
 'registration_sha256':sha(stage/'registration.json'),'driver_sha256':sha(stage/'driver.py'),'command':command,
 'GPU_submissions':0,'ledger_written':False,'GPU_lock_acquired':False,'observed_unix':time.time()}
(stage/'launch.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=code,text=True,capture_output=True,timeout=55)
    if call.returncode:raise RuntimeError(call.stderr[-3000:])
    value=json.loads(call.stdout);launch.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))


if __name__=='__main__':main()
