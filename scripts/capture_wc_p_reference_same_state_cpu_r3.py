"""Read original complete CPU handles and all five-way artifacts independently."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


REMOTE = r'''import base64,copy,gzip,hashlib,json,math,os,pathlib,sys,time
project=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr')
s=project/'.sync/wc-p-reference-same-state-cpu-r3-20261011'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
launch=json.loads((s/'launch.json').read_text());receipt=json.loads((s/'receipt.json').read_text())
assert launch==P['launch'] and launch['source_revision']==receipt['source_revision']
assert receipt['pid']==launch['pid']
ids=[receipt['pid'],receipt['child_pid']]
if any(pathlib.Path('/proc/'+str(p)).exists() for p in ids):
 print(json.dumps({'status':'WAIT_ORIGINAL_P_REFERENCE_SAME_STATE_COMPLETE_CPU','pids':ids,'observed_unix':time.time()}))
 raise SystemExit(0)
assert sha(s/'registration.json')==P['registration_sha256']
reg=json.loads((s/'registration.json').read_text());payload=dict(reg['inherited_payload_sha256'],**reg['new_payload_sha256'])
assert {n:sha(s/n) for n in payload}==payload==receipt['payload_after_sha256'] and len(payload)==444
assert receipt['exit_code']==0 and receipt['status']=='P_REFERENCE_SAME_STATE_COMPLETE_CPU_PASS_PENDING_INDEPENDENT_CAPTURE'
assert receipt['GPU_submissions']==0 and receipt['ledger_written'] is False
assert sha(s/'result.json')==receipt['result_sha256'];value=json.loads((s/'result.json').read_text())
assert value['status']=='P_REFERENCE_SAME_STATE_COMPLETE_BOTH_FLOW_CPU_PASS_NOT_REAL_MODEL_OR_GPU'
assert [g['flow'] for g in value['checks']]==[False,True] and value['CUDA_initialized'] is False
assert (value['full_parent_paths'],value['events'],value['suffixes'],value['same_state_age_points'])==(8,8,32,48)
assert (value['actual_pair_computations'],value['actual_CFG_calls'])==(688,1376)
assert (value['actual_files_reloaded'],value['actual_tensors_reloaded'],value['actual_direct_tensor_comparisons'])==(88,1160,420)
assert value['scope_refusals']==26 and value['actual_truncation_refusals']==2
budget_before=sha(project/'reports/budget.json')
os.environ['CUDA_VISIBLE_DEVICES']='';sys.path.insert(0,str(s/'src'))
import torch
torch.set_num_threads(2)
def forbidden(*a,**kw):raise RuntimeError('Independent same-state capture forbids CUDA and downloads')
torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
from wcomr.mid_coverage import tree_digest
from wcomr.e4c_source_age_tensor_audit_r1 import audit as base_audit
variants=('OFFICIAL_C','P_REFERENCE_SCALAR','D_REFERENCE_UNIT','P_REFERENCE_UNIT','D_REFERENCE_SCALAR')
basekeys={'C','DENSE_SAME_STATE','candidate_latent','timestep'}
extra=set(variants)-{'D_REFERENCE_SCALAR'}
shape=[1,2048,2,8,8];files=[];all_points=[];tensors=direct=restores=D_controls=0
for group in value['checks']:
 assert group['status']=='PASS' and len(group['scope_refusals'])==13 and group['actual_truncation_refused']
 assert group['all_initial_state_and_installed_methods_restored']
 state=group['receipt'];view=copy.deepcopy(state);records={};extra_count=equal_count=0;points=[]
 assert state['initial_state_restored'] and len(state['requests'])==2
 for request in view['requests']:
  for row in request['paths']:
   for event in row['origins']:
    for branch in event['branches']:
     for point in branch['age_points']:
      art=point['artifact'];records[str(pathlib.Path(art['path']).resolve())]=(event,branch,point,copy.deepcopy(art))
      art['tensor_sha256']={k:v for k,v in art['tensor_sha256'].items() if k in basekeys}
 def loader(path,**kwargs):
  global extra_count,equal_count,restores,D_controls
  assert kwargs=={'weights_only':True,'map_location':'cpu'}
  x=torch.load(path,**kwargs);record=records.get(str(path))
  if record is None:return x
  event,branch,point,art=record
  assert set(x)==basekeys|extra and sha(path)==art['sha256']
  assert {k:tree_digest(v) for k,v in x.items()}==art['tensor_sha256']
  rows=point['five_reference_readouts'];assert tuple(r['variant'] for r in rows)==variants
  assert point['all_candidates_same_actual_input_and_full_source'] and point['deployed_reference_unchanged']=='D_REFERENCE_SCALAR'
  assert len(point['serial_restore_guards'])==5 and all(len(g)==2 for g in point['serial_restore_guards']);restores+=5
  assert len(point['research_teacher_actual_head_events'])==2
  assert len({r['source_cache_sha256'] for r in rows})==len({r['true_D_full_state_sha256'] for r in rows})==1
  assert point['teacher_state_restored_before_actual_C'] and not point['teacher_updates_final_deployment_anchors']
  errors={}
  for index,(name,row) in enumerate(zip(variants,rows)):
   assert row['input_sha256']==point['input_sha256'] and row['source']==branch['source'] and row['age']==point['age'] and row['step']==point['step']
   assert row['deployed_after_scoring']==(index==4)
   assert len(row['actual_head_events'])==row['actual_head_calls']==2+row['readout']['extra_heads']
   assert row['readout']['shared_alpha']==(0 if name=='OFFICIAL_C' else .5 if point['step']>=25 else 1)
   for proof in row['readout']['P_reference']:
    if proof is not None:
     assert branch['source']=='P' and name.startswith('P_REFERENCE')
     assert proof['true_D_full_state_before_sha256']==proof['true_D_full_state_after_sha256']
   pair=x['C'] if name=='D_REFERENCE_SCALAR' else x[name]
   assert len(pair)==2 and all(t.device.type=='cpu' and t.dtype==torch.float32 and list(t.shape)==shape and torch.isfinite(t).all() for t in pair)
   ec,eu=[a-b for a,b in zip(pair,x['DENSE_SAME_STATE'])]
   mse=(8*ec-7*eu).double().square().mean().item()
   assert math.isclose(mse,row['guided_moments']['base_guided_MSE'],rel_tol=1e-12,abs_tol=1e-15)
   assert [e.double().square().mean().item() for e in (ec,eu)]==row['guided_moments']['diagnostics']['original_branch_MSE']
   errors[name]=mse
   if name!='D_REFERENCE_SCALAR':extra_count+=2
  if branch['source']=='D':
   for a,b in (('P_REFERENCE_SCALAR','C'),('P_REFERENCE_UNIT','D_REFERENCE_UNIT')):
    assert all(torch.equal(a,b) for a,b in zip(x[a],x[b]));equal_count+=2;D_controls+=2
  points.append({'flow':group['flow'],'event':event['event']['id'],'source':branch['source'],'age':point['age'],'guided_MSE':errors})
  assert sha(path)==art['sha256']
  return {k:v for k,v in x.items() if k in basekeys}
 raw=base_audit(view,s/'CPU-artifacts'/('flow_ON' if group['flow'] else 'flow_OFF'),loader,shape)
 assert len(points)==24 and extra_count==192 and equal_count==48
 assert raw['actual_tensors_reloaded']==388 and raw['actual_direct_tensor_comparisons']==162
 assert raw['files']==group['actual_tensor_audit']['files']
 tensors+=raw['actual_tensors_reloaded']+extra_count;direct+=raw['actual_direct_tensor_comparisons']+equal_count
 files.extend(raw['files']);all_points.extend(points)
assert (len(files),tensors,direct,len(all_points),restores,D_controls)==(88,1160,420,48,240,96)
assert {f['path'] for f in files}=={str(p.resolve()) for p in (s/'CPU-artifacts').rglob('*.pt')}
assert sha(project/'reports/budget.json')==budget_before and not torch.cuda.is_initialized()
assert {n:sha(s/n) for n in payload}==payload and sha(s/'result.json')==receipt['result_sha256']
originals={}
for name in ('launch.json','receipt.json','registration.json','result.json','CPU.log'):
 p=s/name;raw=p.read_bytes();originals[name]={'remote_path':str(p),'sha256':sha(p),'bytes':len(raw),'gzip_base64':base64.b64encode(gzip.compress(raw,mtime=0)).decode()}
print(json.dumps({'status':'P_REFERENCE_SAME_STATE_COMPLETE_CPU_INDEPENDENTLY_AUDITED_NOT_GPU','original_PIDs_absent':ids,
 'source_revision':receipt['source_revision'],'CPU_wall_seconds':receipt['CPU_wall_seconds'],'frozen_source_files_unchanged':444,
 'actual_reloaded_files':len(files),'actual_reloaded_tensors':tensors,'actual_direct_tensor_comparisons':direct,
 'same_state_points':48,'candidate_restore_operations':restores,'D_source_control_equalities':D_controls,
 'all_five_independent_error_records':all_points,'CUDA_initialized':False,'GPU_submissions':0,'ledger_written':False,
 'observed_unix':time.time(),'GPU_inflight_ledger_observation':json.loads((project/'reports/budget.json').read_text()),'files':files,'originals':originals}))
'''


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();assert not args.output.exists()
    root=Path(__file__).resolve().parents[1]
    launch=json.loads((root/'reports/wc_p_reference_same_state_cpu_r3_launch_20261011.json').read_text())
    raw=subprocess.check_output(['git','show',launch['source_revision']+':manifests/wc_p_reference_same_state_cpu_r3_20261011.json'],cwd=root)
    packet={'launch':launch,'registration_sha256':hashlib.sha256(raw).hexdigest()}
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen',
        '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'],
        input='P='+repr(packet)+'\n'+REMOTE,text=True,capture_output=True)
    if call.returncode:raise RuntimeError(call.stderr[-3500:])
    value=json.loads(call.stdout)
    if value['status'].startswith('WAIT_'):print(json.dumps(value));return
    folder=root/'reports'/args.output.stem;assert not folder.exists();folder.mkdir()
    for name,entry in value['originals'].items():
        raw=base64.b64decode(entry.pop('gzip_base64'));plain=gzip.decompress(raw)
        assert hashlib.sha256(plain).hexdigest()==entry['sha256'] and len(plain)==entry['bytes']
        p=folder/(name+'.gz');p.write_bytes(raw);entry['local_path']=str(p)
    args.output.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:value[k] for k in ('status','CPU_wall_seconds','actual_reloaded_files','actual_reloaded_tensors','actual_direct_tensor_comparisons','same_state_points')}))


if __name__=='__main__':main()
