#!/usr/bin/env python3
"""Capture original full-sampling CPU evidence, without redispatch or GPU work."""
import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    launch_path = Path('reports/wc_current_birth_sampling_cpu_r2_launch_20261010.json')
    launch = json.loads(launch_path.read_text())
    code = 'L=' + repr(launch) + '\n' + r'''
import base64,gzip,hashlib,json,pathlib,time
stage=pathlib.Path(L['stage']);root=stage.parent.parent
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return h.hexdigest()
r=json.loads((stage/'receipt.json').read_text());pids=[r['pid'],r.get('child_pid')]
live=[p for p in pids if p and pathlib.Path('/proc/'+str(p)).exists()]
if live:
 print(json.dumps({'capture':{'status':'ORIGINAL_FULL_SAMPLING_CPU_STILL_LIVE','PIDs':live},'native':{}}));raise SystemExit(0)
assert r['pid']==L['supervisor_pid'] and r['source_revision']==L['source_revision']
assert sha(stage/'driver.py')==L['driver_sha256'] and sha(stage/'registration.json')==L['registration_sha256']
reg=json.loads((stage/'registration.json').read_text())
assert {n:sha(stage/n) for n in reg['payload_sha256']}==r['payload_after_sha256']==reg['payload_sha256']
assert {n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']}==reg['runtime_source_sha256']
assert r['GPU_submissions']==0 and not r['ledger_written'] and not r['GPU_lock_acquired']
artifacts=[]
for p in sorted((stage/'CPU-artifacts').rglob('*')):
 if p.is_file():artifacts.append({'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha(p)})
reload_result={}
if r['exit_code']==0:
 import os
 os.environ['CUDA_VISIBLE_DEVICES']=''
 import torch
 torch.set_num_threads(2)
 assert not torch.cuda.is_initialized()
 torch.cuda._lazy_init=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('Independent capture forbids CUDA'))
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
    for a in x:walk(a)
   else:h.update(repr(x).encode())
  walk(value);return h.hexdigest()
 import sys,dataclasses
 sys.path.insert(0,str(stage/'src'))
 from wcomr.source_aware_current_birth_control_r1 import CurrentBirthCPDController
 from wcomr.source_aware_phase_control import CreationPhasePrior
 from wcomr.source_aware_cpd_control import Costs
 from wcomr.cfg_ra_joint_control import Calibration
 calibration=Calibration('SYNTHETIC_CREATION_PHASE_FULL36_RA_PRIOR',
  {(a,s):1. for a in range(1,36) for s in range(a+1,37)},{s:1. for s in range(1,37)})
 result=json.loads((stage/'result.json').read_text());tensors=refs=policy_decisions=0
 for check in result['checks']:
  if check['status']!='PASS':continue
  for request in check['receipt']['requests']:
   loaded={}
   for row in request['paths']:
    art=row['vector_artifact'];p=pathlib.Path(art['path']).resolve()
    assert p.is_relative_to((stage/'CPU-artifacts').resolve()) and sha(p)==art['sha256'] and p.stat().st_size==art['bytes']
    x=torch.load(p,map_location='cpu',weights_only=True)
    assert set(x)=={'guided','final_latent'} and len(x['guided'])==36
    assert all(list(t.shape)==[1,2048,2,8,8] and t.dtype==torch.float32 and t.device.type=='cpu' and bool(torch.isfinite(t).all()) for t in x['guided']+[x['final_latent']])
    assert {k:digest(v) for k,v in x.items()}==art['tensor_sha256']
    assert [digest(t) for t in x['guided']]==row['guided_sha256'];loaded[row['collect']]=x;tensors+=37
    deployment=row['collection_complete'].get('deployment')
    if deployment is not None:
     spec=check['synthetic_policy_specs'][row['collect']]
     prior=CreationPhasePrior(**spec['partial_prior']) if spec['partial_prior'] is not None else None
     controller=CurrentBirthCPDController(calibration,spec['threshold'],Costs(**spec['costs']),prior,
      strategy=check['working_epoch_strategy'])
     assert len(deployment['history'])==36
     for entry in deployment['history']:
      actual=entry['source_policy'];saved=actual['decision']
      decision=controller._choice(saved['step'],tuple(tuple(v) for v in saved['packets']),
       saved['both_sources_ready'],saved['partial_ready'],protected=saved['reason']=='actual_protected_dense')
      expected=json.loads(json.dumps(dataclasses.asdict(dataclasses.replace(decision,owner=saved['owner']))))
      assert expected==saved and controller.query_basis(decision)==actual['working_epoch_basis']
      controller.commit(decision,actual_action=entry['action'][0],pair_completed=True)
      for key,value in {'dense_anchor_after':controller.anchor,'working_kind_after':controller.working_kind,
       'working_created_step_after':controller.working_step,'creation_floor_proxy_after':controller.creation_floor,
       'accumulated_interval_proxy_after':controller.accumulated,'consecutive_P_after':controller.consecutive_P}.items():
       assert actual[key]==value
      assert entry['action']==decision.action*2;policy_decisions+=1
   for method,ref in [('SOURCE_RA','DYNAMIC_NO_P'),('CPD','A_CPD_OFF')]:
    a,b=loaded[method],loaded[ref]
    assert all(torch.equal(x,y) for x,y in zip(a['guided']+[a['final_latent']],b['guided']+[b['final_latent']]))
   a,b=loaded['CPD'],loaded['REF_CPD']
   for x,y in zip(a['guided']+[a['final_latent']],b['guided']+[b['final_latent']]):torch.testing.assert_close(x,y,rtol=1e-5,atol=2e-6)
   refs+=1
 assert (tensors,refs,policy_decisions)==(4736,16,4032) and not torch.cuda.is_initialized()
 reload_result={'actual_tensors':tensors,'full_partial_references':refs,'independently_replayed_working_policy_decisions':policy_decisions,'dense_and_OFF_direct_equal':True,'CUDA_initialized':False}
files=['receipt.json','registration.json','launch.json','driver.py','driver.log','test.log']
files.extend(n for n in ('result.json','result.failure.json') if (stage/n).exists())
native={}
for n in files:
 raw=(stage/n).read_bytes();packed=gzip.compress(raw,compresslevel=1,mtime=0)
 native[n]={'path':str(stage/n),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
  'compressed_sha256':hashlib.sha256(packed).hexdigest(),'base64':base64.b64encode(packed).decode()}
print(json.dumps({'capture':{'status':'FULL_SAMPLING_ORIGINAL_CPU_TERMINAL','source_revision':L['source_revision'],
 'original_PIDs_absent':pids,'exit_code':r['exit_code'],'CPU_wall_seconds':r['CPU_wall_seconds'],
 'GPU_submissions':0,'ledger_written':False,'independent_tensor_reload':reload_result,'actual_CPU_artifacts':artifacts,'observed_unix':time.time()},'native':native}))
'''
    call = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'],
                          input=code,text=True,capture_output=True,timeout=600)
    if call.returncode:
        raise RuntimeError(call.stderr[-3000:])
    value = json.loads(call.stdout)
    if not value['native']:
        print(json.dumps(value['capture'])); return 2
    prefix='reports/wc_current_birth_sampling_cpu_r2_terminal_20261010_'
    dest=Path(prefix+'capture.json'); assert not dest.exists()
    proof=value['capture']; proof['files']={}; objects={}
    for n,item in value['native'].items():
        packed=base64.b64decode(item['base64'],validate=True); raw=gzip.decompress(packed)
        assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
        assert hashlib.sha256(packed).hexdigest()==item['compressed_sha256']
        p=Path(prefix+n+'.native.gz'); assert not p.exists(); p.write_bytes(packed)
        proof['files'][n]={k:v for k,v in item.items() if k!='base64'}
        proof['files'][n]['local_path']=str(p)
        if n.endswith('.json'): objects[n]=json.loads(raw)
    try:
        assert objects['launch.json']==launch
        gitreg=subprocess.check_output(['git','show',launch['source_revision']+':manifests/wc_current_birth_sampling_cpu_r2_preregistration_20261010.json'])
        assert hashlib.sha256(gitreg).hexdigest()==launch['registration_sha256']
        assert json.loads(gitreg)==objects['registration.json']
        for n,digest in objects['registration.json']['payload_sha256'].items():
            assert hashlib.sha256(subprocess.check_output(['git','show',launch['source_revision']+':'+n])).hexdigest()==digest
        deploy=subprocess.check_output(['git','show',launch['source_revision']+':scripts/deploy_wc_current_birth_sampling_cpu_r2.py'])
        tree=ast.parse(deploy)
        drivers=[n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='DRIVER' for t in n.targets)]
        assert len(drivers)==1 and hashlib.sha256(ast.literal_eval(drivers[0]).encode()).hexdigest()==launch['driver_sha256']
        if proof['exit_code']==0:
            receipt=objects['receipt.json']; result=objects['result.json']
            assert receipt['child_exit_code']==0 and proof['files']['result.json']['sha256']==receipt['result_sha256']
            assert result['status']=='CURRENT_BIRTH_FULL_SAMPLER_CPU_PASS_NOT_REAL_MODEL'
            assert result['creation_phase_early_P_pairs']>0 and result['creation_phase_late_P_pairs']>0
            assert result['current_birth_rule']==objects['registration.json']['current_P_birth_rule']
            assert result['additional_current_birth_mutation_refusals']==12
            assert result['P_birth_floor_and_actual_D_history_preserved'] and result['explicit_P_source_transfer_queries']>0
            assert result['original_full128_scope_retained_per_strategy'] and result['same_synthetic_creation_phase_inputs']
            assert result['registered_strategies']==objects['registration.json']['CPU_scope']['working_epoch_strategies']
            assert result['planned_scope']==objects['registration.json']['CPU_scope']
            assert (result['actual_complete_solver_updates'],result['actual_normal_net_calls'],result['actual_all_tensors_reloaded'])==(9216,18432,4736)
            assert not result['CUDA_initialized'] and result['GPU_submissions']==0
            assert result['actual_UniPC_source_executed'] and not result['real_Cosmos_CAL_or_video_or_quality_or_clean_latency_claim'] and result['explicit_synthetic_policy_parameters']
            assert proof['independent_tensor_reload']['actual_tensors']==4736
            assert proof['independent_tensor_reload']['full_partial_references']==16
            assert proof['independent_tensor_reload']['independently_replayed_working_policy_decisions']==4032
            good=[c for c in result['checks'] if c['status']=='PASS'];bad=[c for c in result['checks'] if c['status']=='EXPECTED_FAILURE']
            assert len(good)==len(bad)==4 and {c['flow'] for c in good}=={False,True}
            actual={v['path']:v for v in proof['actual_CPU_artifacts']}
            for check in good:
                raw=check['actual_tensor_audit'];assert len(raw['files'])==32
                assert (raw['actual_guided_reloaded'],raw['actual_latents_reloaded'])==(1152,32)
                assert check['P_source_C_pairs']>0 and check['consecutive_P_pairs']>0 and check['actual_P_pairs']>0 and check['original_RA_policy_comparisons']==144
                assert len(check['mutation_refusals'])==8 and check['actual_artifact_truncation_refused']
                assert len(check['working_epoch_mutation_refusals'])==3
                assert set(check['current_birth_mutation_refusals'])=={'foreign_current_birth_rule','old_P_drift_added_again','C_drops_retained_P_floor'}
                for item in raw['files']:
                    assert actual[item['path']]['bytes']==item['bytes'] and actual[item['path']]['sha256']==item['sha256']
            assert all(c['complete_scope_retained'] and c['initial_full_state_restored'] and c['installed_MLP_methods_restored'] for c in bad)
        proof['independent_source_complete_results_and_actual_artifact_hashes_verified']=True
    except BaseException as error:
        proof['independent_check_error']={'type':type(error).__name__,'message':str(error)}
        dest.write_text(json.dumps(proof,indent=2)+'\n'); raise
    dest.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({k:v for k,v in proof.items() if k not in ('files','actual_CPU_artifacts')})); return 0


if __name__=='__main__': raise SystemExit(main())
