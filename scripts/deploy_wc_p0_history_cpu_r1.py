#!/usr/bin/env python3
"""Stage and run the exact committed P0 deployment core using the existing CPU runtime."""
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
r={'status':'P0_HISTORY_CPU_RUNNING_NOT_REAL_CAL','pid':os.getpid(),
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
      str(stage/'tests/check_partial_mlp_history_cpu_r1.py'),'--runtime',str(root/'runtime'),'--output',str(stage/'controlled-artifacts')]
 with (stage/'test.log').open('x') as log:
  child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env);r['child_pid']=child.pid;save();r['child_exit_code']=child.wait()
 assert r['child_exit_code']==0
 rows=[]
 for line in (stage/'test.log').read_text().splitlines():
  try:v=json.loads(line)
  except ValueError:continue
  if isinstance(v,dict) and v.get('status')=='P0_HISTORY_FULL78_PINNED_BLOCK_CPU_PASS_NOT_UNIPC_OR_VIDEO':rows.append(v)
 assert len(rows)==1;result=rows[0]
 assert not result['CUDA_initialized'] and result['GPU_submissions']==0 and not result['actual_UniPC_or_Cosmos_weights_or_video_or_quality_or_latency_claim']
 assert result['Torch_version']=='2.7.1+cu128' and len(result['complete_paths'])==78
 assert (result['actual_complete_pairs'],result['actual_normal_net_calls'],result['actual_tensors_reloaded'])==(2808,5616,2886)
 assert result['OFF_and_dense_maintenance_full_source_parity_both_flows']
 assert result['independent_full_GEMM_then_replace_reference_for_all24_partial_rollouts']
 assert result['full_P_matches_true_D_output_but_remains_P_provenance_both_flows']
 assert result['actual_gathered_Linear_rows_64_or_96_verified_for_all_partial_opportunities']
 assert result['working_P_not_D_calibration_or_zero_risk_RA_source']
 assert len(result['registered_both_flow_second_branch_failures'])==6
 assert all(f['completed_pairs']==f['failure_step']-1 and f['poisoned_no_resume'] for f in result['registered_both_flow_second_branch_failures'])
 assert result['history_check_totals']=={'P_source_reuse_C_steps':230,'consecutive_P_steps':50,'projection_updates_checked':1520}
 assert result['all_P_C_and_consecutive_P_histories_and_token_provenance_verified']
 assert len(result['invalid_schedule_refusals_before_install'])==7
 (stage/'result.json').write_text(json.dumps(result,indent=2)+'\n');r.update(status='P0_HISTORY_ACTUAL_CPU_PASS_NOT_REAL_CAL',exit_code=0,result_sha256=sha(stage/'result.json'))
except BaseException as e:
 r.update(status='P0_HISTORY_CPU_FAILED_SCOPE_RETAINED',exit_code=1,error_type=type(e).__name__,error=str(e))
finally:
 r.update(CPU_wall_seconds=time.perf_counter()-start,ended_unix=time.time(),budget_after_sha256=sha(budget),
          payload_after_sha256={n:sha(stage/n) for n in reg['payload_sha256']})
 # A concurrent original GPU may legitimately settle its ledger. This CPU
 # program never writes it and does not require the other process to stop.
 r['concurrent_budget_may_change_due_to_original_GPU']=r['budget_before_sha256']!=r['budget_after_sha256']
 if r['payload_after_sha256']!=reg['payload_sha256']:r.update(status='P0_HISTORY_SOURCE_CHANGED',exit_code=1)
 save()
raise SystemExit(r['exit_code'])
'''


def main():
    ref=Path('manifests/wc_p0_history_cpu_r1_preregistration_20261010.json')
    reg=json.loads(ref.read_text());revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    launch=Path('reports/wc_p0_history_cpu_r1_launch_20261010.json');assert not launch.exists()
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
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/'.sync/wc-p0-history-cpu-r1-20261010'
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
