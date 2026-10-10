"""Original handles only; independent tensors, policy replay and source bytes."""
import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    root=Path(__file__).resolve().parents[1]
    launch=json.loads((root/'reports/wc_e1_diag8_sampling_cpu_r1_launch_20261011.json').read_text())
    source=subprocess.check_output(['git','show',launch['source_revision']+':scripts/deploy_wc_e1_diag8_sampling_cpu_r1.py'],cwd=root)
    tree=ast.parse(source);driver=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id=='DRIVER' for t in n.targets))
    packet={'launch':launch,'driver_sha256':hashlib.sha256(driver.encode()).hexdigest()}
    code='P='+repr(packet)+'\n'+r'''import base64,gzip,hashlib,json,pathlib,time
L=P['launch'];s=pathlib.Path(L['stage']);root=s.parents[1]
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(4<<20),b''):h.update(chunk)
 return h.hexdigest()
r=json.loads((s/'receipt.json').read_text());pids=[r['pid'],r.get('child_pid')]
live=[p for p in pids if p and pathlib.Path('/proc/'+str(p)).exists()]
if live:print(json.dumps({'capture':{'status':'ORIGINAL_E1_DIAG8_CPU_LIVE','PIDs':live},'native':{}}));raise SystemExit(0)
assert r['pid']==L['supervisor_pid'] and r['source_revision']==L['source_revision']
assert sha(s/'driver.py')==P['driver_sha256'] and sha(s/'registration.json')==L['registration_sha256']
reg=json.loads((s/'registration.json').read_text())
assert {n:sha(s/n) for n in reg['payload_sha256']}==reg['payload_sha256']==r['payload_after_sha256']
assert {n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']}==reg['runtime_source_sha256']
assert r['budget_before_sha256']==r['budget_after_sha256']==sha(root/'reports/budget.json')
assert r['GPU_submissions']==0 and not r['ledger_written']
independent={}
if r['exit_code']==0:
 assert r['child_exit_code']==0 and r['status']=='E1_DIAG8_COMPLETE_CPU_EXIT0_NOT_GPU_CAPACITY'
 assert sha(s/'result.json')==r['result_sha256']
 import os;os.environ['CUDA_VISIBLE_DEVICES']=''
 import torch;torch.set_num_threads(2);assert not torch.cuda.is_initialized()
 torch.cuda._lazy_init=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('Independent E1 CPU audit forbids CUDA'))
 def digest(value):
  h=hashlib.sha256()
  def walk(x):
   if isinstance(x,torch.Tensor):
    assert bool(torch.isfinite(x).all());h.update(str((str(x.dtype),list(x.shape))).encode())
    h.update(x.detach().contiguous().reshape(-1).view(torch.uint8).numpy().tobytes())
   elif isinstance(x,dict):
    for k in sorted(x):h.update(str(k).encode());walk(x[k])
   elif isinstance(x,(list,tuple)):
    h.update(type(x).__name__.encode())
    for item in x:walk(item)
   else:h.update(repr(x).encode())
  walk(value);return h.hexdigest()
 import sys,dataclasses
 sys.path.insert(0,str(s/'src'))
 from wcomr.source_aware_current_birth_control_r1 import CurrentBirthCPDController
 from wcomr.source_aware_phase_control import CreationPhasePrior
 from wcomr.source_aware_cpd_control import Costs
 from wcomr.cfg_ra_joint_control import Calibration
 calibration=Calibration('SYNTHETIC_E1_CURRENT_BIRTH_PRIOR',
  {(a,t):1. for a in range(1,36) for t in range(a+1,37)},{t:1. for t in range(1,37)})
 value=json.loads((s/'result.json').read_text())
 assert value['status']=='E1_DIAG8_COMPLETE_SAMPLING_CPU_PASS_NOT_REAL_GPU_CAPACITY'
 assert value['planned_scope']==reg['CPU_scope'] and value['payload_sha256']==reg['payload_sha256']
 assert value['scope_mutation_refusals']==72 and value['arm_contract_refusals']==12 and value['actual_truncation_refusals']==8
 tensors=decisions=CPU_roundtrips=original_roundtrips=events=0;loaded={};available_files=set()
 for check in value['checks']:
  for request in check['receipt']['requests']:
   for row in request['paths']:
    if 'vector_artifact' in row:
     art=row['vector_artifact'];path=pathlib.Path(art['path']).resolve()
     assert path.is_relative_to((s/'CPU-artifacts').resolve()) and sha(path)==art['sha256'] and path.stat().st_size==art['bytes']
     data=torch.load(path,map_location='cpu',weights_only=True);available_files.add(str(path))
     assert set(data)=={'guided','final_latent'} and len(data['guided'])==36
     assert all(list(t.shape)==[1,2048,2,8,8] and t.dtype==torch.float32 and t.device.type=='cpu' for t in data['guided']+[data['final_latent']])
     assert {k:digest(v) for k,v in data.items()}==art['tensor_sha256'] and [digest(t) for t in data['guided']]==row['guided_sha256']
     tensors+=37
     if check['status']=='PASS':loaded[(check['flow'],check['arm'],request['sample_name'],row['collect'])]=data
    d=row['collection_complete']['deployment']
    controller=CurrentBirthCPDController(calibration,2.,Costs('SYNTHETIC_CPD_FULL_PAIR',3.,4.,1.),
      CreationPhasePrior('SYNTHETIC_CURRENT_BIRTH_FLOOR',.005,.3,early_creation_floor=.005,late_creation_floor=.02),
      strategy='WORKING_P_AGE_KEEP_INTERVAL')
    assert len(d['history'])==36
    for entry in d['history']:
     actual=entry['source_policy'];saved=actual['decision']
     decision=controller._choice(saved['step'],tuple(tuple(v) for v in saved['packets']),
       saved['both_sources_ready'],saved['partial_ready'],protected=saved['reason']=='actual_protected_dense')
     expected=json.loads(json.dumps(dataclasses.asdict(dataclasses.replace(decision,owner=saved['owner']))))
     assert expected==saved and controller.query_basis(decision)==actual['working_epoch_basis']
     controller.commit(decision,actual_action=entry['action'][0],pair_completed=True)
     assert entry['action']==decision.action*2
     for k,v in {'dense_anchor_after':controller.anchor,'working_kind_after':controller.working_kind,
      'working_created_step_after':controller.working_step,'creation_floor_proxy_after':controller.creation_floor,
      'accumulated_interval_proxy_after':controller.accumulated,'consecutive_P_after':controller.consecutive_P}.items():assert actual[k]==v
     decisions+=1
    assert [x['step'] for x in row['P0_roundtrips']]==[12,30,35,36]
    for snapshot in row['P0_roundtrips']:
     assert snapshot['complete_additional_state_restored'] and snapshot['physical_state_restored']
     if check['arm'].startswith('CPU'):
      assert snapshot['CPU_owned_storage_version']=='R1' and snapshot['original_logical_cap_unchanged']
      assert snapshot['owned_storage_inventory']['unique_GPU_storage_bytes']==0;CPU_roundtrips+=1
     else:original_roundtrips+=1
  events+=len(check['events'])
 assert {str(p.resolve()) for p in (s/'CPU-artifacts').rglob('*.pt')}==available_files
 for flow in (False,True):
  for a,b in (('ORIGINAL_COLD','CPU_COLD'),('ORIGINAL_PREFIX','CPU_PREFIX')):
   keys=[k for k in loaded if k[:2]==(flow,a)]
   for key in keys:
    left,right=loaded[key],loaded[(flow,b,*key[2:])]
    assert all(torch.equal(x,y) for x,y in zip(left['guided']+[left['final_latent']],right['guided']+[right['final_latent']]))
  for impl in ('ORIGINAL','CPU'):
   a=loaded[(flow,impl+'_COLD','human_199','A_CPD_BETA1_ONE_PHASE')]
   b=loaded[(flow,impl+'_PREFIX','human_199','A_CPD_BETA1_ONE_PHASE')]
   assert all(torch.equal(x,y) for x,y in zip(a['guided']+[a['final_latent']],b['guided']+[b['final_latent']]))
 assert (tensors,decisions,CPU_roundtrips,original_roundtrips,events)==(888,1008,56,56,336)
 assert not torch.cuda.is_initialized()
 independent={'actual_vector_files':24,'actual_tensors_reloaded':tensors,'policy_decisions_independently_replayed':decisions,
  'CPU_owned_roundtrips':CPU_roundtrips,'original_roundtrips':original_roundtrips,'metadata_events':events,
  'both_flows_storage_and_cold_prefix_Toy_tensors_direct_equal':True,'CUDA_initialized':False}
names=['receipt.json','registration.json','launch.json','driver.py','driver.log','CPU.log']
names += [n for n in ('result.json','result.failure.json') if (s/n).exists()]
native={}
for n in names:
 raw=(s/n).read_bytes();packed=gzip.compress(raw,compresslevel=6,mtime=0)
 native[n]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'compressed_sha256':hashlib.sha256(packed).hexdigest(),'base64':base64.b64encode(packed).decode()}
capture={'status':'E1_DIAG8_ORIGINAL_CPU_TERMINAL_NOT_GPU_CAPACITY','source_revision':L['source_revision'],
 'original_PIDs_absent':pids,'exit_code':r['exit_code'],'CPU_wall_seconds':r['CPU_wall_seconds'],
 'payload_files':len(reg['payload_sha256']),'budget_sha256':r['budget_after_sha256'],'independent_tensor_and_policy_audit':independent,
 'GPU_submissions':0,'ledger_written':False,'observed_unix':time.time()}
print(json.dumps({'capture':capture,'native':native}))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen',
        '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'],input=code,text=True,capture_output=True)
    if call.returncode:raise RuntimeError(call.stderr[-3000:])
    value=json.loads(call.stdout)
    if not value['native']:print(json.dumps(value['capture']));return 2
    prefix=root/'reports/wc_e1_diag8_sampling_cpu_r1_terminal_20261011_'
    target=Path(str(prefix)+'capture.json');assert not target.exists()
    proof=value['capture'];proof['files']={};objects={}
    for n,item in value['native'].items():
        packed=base64.b64decode(item['base64'],validate=True);raw=gzip.decompress(packed)
        assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
        assert hashlib.sha256(packed).hexdigest()==item['compressed_sha256']
        path=Path(str(prefix)+n+'.native.gz');assert not path.exists();path.write_bytes(packed)
        proof['files'][n]={k:v for k,v in item.items() if k!='base64'}
        proof['files'][n]['local_path']=str(path.relative_to(root))
        if n.endswith('.json'):objects[n]=json.loads(raw)
    assert objects['launch.json']==launch
    reg=objects['registration.json']
    assert reg==json.loads((root/'manifests/wc_e1_diag8_sampling_cpu_r1_preregistration_20261011.json').read_text())
    for n in reg['new_local_files']:
        raw=subprocess.check_output(['git','show',launch['source_revision']+':'+n],cwd=root)
        assert hashlib.sha256(raw).hexdigest()==reg['payload_sha256'][n],n
    proof['original_source_and_full_scope_independently_verified']=True
    target.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({k:v for k,v in proof.items() if k!='files'}));return 0


if __name__=='__main__':raise SystemExit(main())
