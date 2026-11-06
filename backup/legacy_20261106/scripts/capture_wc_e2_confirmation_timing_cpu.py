#!/usr/bin/env python3
"""Read one original E2 CPU terminal; retain failure, raw bytes and scope."""
import argparse
import ast
import base64
import gzip
import hashlib
import json
import re
from pathlib import Path
import subprocess


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--launch',type=Path,required=True)
    parser.add_argument('--prefix',type=Path,required=True)
    args=parser.parse_args();launch=json.loads(args.launch.read_text())
    assert not Path(str(args.prefix)+'capture.json').exists()
    code='L='+repr(launch)+'\n'+r'''import base64,gzip,hashlib,json,pathlib,time
s=pathlib.Path(L['stage']);root=s.parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return h.hexdigest()
r=json.loads((s/'receipt.json').read_text());pids=[r['pid'],r['child_pid']]
live=[p for p in pids if pathlib.Path('/proc/'+str(p)).exists()]
if live:print(json.dumps({'capture':{'status':'ORIGINAL_E2_CPU_STILL_RUNNING','PIDs':live},'native':{}}));raise SystemExit(0)
assert r['pid']==L['supervisor_pid'] and r['source_revision']==L['source_revision']
assert sha(s/'registration.json')==L['registration_sha256']
reg=json.loads((s/'registration.json').read_text())
assert {n:sha(s/n) for n in reg['payload_sha256']}==reg['payload_sha256']==r['payload_after_sha256']
assert {n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']}==reg['runtime_source_sha256']
assert sha(root/'reports/budget.json')==r['budget_after_sha256']==r['budget_before_sha256']
assert r['GPU_submissions']==0 and not r['ledger_written']
artifacts=[{'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted((s/'CPU-artifacts').rglob('*')) if p.is_file()]
independent={}
if r['exit_code']==0:
 import os;os.environ['CUDA_VISIBLE_DEVICES']=''
 import torch;torch.set_num_threads(2);assert not torch.cuda.is_initialized()
 torch.cuda._lazy_init=lambda *a,**k:(_ for _ in ()).throw(RuntimeError('Capture prohibits CUDA'))
 def digest(value):
  h=hashlib.sha256()
  def walk(x):
   if isinstance(x,torch.Tensor):
    assert bool(torch.isfinite(x).all());h.update(str((str(x.dtype),list(x.shape))).encode());h.update(x.detach().contiguous().reshape(-1).view(torch.uint8).numpy().tobytes())
   elif isinstance(x,dict):
    for k in sorted(x):h.update(str(k).encode());walk(x[k])
   elif isinstance(x,(list,tuple)):
    h.update(type(x).__name__.encode())
    for a in x:walk(a)
   else:h.update(repr(x).encode())
  walk(value);return h.hexdigest()
 result=json.loads((s/'result.json').read_text());guided=final=parity=0
 for c in result['checks']:
  if c['status']!='PASS':continue
  assert len(c['receipt']['slots'])==76 and c['receipt']['initial_state_restored']
  old_result=json.loads((pathlib.Path(reg['old_A_CPU_stage'])/'result.json').read_text())
  old=next(v for v in old_result['checks'] if v['status']=='PASS' and v['flow']==c['flow'])['receipt']['batch']['requests'][0]['paths']
  representatives={};paired_inputs={}
  for row in c['receipt']['slots']:
   art=row['vector_artifact'];p=pathlib.Path(art['path']);assert p.resolve().is_relative_to((s/'CPU-artifacts').resolve())
   assert p.stat().st_size==art['bytes'] and sha(p)==art['sha256']
   x=torch.load(p,map_location='cpu',weights_only=True)
   expected={'guided','final_latent'} if row['mode']=='AUDIT' else {'final_latent'}
   assert set(x)==expected
   tensors=x.get('guided',[])+[x['final_latent']]
   assert all(t.dtype==torch.float32 and list(t.shape)==[1,2048,2,8,8] and bool(torch.isfinite(t).all()) for t in tensors)
   assert {k:digest(v) for k,v in x.items()}==art['tensor_sha256'];final+=1
   if row['mode']=='AUDIT':
    identity=(row['first_velocity_input_sha256'],row['condition_fields_before'],row['prepared_input_calls'][0]['prepared'],row['rng_after'])
    if row['request_name'] in paired_inputs:assert identity==paired_inputs[row['request_name']]
    else:paired_inputs[row['request_name']]=identity
    assert row['condition_fields_before']==row['condition_fields_after']
    assert len(x['guided'])==36 and [digest(t) for t in x['guided']]==row['guided_sha256'];guided+=36
   if row['section']=='PARITY':
    representatives[row['method']]=(row,x)
    old_row=next(v for v in old if v['method']==row['method']);old_art=old_row['vector_artifact'];p=pathlib.Path(old_art['path'])
    assert sha(p)==old_art['sha256'];before=torch.load(p,map_location='cpu',weights_only=True)
    assert all(torch.equal(a,b) for a,b in zip(before['guided']+[before['final_latent']],x['guided']+[x['final_latent']]))
    assert row['actions']==old_row['actions'];parity+=1
   if row['section']=='TIMING' and row['request_name']==c['receipt']['slots'][0]['request_name']:
    a,b=representatives[row['method']]
    assert row['actions']==a['actions'] and torch.equal(x['final_latent'],b['final_latent'])
    assert row['video_artifact']['sha256']==a['video_artifact']['sha256']
 assert (guided,final,parity)==(3168,152,8)
 independent={'guided_tensors':guided,'final_latents':final,'old_A_direct_parity_paths':parity,'CUDA_initialized':False}
native={}
for n in ['receipt.json','registration.json','launch.json','driver.py','driver.log','CPU.log']+[n for n in ['result.json','result.failure.json'] if (s/n).exists()]:
 raw=(s/n).read_bytes();packed=gzip.compress(raw,compresslevel=1,mtime=0)
 native[n]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'packed_sha256':hashlib.sha256(packed).hexdigest(),'base64':base64.b64encode(packed).decode()}
print(json.dumps({'capture':{'status':'E2_ORIGINAL_CPU_TERMINAL','source_revision':L['source_revision'],'exit_code':r['exit_code'],'original_PIDs_absent':pids,'CPU_wall_seconds':r['CPU_wall_seconds'],'budget_sha256':r['budget_after_sha256'],'actual_artifacts':artifacts,'independent_tensor_reload':independent,'GPU_submissions':0,'observed_unix':time.time()},'native':native}))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'],input=code,text=True,capture_output=True)
    if call.returncode:raise RuntimeError(call.stderr[-2500:])
    value=json.loads(call.stdout)
    if not value['native']:print(json.dumps(value['capture']));return 2
    proof=value['capture'];proof['files']={};objects={}
    for n,v in value['native'].items():
        packed=base64.b64decode(v['base64'],validate=True);raw=gzip.decompress(packed)
        assert hashlib.sha256(raw).hexdigest()==v['sha256'] and len(raw)==v['bytes']
        assert hashlib.sha256(packed).hexdigest()==v['packed_sha256']
        path=Path(str(args.prefix)+n+'.native.gz');assert not path.exists();path.write_bytes(packed)
        proof['files'][n]={k:x for k,x in v.items() if k!='base64'};proof['files'][n]['local_path']=str(path)
        if n.endswith('.json'):objects[n]=json.loads(raw)
    assert objects['launch.json']==launch
    registration=objects['registration.json']
    assert proof['files']['registration.json']['sha256']==launch['registration_sha256']
    for n,h in registration['payload_sha256'].items():
        if n!=registration['historical_plan_bytes_preserved']:
            assert hashlib.sha256(subprocess.check_output(['git','show',launch['source_revision']+':'+n])).hexdigest()==h
    driver_path='scripts/deploy_wc_e2_confirmation_timing_cpu_'+re.search(r'cpu-(r[0-9]+)-',launch['stage']).group(1)+'.py'
    tree=ast.parse(subprocess.check_output(['git','show',launch['source_revision']+':'+driver_path]))
    driver=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='DRIVER' for t in n.targets))
    assert hashlib.sha256(driver.encode()).hexdigest()==proof['files']['driver.py']['sha256']
    if proof['exit_code']==0:
        result=objects['result.json'];receipt=objects['receipt.json']
        assert receipt['child_exit_code']==0 and receipt['result_sha256']==proof['files']['result.json']['sha256']
        assert result['status']=='E2_FULL76_SAMPLER_CPU_PASS_NOT_REAL_MODEL'
        assert result['successful_complete_paths']==152 and result['actual_guided_reloaded']==3168 and result['actual_final_latents_reloaded']==152
        assert result['old_A_saved_all36_and_final_parity_paths']==8 and not result['real_model_or_latency_or_endpoint_claim']
    proof['original_source_and_raw_identity_verified']=True
    Path(str(args.prefix)+'capture.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({k:v for k,v in proof.items() if k not in ('files','actual_artifacts')}));return 0


if __name__=='__main__':raise SystemExit(main())
