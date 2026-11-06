#!/usr/bin/env python3
"""Transport the registered current-birth full256 CPU scope by SCP."""
import ast
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

DRIVER = "import hashlib,json,os,pathlib,subprocess,sys,time\nstage=pathlib.Path(sys.argv[1]);root=stage.parent.parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()\nreg=json.loads((stage/'registration.json').read_text());budget=root/'reports/budget.json'\nr={'status':'CURRENT_BIRTH_SAMPLING_CPU_RUNNING_NOT_REAL_CAL','pid':os.getpid(),'source_revision':sys.argv[2],\n 'started_unix':time.time(),'GPU_submissions':0,'ledger_written':False,'GPU_lock_acquired':False,\n 'budget_before_sha256':sha(budget),'planned_scope':reg['CPU_scope'],'payload_sha256':reg['payload_sha256']}\ndef save():\n p=stage/'receipt.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(r,indent=2)+'\\n');tmp.replace(p)\nassert not (stage/'receipt.json').exists();save();start=time.perf_counter()\ntry:\n gate=reg['original_working_CPU_completion_gate']\n original=pathlib.Path(gate['stage'])/'receipt.json'\n while True:\n  g=json.loads(original.read_text())\n  assert g['pid']==gate['supervisor_pid'] and g['source_revision']==gate['source_revision']\n  handles=[g['pid'],g.get('child_pid')]\n  live=[n for n in handles if n and pathlib.Path('/proc/'+str(n)).exists()]\n  r.update(status='CURRENT_BIRTH_CPU_WAITING_ORIGINAL_WORKING_FULL256',original_working_live_PIDs=live,original_working_status=g['status']);save()\n  if live:time.sleep(30);continue\n  assert g['exit_code']==g['child_exit_code']==0\n  old_stage=pathlib.Path(gate['stage']);old_reg=json.loads((old_stage/'registration.json').read_text())\n  assert sha(old_stage/'registration.json')==gate['registration_sha256']\n  assert {n:sha(old_stage/n) for n in old_reg['payload_sha256']}==g['payload_after_sha256']==old_reg['payload_sha256']\n  assert sha(old_stage/'result.json')==g['result_sha256']\n  result=json.loads((old_stage/'result.json').read_text())\n  assert result['status']=='WORKING_EPOCH_FULL_SAMPLER_CPU_PASS_NOT_REAL_MODEL'\n  assert (result['actual_complete_solver_updates'],result['actual_normal_net_calls'],result['actual_all_tensors_reloaded'])==(9216,18432,4736)\n  r['original_working_full_CPU_exit0_and_original_handles_absent_before_heavy_CPU']=True\n  r['queue_budget_sha256']=r['budget_before_sha256'];r['budget_before_sha256']=sha(budget)\n  r['queue_wall_seconds']=time.perf_counter()-start;start=time.perf_counter()\n  r.update(status='CURRENT_BIRTH_SAMPLING_CPU_RUNNING_NOT_REAL_CAL');save();break\n assert {n:sha(stage/n) for n in reg['payload_sha256']}==reg['payload_sha256']\n assert {n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']}==reg['runtime_source_sha256']\n env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')\n cmd=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python',str(stage/'scripts/check_wc_current_birth_sampling_cpu_r1.py'),'--stage',str(stage),'--runtime',str(root/'runtime'),'--output',str(stage/'result.json')]\n with (stage/'test.log').open('x') as log:\n  child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env);r['child_pid']=child.pid;save();r['child_exit_code']=child.wait()\n assert r['child_exit_code']==0\n v=json.loads((stage/'result.json').read_text());assert v['status']=='CURRENT_BIRTH_FULL_SAMPLER_CPU_PASS_NOT_REAL_MODEL'\n assert v['planned_scope']==reg['CPU_scope'] and not v['CUDA_initialized'] and v['GPU_submissions']==0\n assert (v['actual_complete_solver_updates'],v['actual_normal_net_calls'],v['actual_all_tensors_reloaded'])==(9216,18432,4736)\n assert v['current_birth_rule']==reg['current_P_birth_rule'] and v['additional_current_birth_mutation_refusals']==12\n r.update(status='CURRENT_BIRTH_SAMPLING_ACTUAL_CPU_PASS_NOT_REAL_CAL',exit_code=0,result_sha256=sha(stage/'result.json'))\nexcept BaseException as e:r.update(status='CURRENT_BIRTH_SAMPLING_CPU_FAILED_COMPLETE_SCOPE_RETAINED',exit_code=1,error_type=type(e).__name__,error=str(e))\nfinally:\n r.update(CPU_wall_seconds=time.perf_counter()-start,ended_unix=time.time(),budget_after_sha256=sha(budget),payload_after_sha256={n:sha(stage/n) for n in reg['payload_sha256']})\n if r['payload_after_sha256']!=reg['payload_sha256']:r.update(status='CURRENT_BIRTH_SAMPLING_SOURCE_CHANGED',exit_code=1)\n save()\nraise SystemExit(r['exit_code'])\n"

REMOTE_ARCHIVE = '/home/gaokuangda/data/gkd/worldcache_omr/.sync/wc-current-birth-sampling-cpu-r1-20261010.tgz'


def main():
    ref = Path('manifests/wc_current_birth_sampling_cpu_r1_preregistration_20261010.json')
    reg = json.loads(ref.read_text())
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    launch = Path('reports/wc_current_birth_sampling_cpu_r1_launch_20261010.json')
    assert not launch.exists()
    proof = json.loads(Path(reg['accepted_dynamic_prerequisite']['capture_ref']).read_text())
    assert proof['exit_code'] == 0 and proof['independent_source_complete_results_and_actual_artifact_hashes_verified']
    assert proof['independent_tensor_reload']['actual_tensors'] == 2368
    assert proof['independent_tensor_reload']['full_partial_references'] == 8
    pure_ref=reg['accepted_working_controller_prerequisite']
    pure=json.loads(Path(pure_ref['capture_ref']).read_text())
    assert hashlib.sha256(Path(pure_ref['capture_ref']).read_bytes()).hexdigest()==pure_ref['capture_sha256']
    assert pure['exit_code']==0 and pure['result']['complete_policy_paths']==18 and pure['GPU_submissions']==0
    assert pure['complete_registered_source_and_scope_checked']
    new_ref = reg['accepted_current_birth_real_parameter_prerequisite']
    value = json.loads(Path(new_ref['result_ref']).read_text())
    assert hashlib.sha256(Path(new_ref['result_ref']).read_bytes()).hexdigest() == new_ref['result_sha256']
    assert value['status'] == 'CURRENT_BIRTH_REAL_PARAMETER_FULL64_SCRIPTED_CPU_PASS_NOT_COSMOS_ROLLOUT'
    assert (value['complete_scripted_full36_paths'], value['complete_scripted_decisions'], value['healthy_state_roundtrips'], value['scripted_P_actions_not_real_P_calls']) == (64,2304,256,240)
    assert len(value['mutation_refusals']) == 14 and value['GPU_submissions'] == 0
    assert value['current_P_birth_rule'] == reg['current_P_birth_rule']
    assert all(hashlib.sha256(Path(n).read_bytes()).hexdigest()==h for n,h in value['source_sha256'].items())
    driver = DRIVER
    compile(driver, 'unchanged_registered_driver', 'exec')
    assert ref.read_bytes() == subprocess.check_output(['git', 'show', revision + ':' + str(ref)])
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode='w:gz') as tar:
        files = {n: Path(n).read_bytes() for n in reg['payload_sha256']}
        for n, raw in files.items():
            assert hashlib.sha256(raw).hexdigest() == reg['payload_sha256'][n]
            assert raw == subprocess.check_output(['git', 'show', revision + ':' + n])
        files.update({'registration.json': ref.read_bytes(), 'driver.py': driver.encode()})
        for n, raw in files.items():
            entry = tarfile.TarInfo(n)
            entry.size = len(raw)
            tar.addfile(entry, io.BytesIO(raw))
    raw = archive.getvalue()
    archive_path = Path('.sync/wc-current-birth-sampling-cpu-r1-20261010.tgz')
    assert not archive_path.exists()
    archive_path.write_bytes(raw)
    packet = {'archive_path': REMOTE_ARCHIVE, 'archive_sha256': hashlib.sha256(raw).hexdigest(),
              'archive_bytes': len(raw), 'source_revision': revision,
              'driver_sha256': hashlib.sha256(driver.encode()).hexdigest(), 'transport': 'SCP_FILE_CURRENT_BIRTH_FULL256_R1'}
    check = "import pathlib; assert not pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr/.sync/wc-current-birth-sampling-cpu-r1-20261010').exists(); assert not pathlib.Path(" + repr(REMOTE_ARCHIVE) + ").exists()"
    subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', 'gkd_minchen', 'python3 -'],
                   input=check, text=True, check=True, timeout=40)
    print(json.dumps({'transport': packet['transport'], 'archive_bytes': len(raw), 'phase': 'uploading'}), flush=True)
    subprocess.run(['scp', '-q', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', str(archive_path),
                    'gkd_minchen:' + REMOTE_ARCHIVE], check=True, timeout=600)
    code = 'P=' + repr(packet) + '\n' + r'''
import hashlib,io,json,os,pathlib,subprocess,tarfile,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/'.sync/wc-current-birth-sampling-cpu-r1-20261010'
assert not stage.exists();raw=pathlib.Path(P['archive_path']).read_bytes()
assert len(raw)==P['archive_bytes'] and hashlib.sha256(raw).hexdigest()==P['archive_sha256']
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as tar:
 for item in tar.getmembers():
  p=pathlib.PurePosixPath(item.name);assert item.isfile() and not p.is_absolute() and '..' not in p.parts
 stage.mkdir();tar.extractall(stage)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reg=json.loads((stage/'registration.json').read_text());prerequisite=reg['accepted_dynamic_prerequisite']
assert sha(stage/'driver.py')==P['driver_sha256']
assert {n:sha(stage/n) for n in reg['payload_sha256']}==reg['payload_sha256']
old=root/prerequisite['stage'];previous=json.loads((old/'receipt.json').read_text())
assert previous['exit_code']==previous['child_exit_code']==0 and previous['source_revision']==prerequisite['source_revision']
assert not any(pathlib.Path('/proc/'+str(p)).exists() for p in (previous['pid'],previous['child_pid']))
assert sha(old/'result.json')==previous['result_sha256']
previous_reg=json.loads((old/'registration.json').read_text())
assert {n:sha(old/n) for n in previous_reg['payload_sha256']}==previous_reg['payload_sha256']==previous['payload_after_sha256']
command=['python3',str(stage/'driver.py'),str(stage),P['source_revision']]
with (stage/'driver.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),start_new_session=True)
value={'stage':str(stage),'supervisor_pid':child.pid,'source_revision':P['source_revision'],'archive_sha256':P['archive_sha256'],
 'registration_sha256':sha(stage/'registration.json'),'driver_sha256':sha(stage/'driver.py'),'command':command,
 'transport':P['transport'],'remote_archive_path':P['archive_path'],'GPU_submissions':0,
 'ledger_written':False,'GPU_lock_acquired':False,'observed_unix':time.time()}
(stage/'launch.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))
'''
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', 'gkd_minchen', 'python3 -'],
                            input=code, text=True, capture_output=True, timeout=55)
    if result.returncode:
        raise RuntimeError(result.stderr[-3000:])
    value = json.loads(result.stdout)
    launch.write_text(json.dumps(value, indent=2) + '\n')
    print(json.dumps(value), flush=True)


if __name__ == '__main__':
    main()
