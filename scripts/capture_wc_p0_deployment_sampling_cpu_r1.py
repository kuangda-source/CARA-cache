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
    launch_path = Path('reports/wc_p0_deployment_sampling_cpu_r1_launch_20261010.json')
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
 result=json.loads((stage/'result.json').read_text());tensors=refs=0
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
   for method,ref in [('OFF','SOURCE_D6'),('DENSE_CONTROL','SOURCE_D6'),('FULL_P_DECLARED_P','TRUE_D_REFERENCE')]:
    a,b=loaded[method],loaded[ref]
    assert all(torch.equal(x,y) for x,y in zip(a['guided']+[a['final_latent']],b['guided']+[b['final_latent']]))
   for method in ('ROTATION_050','RANDOM_050','ROTATION_075','RANDOM_075'):
    a,b=loaded[method],loaded['REF_'+method]
    for x,y in zip(a['guided']+[a['final_latent']],b['guided']+[b['final_latent']]):torch.testing.assert_close(x,y,rtol=1e-5,atol=2e-6)
    refs+=1
 assert (tensors,refs)==(3848,32) and not torch.cuda.is_initialized()
 reload_result={'actual_tensors':tensors,'full_partial_references':refs,'dense_and_OFF_direct_equal':True,'CUDA_initialized':False}
files=['receipt.json','registration.json','launch.json','driver.py','driver.log','test.log']
files.extend(n for n in ('result.json','result.failure.json') if (stage/n).exists())
native={}
for n in files:
 raw=(stage/n).read_bytes();packed=gzip.compress(raw,mtime=0)
 native[n]={'path':str(stage/n),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
  'compressed_sha256':hashlib.sha256(packed).hexdigest(),'base64':base64.b64encode(packed).decode()}
print(json.dumps({'capture':{'status':'FULL_SAMPLING_ORIGINAL_CPU_TERMINAL','source_revision':L['source_revision'],
 'original_PIDs_absent':pids,'exit_code':r['exit_code'],'CPU_wall_seconds':r['CPU_wall_seconds'],
 'GPU_submissions':0,'ledger_written':False,'independent_tensor_reload':reload_result,'actual_CPU_artifacts':artifacts,'observed_unix':time.time()},'native':native}))
'''
    call = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'],
                          input=code,text=True,capture_output=True,timeout=55)
    if call.returncode:
        raise RuntimeError(call.stderr[-3000:])
    value = json.loads(call.stdout)
    if not value['native']:
        print(json.dumps(value['capture'])); return 2
    prefix='reports/wc_p0_deployment_sampling_cpu_r1_terminal_20261010_'
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
        gitreg=subprocess.check_output(['git','show',launch['source_revision']+':manifests/wc_p0_deployment_sampling_cpu_r1_preregistration_20261010.json'])
        assert hashlib.sha256(gitreg).hexdigest()==launch['registration_sha256']
        assert json.loads(gitreg)==objects['registration.json']
        for n,digest in objects['registration.json']['payload_sha256'].items():
            assert hashlib.sha256(subprocess.check_output(['git','show',launch['source_revision']+':'+n])).hexdigest()==digest
        deploy=subprocess.check_output(['git','show',launch['source_revision']+':scripts/deploy_wc_p0_deployment_sampling_cpu_r1.py'])
        tree=ast.parse(deploy)
        drivers=[n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='DRIVER' for t in n.targets)]
        assert len(drivers)==1 and hashlib.sha256(ast.literal_eval(drivers[0]).encode()).hexdigest()==launch['driver_sha256']
        if proof['exit_code']==0:
            receipt=objects['receipt.json']; result=objects['result.json']
            assert receipt['child_exit_code']==0 and proof['files']['result.json']['sha256']==receipt['result_sha256']
            assert result['status']=='P0_DEPLOYMENT_FULL_SAMPLER_ACTUAL_CPU_PASS_NOT_REAL_MODEL'
            assert result['planned_scope']==objects['registration.json']['CPU_scope']
            assert (result['actual_complete_solver_updates'],result['actual_normal_net_calls'],result['actual_all_tensors_reloaded'])==(7488,14976,3848)
            assert not result['CUDA_initialized'] and result['GPU_submissions']==0
            assert result['actual_UniPC_source_executed'] and not result['real_Cosmos_CAL_or_video_or_quality_or_clean_latency_claim']
            assert proof['independent_tensor_reload']['actual_tensors']==3848
            assert proof['independent_tensor_reload']['full_partial_references']==32
            good=[c for c in result['checks'] if c['status']=='PASS'];bad=[c for c in result['checks'] if c['status']=='EXPECTED_FAILURE']
            assert len(good)==len(bad)==2 and {c['flow'] for c in good}=={False,True}
            actual={v['path']:v for v in proof['actual_CPU_artifacts']}
            for check in good:
                raw=check['actual_tensor_audit'];assert len(raw['files'])==52
                assert (raw['actual_guided_reloaded'],raw['actual_latents_reloaded'])==(1872,52)
                assert check['P_source_reuse_C_checks']==180 and check['consecutive_P_checks']==100
                assert len(check['mutation_refusals'])==7 and check['actual_artifact_truncation_refused']
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
