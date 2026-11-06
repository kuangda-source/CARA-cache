#!/usr/bin/env python3
"""Stage and run the exact committed A output core using the existing CPU runtime."""
import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile


DRIVER = r'''
import hashlib,json,os,pathlib,subprocess,sys,time
stage=pathlib.Path(sys.argv[1]);root=stage.parent.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reg=json.loads((stage/'registration.json').read_text());budget=root/'reports/budget.json'
r={'status':'MF_A_COLLECTION_CORE_CPU_RUNNING_NOT_REAL_CAL','pid':os.getpid(),
   'source_revision':sys.argv[2],'started_unix':time.time(),
   'GPU_submissions':0,'ledger_written':False,'GPU_lock_acquired':False,
   'budget_before_sha256':sha(budget),'payload_sha256':reg['payload_sha256']}
def save():
 p=stage/'receipt.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(r,indent=2)+'\n');tmp.replace(p)
assert not (stage/'receipt.json').exists();save();start=time.perf_counter()
try:
 assert {n:sha(stage/n) for n in reg['payload_sha256']}==reg['payload_sha256']
 assert {n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']}==reg['runtime_source_sha256']
 env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
          OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONPATH=str(stage/'src'))
 cmd=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python',
      str(stage/'tests/check_cfg_guided_w1_collection_cpu.py'),'--runtime',str(root/'runtime'),'--output',str(stage/'controlled-artifacts')]
 with (stage/'test.log').open('x') as log:
  child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env);r['child_pid']=child.pid;save();r['child_exit_code']=child.wait()
 assert r['child_exit_code']==0
 rows=[]
 for line in (stage/'test.log').read_text().splitlines():
  try:v=json.loads(line)
  except ValueError:continue
  if isinstance(v,dict) and v.get('status')=='GUIDED_W1_PINNED_COLLECTION_FULL36_CONTROLLED_CPU_PASS_NOT_REAL_CAL':rows.append(v)
 assert len(rows)==1;result=rows[0]
 assert not result['CUDA_initialized'] and result['GPU_submissions']==0 and not result['actual_UniPC_or_Cosmos_weights_or_video_or_quality_or_latency_claim']
 assert result['Torch_version']=='2.7.1+cu128' and len(result['complete_flow_OFF_ON_controls'])==2
 assert result['actual_tensor_artifacts_reloaded']==5 and result['actual_branch_tensors_reloaded']==40
 assert all(v['actual_guided_outputs_direct_equal']==36 and v['actual_final_latent_direct_equal'] and v['action_counter_RNG_and_buffer_values_equal'] for v in result['complete_flow_OFF_ON_controls'])
 assert result['registered_second_origin_writer_failure']['status']=='EXPECTED_FAILURE'
 (stage/'result.json').write_text(json.dumps(result,indent=2)+'\n');r.update(status='MF_A_COLLECTION_CORE_ACTUAL_CPU_PASS_NOT_REAL_CAL',exit_code=0,result_sha256=sha(stage/'result.json'))
except BaseException as e:
 r.update(status='MF_A_COLLECTION_CORE_CPU_FAILED_SCOPE_RETAINED',exit_code=1,error_type=type(e).__name__,error=str(e))
finally:
 r.update(CPU_wall_seconds=time.perf_counter()-start,ended_unix=time.time(),budget_after_sha256=sha(budget),
          payload_after_sha256={n:sha(stage/n) for n in reg['payload_sha256']})
 # A concurrent original GPU may legitimately settle its ledger. This CPU
 # program never writes it and does not require the other process to stop.
 r['concurrent_budget_may_change_due_to_original_GPU']=r['budget_before_sha256']!=r['budget_after_sha256']
 if r['payload_after_sha256']!=reg['payload_sha256']:r.update(status='MF_A_COLLECTION_CORE_SOURCE_CHANGED',exit_code=1)
 save()
raise SystemExit(r['exit_code'])
'''


def main():
    ref=Path('manifests/wc_mf_a_collection_core_cpu_r4_preregistration_20261010.json')
    reg=json.loads(ref.read_text());revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    launch=Path('reports/wc_mf_a_collection_core_cpu_r4_launch_20261010.json');assert not launch.exists()
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
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/'.sync/wc-mf-a-collection-core-cpu-r4-20261010'
assert not stage.exists();raw=base64.b64decode(P['archive']);assert hashlib.sha256(raw).hexdigest()==P['archive_sha256']
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as tar:
 for item in tar.getmembers():
  p=pathlib.PurePosixPath(item.name);assert item.isfile() and not p.is_absolute() and '..' not in p.parts
 stage.mkdir();tar.extractall(stage)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
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
