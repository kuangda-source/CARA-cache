"""Independent source, original handles, tensor identities and block-pair read."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    root=Path(__file__).resolve().parents[1]
    launch=json.loads((root/'reports/wc_e3_complete64_blocks_cpu_r2_launch_20261011.json').read_text())
    code='P='+repr(launch)+'\n'+r'''import base64,gzip,hashlib,json,pathlib,os,time
s=pathlib.Path(P['stage']);project=s.parents[1];r=json.loads((s/'receipt.json').read_text());reg=json.loads((s/'registration.json').read_text())
pids=[r['pid'],r.get('child_pid')];live=[p for p in pids if p and pathlib.Path('/proc/'+str(p)).exists()]
if live:print(json.dumps({'status':'E3_ORIGINAL_BLOCK_CPU_HANDLES_LIVE','PIDs':live}));raise SystemExit(0)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert r['pid']==P['supervisor_pid'] and r['source_revision']==P['source_revision']
assert sha(s/'registration.json')==P['registration_sha256']
assert {n:sha(s/n) for n in reg['payload_sha256']}==reg['payload_sha256']==r['payload_after_sha256']
assert r['budget_before_sha256']==r['budget_after_sha256'] and r['GPU_submissions']==0 and not r['ledger_written']
independent={};names=['receipt.json','registration.json','CPU.log','driver.log','launch.json']
if (s/'result.failure.json').exists():names.append('result.failure.json')
if r['exit_code']==0:
 assert r['child_exit_code']==0 and sha(s/'result.json')==r['result_sha256'];names.append('result.json')
 v=json.loads((s/'result.json').read_text());assert v['payload_sha256']==reg['payload_sha256'] and not v['CUDA_initialized']
 assert (v['successful_complete_CPU_paths'],v['writer_failure_attempted_CPU_paths'],v['actual_all_tensors_reloaded'])==(64,12,2368)
 os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
 import torch;torch.set_num_threads(2)
 def forbidden(*a,**k):raise RuntimeError('E3 independent block capture forbids CUDA/downloads')
 torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
 def digest(x):
  h=hashlib.sha256()
  def walk(t):
   if isinstance(t,torch.Tensor):
    assert torch.isfinite(t).all();h.update(str((str(t.dtype),list(t.shape))).encode());h.update(t.detach().contiguous().reshape(-1).view(torch.uint8).numpy().tobytes())
   elif isinstance(t,dict):
    for k in sorted(t):h.update(str(k).encode());walk(t[k])
   elif isinstance(t,(list,tuple)):
    h.update(type(t).__name__.encode())
    for a in t:walk(a)
   else:h.update(repr(t).encode())
  walk(x);return h.hexdigest()
 actual=set();read=0;success=0;loaded={}
 for check in v['checks']:
  for q in check['receipt']['requests']:
   for row in q['paths']:
    if 'vector_artifact' not in row:continue
    a=row['vector_artifact'];p=pathlib.Path(a['path']).resolve()
    assert p.is_relative_to((s/'CPU-artifacts').resolve()) and p.stat().st_size==a['bytes'] and sha(p)==a['sha256']
    x=torch.load(p,map_location='cpu',weights_only=True)
    assert set(x)=={'guided','final_latent'} and len(x['guided'])==36
    assert all(t.dtype==torch.float32 and t.device.type=='cpu' and list(t.shape)==[1,2048,2,8,8] for t in x['guided']+[x['final_latent']])
    assert {k:digest(z) for k,z in x.items()}==a['tensor_sha256']
    assert [digest(t) for t in x['guided']]==row['guided_sha256'] and digest(x['final_latent'])==row['final_latent_sha256']
    actual.add(str(p));read+=37
    if check['status']=='PASS':
     success+=1
     loaded[(check['working_epoch_strategy'],check['flow'],check['block']['id'],check['CPU_original_control'],row['collect'])]=p
    del x
 assert actual=={str(p.resolve()) for p in (s/'CPU-artifacts').rglob('*.pt')} and len(actual)==72 and success==64
 comparisons=[]
 for key,p in loaded.items():
  if not key[3]:continue
  partner=(key[0],key[1],key[2],False,key[4]);q=loaded[partner]
  x,y=[torch.load(a,map_location='cpu',weights_only=True) for a in (p,q)]
  equal=[torch.equal(a,b) for a,b in zip(x['guided']+[x['final_latent']],y['guided']+[y['final_latent']])]
  assert len(equal)==37 and all(equal)
  comparisons.append({'strategy':key[0],'flow':key[1],'block':key[2],'method':key[4],'equal_guided36_and_final':equal})
  del x,y
 assert len(comparisons)==32 and not torch.cuda.is_initialized()
 independent={'actual_written_vector_files_reloaded':len(actual),'actual_written_tensors_reloaded':read,
  'successful_complete_vector_paths':success,'successful_complete_tensors':37*success,
  'failed_block_completed_prefix_vector_files':len(actual)-success,'direct_pairs':comparisons,
  'actual_direct_tensor_comparisons':37*len(comparisons),'CUDA_initialized':False,'GPU_submissions':0}
native={}
for n in names:
 raw=(s/n).read_bytes();z=gzip.compress(raw,mtime=0)
 native[n]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'compressed_sha256':hashlib.sha256(z).hexdigest(),'base64':base64.b64encode(z).decode()}
print(json.dumps({'status':'E3_ORIGINAL_AFFECTED_BLOCK_CPU_TERMINAL_CAPTURE','receipt':r,
 'independent_actual_vector_reads':independent,'original_handles_absent':pids,'observed_unix':time.time(),'native':native}))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen',
        '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'],input=code,text=True,capture_output=True)
    if call.returncode:raise RuntimeError(call.stderr[-3000:])
    v=json.loads(call.stdout)
    if 'native' not in v:print(json.dumps(v));return 2
    target=root/'reports/wc_e3_complete64_blocks_cpu_r2_terminal_20261011_capture.json';assert not target.exists()
    reg=json.loads((root/'manifests/wc_e3_complete64_blocks_affected_cpu_r2_20261011.json').read_text());v['files']={}
    for n,item in v.pop('native').items():
        z=base64.b64decode(item.pop('base64'),validate=True);raw=gzip.decompress(z)
        assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'] and hashlib.sha256(z).hexdigest()==item['compressed_sha256']
        p=root/'reports'/('wc_e3_complete64_blocks_cpu_r2_terminal_20261011_'+n+'.native.gz');assert not p.exists();p.write_bytes(z)
        v['files'][n]={**item,'local_path':str(p.relative_to(root))}
        if n=='registration.json':assert json.loads(raw)==reg
        if n=='launch.json':assert json.loads(raw)==launch
    v['original_source_receipts_complete_scope_and_actual_vectors_independently_verified']=v['receipt']['exit_code']==0
    target.write_text(json.dumps(v,indent=2)+'\n')
    print(json.dumps({'status':v['status'],'exit_code':v['receipt']['exit_code'],
        'independent':{k:w for k,w in v['independent_actual_vector_reads'].items() if k!='direct_pairs'}}));return 0


if __name__=='__main__':raise SystemExit(main())
