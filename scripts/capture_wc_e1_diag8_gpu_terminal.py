"""Capture original E1 terminal handles, complete scope, bytes and billed cost."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--version',choices=('r1','r2'),required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1];tag='wc_e1_diag8_gpu_'+args.version
    launch=json.loads((root/'reports'/(tag+'_launch_20261011.json')).read_text())
    run='wc-e1-cold-prefix-storage-diag8-'+args.version
    config_name='e1-diag8-config.json' if args.version=='r1' else 'e1-diag8-r2-config.json'
    packet={'launch':launch,'run':run,'config_name':config_name,'version':args.version}
    code='P='+repr(packet)+'\n'+r'''import base64,fcntl,gzip,hashlib,json,pathlib,subprocess,time
L=P['launch'];stage=pathlib.Path(L['stage']);project=stage.parents[1];out=project/'outputs'/P['run']
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(4<<20),b''):h.update(block)
 return h.hexdigest()
s=json.loads((out/'supervisor.json').read_text());post=json.loads((stage/'post-CPU-receipt.json').read_text())
pids=[s['pid'],post['pid'],post.get('child_pid')]+[a.get('pid') for a in s['arms']]
live=[p for p in pids if p and pathlib.Path('/proc/'+str(p)).exists()]
if live:print(json.dumps({'capture':{'status':'ORIGINAL_E1_HANDLES_LIVE_NOT_TERMINAL','PIDs':live},'native':{}}));raise SystemExit(0)
assert s['pid']==L['GPU_supervisor_pid'] and post['pid']==L['post_CPU_pid']
assert s['source_revision']==post['source_revision']==L['source_revision']
assert s['status']=='E1_DIAG8_EXITED_REQUIRES_COMPLETE_SCOPE_RAW_CPU_AUDIT'
c=json.loads((stage/P['config_name']).read_text());assert sha(stage/P['config_name'])==L['selected_config_sha256']==s['config_sha256']
assert {n:sha(stage/n) for n in c['payload_sha256']}==c['payload_sha256']
assert {n:sha(project/c['parent_stage']/n) for n in c['parent_import_source_sha256']}==c['parent_import_source_sha256']
assert len(s['arms'])==4 and sum(a['planned_paths'] for a in s['arms'])==8
before,after=s['budget_before'],s['budget_after']
assert abs(after['used_gpu_hours']-before['used_gpu_hours']-s['wall_seconds']/3600)<1e-12
assert after['gpu_jobs_launched']==before['gpu_jobs_launched']+1
assert not any('inflight' in n for n in after)
budget_raw=(project/'reports/budget.json').read_bytes();assert json.loads(budget_raw)==after
assert post['GPU_submissions']==0 and not post['ledger_written']
native_names=[('supervisor',out/'supervisor.json'),('GPU-launch',stage/'GPU-launch.json'),
 ('selected-config',stage/P['config_name']),('selection',stage/'selection.json'),
 ('production-CPU-receipt',stage/'production-CPU-receipt.json'),('post-CPU-receipt',stage/'post-CPU-receipt.json'),
 ('post-CPU.log',stage/'post-CPU.log'),('post-driver.log',stage/'post-driver.log'),
 ('GPU-supervisor.log',stage/'GPU-supervisor.log'),('gpu-monitor.jsonl',out/'gpu-monitor.jsonl')]
raw_audit=None
if post['exit_code']==0:
 assert post['child_exit_code']==0 and sha(out/'raw-CPU-audit.json')==post['raw_audit_sha256']
 raw_audit=json.loads((out/'raw-CPU-audit.json').read_text())
 assert raw_audit['planned_paths']==8 and len(raw_audit['slots'])==8 and len(raw_audit['arms'])==4
 assert not raw_audit['CUDA_initialized'] and not raw_audit['scientific_quality_or_clean_speed_claim']
 native_names.append(('raw-CPU-audit',out/'raw-CPU-audit.json'))
for arm in c['arms']:
 for label,path in [('receipt',out/arm['id']/'receipt.json'),('memory-observer.jsonl',out/arm['id']/'memory-observer.jsonl'),
                    ('log',out/(arm['id']+'.log'))]:
  if path.exists():native_names.append((arm['id']+'-'+label,path))
independent={}
if raw_audit is not None and any(out.rglob('*.pt')):
 import os,sys,dataclasses
 os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_CACHE=str(project/'hfhub'))
 import torch;torch.set_num_threads(2)
 def forbidden(*a,**k):raise RuntimeError('Independent E1 terminal audit forbids CUDA or downloads')
 torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
 import triton
 class ImportOnlyDriver:
  def get_benchmarker(self):return forbidden
  def __getattr__(self,n):raise RuntimeError('Independent E1 terminal audit forbids Triton: '+n)
 triton.runtime.driver.active=ImportOnlyDriver()
 sys.path[:0]=[str(stage/'src'),str(project/'runtime'),str(project/'runtime/packages/cosmos-oss'),str(project/'runtime/packages/cosmos-cuda')]
 if P['version']=='r2':
  from wcomr.e1_diag8_production_r2 import validate
 else:
  from wcomr.e1_diag8_production_r1 import validate
 _,old,inputs=validate(project,stage);calibration,specs,_,_=inputs
 from wcomr.source_aware_current_birth_control_r1 import CurrentBirthCPDController
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
 tensors=decisions=whole_paths=0;actual_files=set();loaded={};per_path=[]
 for arm,process in zip(c['arms'],s['arms']):
  receipt_path=out/arm['id']/'receipt.json'
  if not receipt_path.exists():continue
  receipt=json.loads(receipt_path.read_text());assert sha(receipt_path)==process['receipt_sha256']
  for request in receipt['batch'].get('requests',[]):
   for row in request['paths']:
    key=(arm['id'],request['sample_name'],row['collect']);record={'arm':key[0],'sample_name':key[1],'method':key[2],
     'whole_arm_exit_code':process['exit_code'],'vectors_reloaded':0,'policy_replayed':0}
    if 'vector_artifact' in row:
     art=row['vector_artifact'];path=pathlib.Path(art['path']).resolve()
     assert path.is_relative_to(out.resolve()) and sha(path)==art['sha256'] and path.stat().st_size==art['bytes']
     data=torch.load(path,map_location='cpu',weights_only=True);actual_files.add(str(path))
     assert set(data)=={'guided','final_latent'} and len(data['guided'])==36
     assert all(list(t.shape)==old['expected_real_shape'] and t.dtype==torch.float32 and t.device.type=='cpu' for t in data['guided']+[data['final_latent']])
     assert {k:digest(v) for k,v in data.items()}==art['tensor_sha256']
     assert [digest(t) for t in data['guided']]==row['guided_sha256'];tensors+=37;record['vectors_reloaded']=37
     if process['exit_code']==0:loaded[key]=data;whole_paths+=1
    deployment=row.get('collection_complete',{}).get('deployment')
    if deployment is not None:
     spec=specs[c['working_epoch_strategy']][row['collect']]
     controller=CurrentBirthCPDController(calibration,spec['threshold'],spec['costs'],spec['partial_prior'],strategy=c['working_epoch_strategy'])
     assert len(deployment['history'])==36
     for entry in deployment['history']:
      actual=entry['source_policy'];saved=actual['decision']
      decision=controller._choice(saved['step'],tuple(tuple(v) for v in saved['packets']),saved['both_sources_ready'],
       saved['partial_ready'],protected=saved['reason']=='actual_protected_dense')
      expected=json.loads(json.dumps(dataclasses.asdict(dataclasses.replace(decision,owner=saved['owner']))))
      assert expected==saved and controller.query_basis(decision)==actual['working_epoch_basis']
      controller.commit(decision,actual_action=entry['action'][0],pair_completed=True);assert entry['action']==decision.action*2
      for k,v in {'dense_anchor_after':controller.anchor,'working_kind_after':controller.working_kind,
       'working_created_step_after':controller.working_step,'creation_floor_proxy_after':controller.creation_floor,
       'accumulated_interval_proxy_after':controller.accumulated,'consecutive_P_after':controller.consecutive_P}.items():assert actual[k]==v
      decisions+=1;record['policy_replayed']+=1
    per_path.append(record)
 assert actual_files=={str(v.resolve()) for v in out.rglob('*.pt')}
 assert whole_paths==raw_audit['complete_numeric_paths']
 comparisons=[]
 for a,b in [('ORIGINAL_COLD','CPU_COLD'),('ORIGINAL_PREFIX','CPU_PREFIX'),('ORIGINAL_COLD','ORIGINAL_PREFIX'),('CPU_COLD','CPU_PREFIX')]:
  for key,left in loaded.items():
   if key[0]!=a:continue
   right=loaded.get((b,*key[1:]))
   if right is None:continue
   equal=[torch.equal(x,y) for x,y in zip(left['guided']+[left['final_latent']],right['guided']+[right['final_latent']])]
   recorded=[v for v in raw_audit['successful_storage_or_cold_prefix_comparisons'] if v['arms']==[a,b]
    and v['sample_name']==key[1] and v['method']==key[2]]
   assert len(recorded)==1 and recorded[0]['equal']==equal and recorded[0]['all_equal']==all(equal)
   comparisons.append({'arms':[a,b],'sample_name':key[1],'method':key[2],'equal':equal,'all_equal':all(equal)})
 assert not torch.cuda.is_initialized()
 independent={'actual_vector_files':len(actual_files),'actual_tensors_reloaded':tensors,
  'actual_complete_policy_decisions_replayed':decisions,'whole_arm_accepted_numeric_paths':whole_paths,
  'per_path':per_path,'direct_full36_and_final_comparisons':comparisons,'CUDA_initialized':False,
  'no_quality_or_clean_speed_claim':True}
lock=(project/'.sync/f1.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
u='GPU-cebf7119-cf03-23b9-e192-cd196332b704'
gpu=subprocess.check_output(['nvidia-smi','-i',u,'--query-gpu=uuid,memory.used','--format=csv,noheader,nounits'],text=True).strip()
apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True).strip()
capture={'status':'E1_ORIGINAL_GPU_TERMINAL_ALL8_SCOPE_CAPTURED','source_revision':L['source_revision'],
 'original_PIDs_absent':[p for p in pids if p],'planned_paths':8,'arms':s['arms'],
 'complete_numeric_paths':None if raw_audit is None else raw_audit['complete_numeric_paths'],
 'post_CPU_exit_code':post['exit_code'],'wall_seconds':s['wall_seconds'],'billed_GPUh':s['wall_seconds']/3600,
 'budget_before_used_GPUh':before['used_gpu_hours'],'budget_after_used_GPUh':after['used_gpu_hours'],
 'remaining_window_GPUh':after['cap_gpu_hours']-after['used_gpu_hours'],'GPU_jobs_launched':after['gpu_jobs_launched'],
 'payload_files':len(c['payload_sha256']),'GPU_release':gpu,'compute_apps':apps,'lock_available':True,
 'tensor_files':len(list(out.rglob('*.pt'))),'video_files':len(list(out.rglob('*.mp4'))),
 'independent_actual_tensor_and_policy_audit':independent,'observed_unix':time.time()}
native={}
for key,path in native_names+[('budget',project/'reports/budget.json')]:
 raw=path.read_bytes();packed=gzip.compress(raw,compresslevel=6,mtime=0)
 native[key]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'compressed_sha256':hashlib.sha256(packed).hexdigest(),
  'base64':base64.b64encode(packed).decode()}
print(json.dumps({'capture':capture,'native':native}))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen',
        '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'],
        input=code,text=True,capture_output=True)
    if call.returncode:raise RuntimeError(call.stderr[-3500:])
    value=json.loads(call.stdout)
    if not value['native']:print(json.dumps(value['capture']));return 2
    prefix=root/'reports'/(tag+'_terminal_20261011_native_capture_r2_')
    target=root/'reports'/(tag+'_terminal_20261011_capture.json');assert not target.exists()
    proof=value['capture'];proof['files']={};objects={}
    for key,v in value['native'].items():
        data=base64.b64decode(v['base64'],validate=True);raw=gzip.decompress(data)
        assert len(raw)==v['bytes'] and hashlib.sha256(raw).hexdigest()==v['sha256']
        assert hashlib.sha256(data).hexdigest()==v['compressed_sha256']
        path=Path(str(prefix)+key+'.native.gz');assert not path.exists();path.write_bytes(data)
        proof['files'][key]={k:x for k,x in v.items() if k!='base64'};proof['files'][key]['local_path']=str(path.relative_to(root))
        if key in ('supervisor','selected-config','GPU-launch','raw-CPU-audit','budget'):objects[key]=json.loads(raw)
    assert objects['GPU-launch']==launch
    config_ref='configs/wc_e1_diag8_production_'+args.version+'_20261011.json'
    committed=json.loads(subprocess.check_output(['git','show',launch['source_revision']+':'+config_ref],cwd=root))
    dynamic={'GPU_execution_selected','gpu_uuid','production_CPU_receipt_sha256'}
    assert {k:v for k,v in committed.items() if k not in dynamic}=={
        k:v for k,v in objects['selected-config'].items() if k not in dynamic}
    # Frozen inherited files intentionally have historical bytes. Their full
    # hash table is committed in the original config and re-hashed remotely.
    # Current launch HEAD need not contain every historical document version.
    if proof['tensor_files']==proof['video_files']==0:
        assert proof['complete_numeric_paths']==0 and not objects['raw-CPU-audit']['memory_events']
    assert objects['budget']==objects['supervisor']['budget_after']
    proof['original_source_terminal_scope_and_cost_independently_verified']=True
    target.write_text(json.dumps(proof,indent=2)+'\n')
    # Mirror authoritative settled bytes, retaining all fees and history.
    budget=gzip.decompress((root/proof['files']['budget']['local_path']).read_bytes())
    (root/'reports/budget.json').write_bytes(budget)
    print(json.dumps({k:v for k,v in proof.items() if k!='files'}));return 0


if __name__=='__main__':raise SystemExit(main())
