"""Read original P CPU handles, source receipts and every full tensor file."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


REMOTE=r'''import base64,gzip,hashlib,json,pathlib,time,os,sys
project=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr')
s=project/'.sync/wc-p-working-reference-sampling-cpu-r3-20261011'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
launch=json.loads((s/'launch.json').read_text());receipt=json.loads((s/'receipt.json').read_text())
assert launch['source_revision']==receipt['source_revision']=='a2f40f38e8a8f7a2f16b4e6c562cd3a42cfe424e'
assert launch['pid']==receipt['pid']==4108321
ids=[receipt['pid'],receipt['child_pid']]
if any(pathlib.Path('/proc/'+str(p)).exists() for p in ids):
 print(json.dumps({'status':'WAIT_ORIGINAL_P_REFERENCE_COMPLETE10_CPU','pids':ids,'observed_unix':time.time()}))
 raise SystemExit(0)
reg=json.loads((s/'registration.json').read_text());payload=dict(reg['inherited_payload_sha256'],**reg['new_payload_sha256'])
assert {n:sha(s/n) for n in payload}==payload==receipt['payload_after_sha256'] and len(payload)==440
assert receipt['exit_code']==0 and receipt['status']=='P_REFERENCE_COMPLETE10_CPU_PASS_PENDING_INDEPENDENT_CAPTURE'
assert receipt['GPU_submissions']==0 and receipt['ledger_written'] is False
assert sha(s/'result.json')==receipt['result_sha256']
value=json.loads((s/'result.json').read_text())
assert value['status']=='P_WORKING_REFERENCE_FULL_UNIPC_TWO_FLOW_CPU_PASS_NOT_GPU'
assert value['complete_paths']==10 and value['updates']==360 and value['CFG_calls']==720
assert value['written_tensors']==370 and value['full_physical_and_owned_restores']==40
assert [x['flow'] for x in value['checks']]==[False,True] and value['CUDA_initialized'] is False
budget_before=sha(project/'reports/budget.json')
os.environ['CUDA_VISIBLE_DEVICES']='';sys.path.insert(0,str(s/'src'))
import torch
torch.set_num_threads(2)
def forbidden(*a,**kw):raise RuntimeError('Independent P capture forbids CUDA and downloads')
torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
from wcomr.mid_coverage import tree_digest
loaded=checked=0;files=[];seen=set();formula_checks=0
for group in value['checks']:
 assert group['status']=='PASS' and group['verdict']=={'paths':5,'updates':180,'CFG_calls':360,'full_restores':20}
 assert group['receipt']['initial_state_restored'] and len(group['observations'])==360
 rows=group['receipt']['requests'][0]['paths'];assert len(rows)==5
 methods=['OFF','D_REFERENCE_W1_ONE_PHASE','P_REFERENCE_W1_ONE_PHASE','D_REFERENCE_BETA1_ONE_PHASE','P_REFERENCE_BETA1_ONE_PHASE']
 assert [r['collect'] for r in rows]==methods
 values={}
 for row in rows:
  art=row['vector_artifact'];p=pathlib.Path(art['path']).resolve()
  assert p.is_relative_to((s/'CPU-artifacts').resolve()) and p not in seen
  assert sha(p)==art['sha256'];seen.add(p)
  x=torch.load(p,map_location='cpu',weights_only=True)
  assert set(x)=={'guided','final_latent'} and len(x['guided'])==36
  assert {k:tree_digest(v) for k,v in x.items()}==art['tensor_sha256']
  for t in x['guided']+[x['final_latent']]:
   assert t.device.type=='cpu' and t.dtype==torch.float32 and list(t.shape)==[1,2048,2,8,8] and torch.isfinite(t).all();loaded+=1
  assert sha(p)==art['sha256'];values[row['collect']]=x;files.append({'path':str(p),'sha256':art['sha256']})
  assert len(row['P0_roundtrips'])==4 and all(z['physical_state_restored'] and z['complete_additional_state_restored']
         and z['checkpoint_perturbation_executed'] for z in row['P0_roundtrips'])
  d=row['collection_complete']['deployment'];a=d['A_readout']
  assert len(a['history'])==36 and a['teacher_calls']==0
  assert len(row['collection_complete']['actual_original_plus_candidate_heads'])==72+a['extra_candidate_heads']
  for h in d['history']:
   if h['action']!='DD':assert h['true_D_before']==h['true_D_after']
   if h['action']=='PP':assert all(s['creation_error']=='UNKNOWN_NOT_ZERO' and not s['RA_zero_risk_reset_allowed'] for s in h['working_sources'])
  if row['collect'].startswith('P_REFERENCE'):
   for h in a['history']:
    for proof in h['P_reference']:
     if proof:
      assert proof['true_D_full_state_before_sha256']==proof['true_D_full_state_after_sha256']
      assert max(proof['true_D_steps'])<proof['working_created_step']<h['step'];formula_checks+=1
 for mode in ('W1_ONE_PHASE','BETA1_ONE_PHASE'):
  a,b=[values[v+'_REFERENCE_'+mode] for v in ('D','P')]
  assert all(torch.equal(x,y) for x,y in zip(a['guided'][:10],b['guided'][:10]));checked+=10
  assert any(not torch.equal(x,y) for x,y in zip(a['guided'][10:],b['guided'][10:]))
  actual=[x for x in group['observations'] if x['method']=='P_REFERENCE_'+mode and x['independent_actual_P_formula_and_head_checked']]
  assert actual and {x['slot'] for x in actual}=={0,1}
assert loaded==370 and checked==40 and len(seen)==10
assert seen=={p.resolve() for p in (s/'CPU-artifacts').rglob('*.pt')}
assert sha(project/'reports/budget.json')==budget_before and not torch.cuda.is_initialized()
assert {n:sha(s/n) for n in payload}==payload and sha(s/'result.json')==receipt['result_sha256']
originals={}
for name in ('launch','receipt','registration','result'):
 p=s/(name+'.json');raw=p.read_bytes();originals[name]={'remote_path':str(p),'sha256':sha(p),'bytes':len(raw),
  'gzip_base64':base64.b64encode(gzip.compress(raw,mtime=0)).decode()}
print(json.dumps({'status':'P_REFERENCE_COMPLETE10_CPU_INDEPENDENTLY_AUDITED_NOT_GPU','original_PIDs_absent':ids,
 'source_revision':receipt['source_revision'],'CPU_wall_seconds':receipt['CPU_wall_seconds'],
 'frozen_source_files_unchanged':440,'actual_reloaded_files':len(seen),'actual_reloaded_tensors':loaded,
 'first_ten_update_equalities':checked,'actual_P_reference_branch_checks':formula_checks,
 'complete_restores':40,'source_RNG_and_cache_checks_in_original_fixture':True,
 'CUDA_initialized':False,'GPU_submissions':0,'ledger_written':False,'observed_unix':time.time(),
 'GPU_inflight_ledger_observation':json.loads((project/'reports/budget.json').read_text()),'files':files,'originals':originals}))
'''


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();assert not args.output.exists()
    root=Path(__file__).resolve().parents[1]
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen',
        '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'],input=REMOTE,text=True,capture_output=True)
    if call.returncode:raise RuntimeError(call.stderr[-3500:])
    value=json.loads(call.stdout)
    if value['status'].startswith('WAIT_'):print(json.dumps(value));return
    folder=root/'reports'/args.output.stem;assert not folder.exists();folder.mkdir()
    for name,entry in value['originals'].items():
        raw=base64.b64decode(entry.pop('gzip_base64'));plain=gzip.decompress(raw)
        assert hashlib.sha256(plain).hexdigest()==entry['sha256'] and len(plain)==entry['bytes']
        p=folder/(name+'.json.gz');p.write_bytes(raw);entry['local_path']=str(p)
    args.output.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:value[k] for k in ('status','CPU_wall_seconds','actual_reloaded_files',
        'actual_reloaded_tensors','first_ten_update_equalities','actual_P_reference_branch_checks')}))


if __name__=='__main__':main()
